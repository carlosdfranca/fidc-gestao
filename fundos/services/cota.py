"""
Motor de Cálculo de Cota de Fundo
Referência: Instrução CVM 555/2014
"""

from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from django.db import transaction
from django.db.models import Sum, Q

from fundos.models import Fundo, CotaHistorico, Ativo, Recebiveis
from .tributos import calcular_pdd


def calcular_cota_fechamento(fundo_id: str, data_referencia: date) -> dict:
    """
    Calcula cota de fechamento do fundo para uma data específica.
    
    Fórmula:
    Cota = PL / Quantidade de Cotas
    
    Onde:
    PL = Ativos - Passivos
    Ativos = Carteira (marcação a mercado) + Disponibilidades
    Passivos = Taxas provisionadas + Outras obrigações
    
    Args:
        fundo_id: UUID do fundo
        data_referencia: Data do cálculo
        
    Returns:
        dict com valor_cota, patrimonio_liquido, quantidade_cotas, etc.
    """
    try:
        fundo = Fundo.objects.get(id=fundo_id)
    except Fundo.DoesNotExist:
        raise ValueError(f"Fundo {fundo_id} não encontrado")
    
    # 1. Valor da carteira (marcação a mercado)
    ativos = Ativo.objects.filter(
        fundo_id=fundo_id,
        ativo=True
    )
    
    valor_carteira = sum(
        (ativo.valor_mercado or Decimal('0.00')) for ativo in ativos
    )
    
    # 2. Se FIDC, calcula PDD e desconta
    if fundo.tipo_fundo == 'FIDC':
        recebiveis = Recebiveis.objects.filter(
            fundo_id=fundo_id
        ).exclude(status='BAIXADO')
        
        total_pdd = Decimal('0.00')
        for rec in recebiveis:
            pdd = calcular_pdd(rec.dias_atraso, rec.valor_nominal)
            rec.pdd_valor = pdd
            rec.pdd_percentual = (pdd / rec.valor_nominal * 100) if rec.valor_nominal > 0 else 0
            total_pdd += pdd
        
        # Bulk update
        Recebiveis.objects.bulk_update(recebiveis, ['pdd_valor', 'pdd_percentual'])
        
        valor_carteira -= total_pdd
    
    # 3. Disponibilidades (simplificado - em produção integrar com extrato bancário)
    disponibilidades = Decimal('0.00')
    
    # 4. Passivo exigível - Provisionamento de taxas
    dias_mes = 30
    dias_decorridos = data_referencia.day
    
    taxa_admin_mes = (fundo.taxa_administracao or Decimal('0.00')) / 12
    taxa_gestao_mes = (fundo.taxa_gestao or Decimal('0.00')) / 12
    
    pl_aproximado = valor_carteira + disponibilidades
    
    taxa_admin_provisionada = pl_aproximado * taxa_admin_mes * (Decimal(dias_decorridos) / Decimal(dias_mes))
    taxa_gestao_provisionada = pl_aproximado * taxa_gestao_mes * (Decimal(dias_decorridos) / Decimal(dias_mes))
    
    passivo_exigivel = taxa_admin_provisionada + taxa_gestao_provisionada
    
    # 5. Patrimônio Líquido
    patrimonio_liquido = valor_carteira + disponibilidades - passivo_exigivel
    
    # 6. Quantidade de cotas
    ultima_cota = CotaHistorico.objects.filter(
        fundo_id=fundo_id
    ).order_by('-data_referencia').first()
    
    if ultima_cota:
        quantidade_cotas = ultima_cota.quantidade_cotas
    else:
        quantidade_cotas = Decimal('1000000.000000')  # Cotas iniciais padrão
    
    # 7. Valor da cota
    if quantidade_cotas > 0:
        valor_cota = patrimonio_liquido / quantidade_cotas
    else:
        valor_cota = Decimal('1.000000')
    
    valor_cota = valor_cota.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
    
    # 8. Conta cotistas ativos (simplificado)
    quantidade_cotistas = _contar_cotistas(fundo_id)
    
    # 9. Calcula rentabilidade
    rentabilidade_dia = _calcular_rentabilidade_dia(fundo_id, valor_cota, ultima_cota)
    
    # 10. Salva histórico
    with transaction.atomic():
        cota_hist, created = CotaHistorico.objects.update_or_create(
            fundo_id=fundo_id,
            data_referencia=data_referencia,
            defaults={
                'valor_cota': valor_cota,
                'patrimonio_liquido': patrimonio_liquido,
                'quantidade_cotas': quantidade_cotas,
                'quantidade_cotistas': quantidade_cotistas,
                'rentabilidade_dia': rentabilidade_dia,
            }
        )
    
    return {
        'valor_cota': float(valor_cota),
        'patrimonio_liquido': float(patrimonio_liquido),
        'quantidade_cotas': float(quantidade_cotas),
        'quantidade_cotistas': quantidade_cotistas,
        'data_referencia': data_referencia.isoformat(),
        'criado': created
    }


def _contar_cotistas(fundo_id: str) -> int:
    """
    Conta cotistas ativos do fundo.
    Em produção, implementar tabela PosicaoCotista.
    """
    from fundos.models import MovimentacaoCota
    
    cotistas_ativos = MovimentacaoCota.objects.filter(
        fundo_id=fundo_id,
        status='CONFIRMADO'
    ).values('cotista').distinct().count()
    
    return cotistas_ativos


def _calcular_rentabilidade_dia(fundo_id: str, valor_cota_atual: Decimal, ultima_cota) -> Decimal:
    """
    Calcula rentabilidade do dia.
    Rentabilidade = (Cota_Atual / Cota_Anterior) - 1
    """
    if not ultima_cota or not ultima_cota.valor_cota:
        return Decimal('0.00')
    
    if ultima_cota.valor_cota == 0:
        return Decimal('0.00')
    
    rentabilidade = (valor_cota_atual / ultima_cota.valor_cota) - Decimal('1.00')
    return rentabilidade.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)


def recalcular_rentabilidade_mes(fundo_id: str, mes: int, ano: int):
    """
    Recalcula rentabilidade acumulada do mês.
    Útil para ajustes retroativos.
    """
    from django.db.models import F
    from datetime import datetime
    
    data_inicio = datetime(ano, mes, 1).date()
    
    if mes == 12:
        data_fim = datetime(ano + 1, 1, 1).date()
    else:
        data_fim = datetime(ano, mes + 1, 1).date()
    
    cotas_mes = CotaHistorico.objects.filter(
        fundo_id=fundo_id,
        data_referencia__gte=data_inicio,
        data_referencia__lt=data_fim
    ).order_by('data_referencia')
    
    if not cotas_mes.exists():
        return
    
    primeira_cota = cotas_mes.first()
    ultima_cota = cotas_mes.last()
    
    if primeira_cota.valor_cota == 0:
        return
    
    rentabilidade_mes = (ultima_cota.valor_cota / primeira_cota.valor_cota) - Decimal('1.00')
    
    # Atualiza todas as cotas do mês
    cotas_mes.update(rentabilidade_mes=rentabilidade_mes)