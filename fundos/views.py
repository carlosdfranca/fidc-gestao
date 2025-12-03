from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal
from datetime import date
import uuid

from .models import Fundo, Cotista, MovimentacaoCota, CotaHistorico
from .services.cota import calcular_cota_fechamento
from .services.movimentacoes import processar_aplicacao, processar_resgate


@login_required
def calcular_cota_manual(request, fundo_id):
    """View para calcular cota manualmente"""

    fundo_id = str(fundo_id)
    
    # Converte string para UUID (com ou sem hífens)
    try:
        if '-' not in fundo_id and len(fundo_id) == 32:
            fundo_id = f"{fundo_id[:8]}-{fundo_id[8:12]}-{fundo_id[12:16]}-{fundo_id[16:20]}-{fundo_id[20:]}"
        
        fundo_uuid = uuid.UUID(fundo_id)
        fundo = get_object_or_404(Fundo, id=fundo_uuid)
    except (ValueError, AttributeError):
        messages.error(request, "UUID inválido")
        return redirect('home')
    
    if request.method == 'POST':
        data_referencia = request.POST.get('data_referencia')
        
        try:
            data_obj = date.fromisoformat(data_referencia)
            resultado = calcular_cota_fechamento(str(fundo.id), data_obj)
            
            messages.success(
                request,
                f"Cota calculada: R$ {resultado['valor_cota']:.6f} | "
                f"PL: R$ {resultado['patrimonio_liquido']:,.2f}"
            )
        except Exception as e:
            messages.error(request, f"Erro ao calcular cota: {str(e)}")
        
        return redirect('fundos:calcular_cota_manual', fundo_id=str(fundo.id))
    
    # Busca últimas 10 cotas
    historico = CotaHistorico.objects.filter(fundo=fundo).order_by('-data_referencia')[:10]
    
    context = {
        'fundo': fundo,
        'historico': historico,
        'data_hoje': date.today().isoformat()
    }
    
    return render(request, 'fundos/calcular_cota.html', context)


@login_required
def nova_aplicacao(request):
    """View para processar nova aplicação"""
    if request.method == 'POST':
        fundo_id = request.POST.get('fundo')
        cotista_id = request.POST.get('cotista')
        valor = request.POST.get('valor')
        
        try:
            movimentacao = processar_aplicacao(
                fundo_id,
                cotista_id,
                Decimal(valor)
            )
            
            messages.success(
                request,
                f"Aplicação processada! Cotização em {movimentacao.data_cotizacao.strftime('%d/%m/%Y')}"
            )
            return redirect('fundos:nova_aplicacao')
        
        except Exception as e:
            messages.error(request, f"Erro: {str(e)}")
    
    fundos = Fundo.objects.filter(ativo=True)
    cotistas = Cotista.objects.filter(ativo=True)
    ultimas_aplicacoes = MovimentacaoCota.objects.filter(
        tipo_movimentacao='APLICACAO'
    ).select_related('fundo', 'cotista').order_by('-data_solicitacao')[:10]
    
    context = {
        'fundos': fundos,
        'cotistas': cotistas,
        'ultimas_aplicacoes': ultimas_aplicacoes
    }
    
    return render(request, 'fundos/nova_aplicacao.html', context)


@login_required
def novo_resgate(request):
    """View para processar novo resgate"""
    if request.method == 'POST':
        fundo_id = request.POST.get('fundo')
        cotista_id = request.POST.get('cotista')
        quantidade = request.POST.get('quantidade')
        
        try:
            movimentacao = processar_resgate(
                fundo_id,
                cotista_id,
                Decimal(quantidade)
            )
            
            messages.success(
                request,
                f"Resgate solicitado! Cotização em {movimentacao.data_cotizacao.strftime('%d/%m/%Y')}"
            )
            return redirect('fundos:novo_resgate')
        
        except Exception as e:
            messages.error(request, f"Erro: {str(e)}")
    
    fundos = Fundo.objects.filter(ativo=True)
    cotistas = Cotista.objects.filter(ativo=True)
    ultimos_resgates = MovimentacaoCota.objects.filter(
        tipo_movimentacao='RESGATE'
    ).select_related('fundo', 'cotista').order_by('-data_solicitacao')[:10]
    
    context = {
        'fundos': fundos,
        'cotistas': cotistas,
        'ultimos_resgates': ultimos_resgates
    }
    
    return render(request, 'fundos/novo_resgate.html', context)