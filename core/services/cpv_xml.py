from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import re
import xml.etree.ElementTree as ET
from typing import Any


# ============================================================
# Helpers
# ============================================================

_RE_DIGITS = re.compile(r"\D+")


def _digits(value: str | None) -> str:
    if value is None:
        return ""
    return _RE_DIGITS.sub("", str(value))


def _to_decimal(value: str | None) -> Decimal:
    """
    Converte string para Decimal aceitando:
      - "15000.75"
      - "15.000,75"
      - "15000,75"
      - ""
    """
    if value is None:
        return Decimal("0")
    s = str(value).strip()
    if not s:
        return Decimal("0")

    # remove espaços
    s = s.replace(" ", "")

    # se tiver vírgula e ponto, assume pt-BR "15.000,75"
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    # se só tiver vírgula, assume decimal com vírgula
    elif "," in s and "." not in s:
        s = s.replace(",", ".")

    try:
        return Decimal(s)
    except InvalidOperation:
        return Decimal("0")


def _find_first_text(elem: ET.Element, paths: list[str], ns: dict[str, str]) -> str:
    """
    Procura o primeiro texto existente em uma lista de XPaths (relativos ao elem).
    Retorna "" se não achar.
    """
    for p in paths:
        found = elem.find(p, ns)
        if found is not None and (found.text or "").strip():
            return (found.text or "").strip()
    return ""


def _all(elem: ET.Element, path: str, ns: dict[str, str]) -> list[ET.Element]:
    return list(elem.findall(path, ns))


def _infer_namespace(root: ET.Element) -> dict[str, str]:
    """
    NF-e normalmente usa namespace como:
      {http://www.portalfiscal.inf.br/nfe}
    Este helper tenta capturar e retornar um dict pro ElementTree.
    """
    m = re.match(r"\{(.+)\}", root.tag)
    if m:
        return {"nfe": m.group(1)}
    return {}


@dataclass(frozen=True)
class CpvTitulo:
    sacado_nome: str
    sacado_doc: str  # CPF/CNPJ apenas dígitos
    valor: Decimal
    vencimento_iso: str  # "YYYY-MM-DD"
    tipo_credito: str = "Duplicata"
    numero_titulo: str = ""  # opcional


@dataclass(frozen=True)
class CpvPartes:
    cedente_nome: str
    cedente_doc: str  # CNPJ apenas dígitos
    sacado_nome: str
    sacado_doc: str  # CPF/CNPJ apenas dígitos
    numero_nota: str = ""     # nNF
    data_emissao_iso: str = ""  # dhEmi / dEmi


@dataclass(frozen=True)
class CpvParseResult:
    partes: CpvPartes
    titulos: list[CpvTitulo]
    total: Decimal


# ============================================================
# Parser principal
# ============================================================

def parse_nfe_xml(xml_bytes: bytes) -> CpvParseResult:
    """
    Lê XML NF-e (vários formatos comuns) e extrai:
      - emit/xNome + emit/CNPJ
      - dest/xNome + dest/CNPJ ou dest/CPF
      - duplicatas: cobr/dup (dVenc e (vDup opcional))
      - fallback de valor: somar det/prod/vProd

    Não salva nada em disco. Só retorna dados.
    """
    root = ET.fromstring(xml_bytes)
    ns = _infer_namespace(root)

    # Achar o nó infNFe (pode estar em nfeProc/NFe/infNFe etc.)
    # Tentativas sem e com namespace.
    infnfe = None

    # sem namespace
    infnfe = root.find(".//infNFe")
    if infnfe is None and ns:
        infnfe = root.find(".//nfe:infNFe", ns)

    if infnfe is None:
        raise ValueError("XML não contém infNFe (não parece ser uma NF-e válida).")

    # nós principais
    emit = infnfe.find("emit") or (infnfe.find("nfe:emit", ns) if ns else None)
    dest = infnfe.find("dest") or (infnfe.find("nfe:dest", ns) if ns else None)
    ide = infnfe.find("ide") or (infnfe.find("nfe:ide", ns) if ns else None)
    cobr = infnfe.find("cobr") or (infnfe.find("nfe:cobr", ns) if ns else None)

    if emit is None or dest is None:
        raise ValueError("XML NF-e sem tags emit/dest.")

    cedente_nome = _find_first_text(emit, ["xNome", "nfe:xNome"], ns)
    cedente_cnpj = _digits(_find_first_text(emit, ["CNPJ", "nfe:CNPJ"], ns))

    sacado_nome = _find_first_text(dest, ["xNome", "nfe:xNome"], ns)
    sacado_doc = _digits(_find_first_text(dest, ["CNPJ", "nfe:CNPJ", "CPF", "nfe:CPF"], ns))

    numero_nota = ""
    data_emissao = ""
    if ide is not None:
        numero_nota = _find_first_text(ide, ["nNF", "nfe:nNF"], ns)
        # dhEmi é comum, mas algumas versões usam dEmi
        data_emissao = _find_first_text(ide, ["dhEmi", "nfe:dhEmi", "dEmi", "nfe:dEmi"], ns)
        # se vier com timezone "2026-02-05T00:00:00-03:00" mantém string (você pode normalizar depois)
        data_emissao = (data_emissao or "").strip()

    # Total por produtos (fallback)
    # somar det/prod/vProd
    det_nodes = _all(infnfe, "det", ns) or (_all(infnfe, "nfe:det", ns) if ns else [])
    soma_vprod = Decimal("0")
    for det in det_nodes:
        prod = det.find("prod") or (det.find("nfe:prod", ns) if ns else None)
        if prod is None:
            continue
        vprod = _find_first_text(prod, ["vProd", "nfe:vProd"], ns)
        soma_vprod += _to_decimal(vprod)

    # Duplicatas (cobr/dup)
    dup_nodes: list[ET.Element] = []
    if cobr is not None:
        dup_nodes = _all(cobr, "dup", ns) or (_all(cobr, "nfe:dup", ns) if ns else [])

    titulos: list[CpvTitulo] = []

    if dup_nodes:
        for dup in dup_nodes:
            d_venc = _find_first_text(dup, ["dVenc", "nfe:dVenc"], ns).strip()
            # valor da duplicata pode ser vDup; se não existir, deixa 0 e a tela decide
            v_dup = _to_decimal(_find_first_text(dup, ["vDup", "nfe:vDup"], ns))
            n_dup = _find_first_text(dup, ["nDup", "nfe:nDup"], ns).strip()

            titulos.append(
                CpvTitulo(
                    sacado_nome=sacado_nome,
                    sacado_doc=sacado_doc,
                    valor=v_dup,
                    vencimento_iso=d_venc,  # geralmente já vem YYYY-MM-DD
                    tipo_credito="Duplicata",
                    numero_titulo=n_dup or numero_nota,
                )
            )

        # Se todas vieram com valor 0 (comum em alguns XMLs), distribui proporcionalmente ou joga soma total?
        # Aqui, por simplicidade, se TODOS forem 0 e existir soma_vprod, coloca tudo no primeiro título.
        if soma_vprod > 0 and all(t.valor == 0 for t in titulos):
            first = titulos[0]
            titulos[0] = CpvTitulo(
                sacado_nome=first.sacado_nome,
                sacado_doc=first.sacado_doc,
                valor=soma_vprod,
                vencimento_iso=first.vencimento_iso,
                tipo_credito=first.tipo_credito,
                numero_titulo=first.numero_titulo,
            )

    else:
        # Sem duplicata no XML: cria 1 título padrão com vencimento vazio.
        # A tela vai permitir editar vencimento/valor.
        titulos.append(
            CpvTitulo(
                sacado_nome=sacado_nome,
                sacado_doc=sacado_doc,
                valor=soma_vprod,
                vencimento_iso="",
                tipo_credito="Duplicata",
                numero_titulo=numero_nota,
            )
        )

    total = sum((t.valor for t in titulos), Decimal("0"))

    partes = CpvPartes(
        cedente_nome=cedente_nome,
        cedente_doc=cedente_cnpj,
        sacado_nome=sacado_nome,
        sacado_doc=sacado_doc,
        numero_nota=numero_nota,
        data_emissao_iso=data_emissao,
    )

    return CpvParseResult(partes=partes, titulos=titulos, total=total)


# ============================================================
# Utilitário opcional para sua view
# ============================================================

def parse_nfe_uploaded_file(uploaded_file) -> CpvParseResult:
    """
    Aceita request.FILES['xml'] (UploadedFile do Django).
    """
    return parse_nfe_xml(uploaded_file.read())
