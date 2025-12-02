from django.contrib import admin
from .models import Fundo, Cotista, MovimentacaoCota, CotaHistorico, Ativo, Recebiveis

@admin.register(Fundo)
class FundoAdmin(admin.ModelAdmin):
    list_display = ('razao_social', 'cnpj', 'tipo_fundo', 'ativo', 'data_cadastro')
    list_filter = ('tipo_fundo', 'ativo', 'empresa')
    search_fields = ('razao_social', 'cnpj', 'codigo_anbima')
    readonly_fields = ('id', 'data_cadastro', 'data_atualizacao')

@admin.register(Cotista)
class CotistaAdmin(admin.ModelAdmin):
    list_display = ('nome_razao_social', 'cpf_cnpj', 'tipo_pessoa', 'email', 'ativo')
    list_filter = ('tipo_pessoa', 'qualificacao', 'ativo')
    search_fields = ('nome_razao_social', 'cpf_cnpj', 'email')

@admin.register(MovimentacaoCota)
class MovimentacaoCotaAdmin(admin.ModelAdmin):
    list_display = ('fundo', 'cotista', 'tipo_movimentacao', 'valor_financeiro', 'data_cotizacao', 'status')
    list_filter = ('tipo_movimentacao', 'status', 'data_cotizacao')
    search_fields = ('fundo__razao_social', 'cotista__nome_razao_social')
    date_hierarchy = 'data_cotizacao'

@admin.register(CotaHistorico)
class CotaHistoricoAdmin(admin.ModelAdmin):
    list_display = ('fundo', 'data_referencia', 'valor_cota', 'patrimonio_liquido', 'quantidade_cotas')
    list_filter = ('fundo', 'data_referencia')
    date_hierarchy = 'data_referencia'

@admin.register(Ativo)
class AtivoAdmin(admin.ModelAdmin):
    list_display = ('fundo', 'tipo_ativo', 'codigo_isin', 'emissor_nome', 'valor_mercado', 'ativo')
    list_filter = ('tipo_ativo', 'ativo', 'fundo')
    search_fields = ('codigo_isin', 'codigo_negociacao', 'emissor_nome')

@admin.register(Recebiveis)
class RecebiveisAdmin(admin.ModelAdmin):
    list_display = ('fundo', 'numero_titulo', 'cedente_nome', 'sacado_nome', 'valor_nominal', 'data_vencimento', 'status', 'dias_atraso')
    list_filter = ('status', 'fundo', 'data_vencimento')
    search_fields = ('numero_titulo', 'cedente_nome', 'sacado_nome', 'cedente_cnpj', 'sacado_cpf_cnpj')
    date_hierarchy = 'data_vencimento'
