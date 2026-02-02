from io import BytesIO
from decimal import Decimal
from docxtpl import DocxTemplate


# -------------------------------------------------
# Helpers
# -------------------------------------------------

def _fmt_money(v: Decimal) -> str:
    s = f"{v:,.2f}"
    # 12,345.67 -> 12.345,67
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_doc(doc: str) -> str:
    if len(doc) == 14:
        return f"{doc[:2]}.{doc[2:5]}.{doc[5:8]}/{doc[8:12]}-{doc[12:]}"
    if len(doc) == 11:
        return f"{doc[:3]}.{doc[3:6]}.{doc[6:9]}-{doc[9:]}"
    return doc


# -------------------------------------------------
# Render principal
# -------------------------------------------------

def render_termo_cessao_docx(
    template_path: str,
    *,
    partes,
    titulos,
    dados_operacao: dict
) -> bytes:
    """
    Gera DOCX em memória — NÃO salva em disco.

    partes → CpvPartes
    titulos → list[CpvTitulo]
    dados_operacao → dict com:
        data_contrato
        preco_aquisicao
        banco
        agencia
        conta
        cessionario_nome
        cessionario_doc
    """

    doc = DocxTemplate(template_path)

    total = sum(t.valor for t in titulos)

    tabela = []
    for t in titulos:
        tabela.append({
            "sacado_nome": t.sacado_nome,
            "sacado_doc": _fmt_doc(t.sacado_doc),
            "valor": _fmt_money(t.valor),
            "vencimento": t.vencimento_iso,
            "tipo": t.tipo_credito,
            "numero": t.numero_titulo,
        })

    context = {
        # -------- Partes --------
        "cedente_nome": partes.cedente_nome,
        "cedente_doc": _fmt_doc(partes.cedente_doc),
        "sacado_nome": partes.sacado_nome,
        "sacado_doc": _fmt_doc(partes.sacado_doc),

        # -------- Operação --------
        "data_contrato": dados_operacao.get("data_contrato"),
        "preco_aquisicao": _fmt_money(dados_operacao.get("preco_aquisicao", Decimal("0"))),
        "banco": dados_operacao.get("banco"),
        "agencia": dados_operacao.get("agencia"),
        "conta": dados_operacao.get("conta"),

        "cessionario_nome": dados_operacao.get("cessionario_nome"),
        "cessionario_doc": _fmt_doc(dados_operacao.get("cessionario_doc", "")),

        # -------- Títulos --------
        "titulos": tabela,
        "total": _fmt_money(total),
    }

    doc.render(context)

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)

    return buf.read()
