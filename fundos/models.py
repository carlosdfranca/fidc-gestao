from django.db import models
from decimal import Decimal
from usuarios.models import Empresa
import uuid

# ============================================
# ENUMS
# ============================================

class TipoFundo(models.TextChoices):
    FII = 'FII', 'Fundo de Investimento Imobiliário'
    FIDC = 'FIDC', 'Fundo de Investimento em Direitos Creditórios'
    FIP = 'FIP', 'Fundo de Investimento em Participações'

class StatusMovimentacao(models.TextChoices):
    SOLICITADO = 'SOLICITADO', 'Solicitado'
    AGUARDANDO_PAGAMENTO = 'AGUARDANDO_PAGAMENTO', 'Aguardando Pagamento'
    CONFIRMADO = 'CONFIRMADO', 'Confirmado'
    CANCELADO = 'CANCELADO', 'Cancelado'

# ============================================
# MODELO: FUNDO
# ============================================

class Fundo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name='fundos')
    
    # Identificação
    cnpj = models.CharField(max_length=14, unique=True, db_index=True)
    codigo_anbima = models.CharField(max_length=6, unique=True, db_index=True, null=True, blank=True)
    razao_social = models.CharField(max_length=200)
    nome_comercial = models.CharField(max_length=200, blank=True)
    tipo_fundo = models.CharField(max_length=10, choices=TipoFundo.choices)
    data_constituicao = models.DateField()
    
    # Configurações
    tipo_cotizacao = models.CharField(max_length=10, default='D+0', help_text='D+0 ou D+1')
    prazo_liquidacao = models.IntegerField(default=0, help_text='Dias úteis')
    horario_corte = models.TimeField(default='14:00')
    
    # Taxas (% ao ano)
    taxa_administracao = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    taxa_gestao = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    
    # Status
    ativo = models.BooleanField(default=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    # JSON para flexibilidade
    politica_investimento = models.JSONField(null=True, blank=True)
    dados_adicionais = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'fundos'
        verbose_name = 'Fundo'
        verbose_name_plural = 'Fundos'
        ordering = ['-data_cadastro']
        indexes = [
            models.Index(fields=['cnpj']),
            models.Index(fields=['codigo_anbima']),
            models.Index(fields=['empresa', 'ativo']),
        ]
    
    def __str__(self):
        return f"{self.razao_social} ({self.cnpj})"

# ============================================
# MODELO: COTISTA
# ============================================

class Cotista(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Identificação
    cpf_cnpj = models.CharField(max_length=14, unique=True, db_index=True)
    tipo_pessoa = models.CharField(max_length=2, choices=[('PF', 'Pessoa Física'), ('PJ', 'Pessoa Jurídica')])
    nome_razao_social = models.CharField(max_length=200)
    email = models.EmailField(max_length=100, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    
    # Endereço
    cep = models.CharField(max_length=8, blank=True)
    logradouro = models.CharField(max_length=200, blank=True)
    numero = models.CharField(max_length=10, blank=True)
    complemento = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    uf = models.CharField(max_length=2, blank=True)
    
    # Compliance
    qualificacao = models.CharField(max_length=50, blank=True, help_text='Varejo, Qualificado, Profissional')
    perfil_investidor = models.CharField(max_length=50, blank=True)
    data_suitability = models.DateField(null=True, blank=True)
    
    # Dados bancários
    banco = models.CharField(max_length=3, blank=True)
    agencia = models.CharField(max_length=10, blank=True)
    conta = models.CharField(max_length=20, blank=True)
    
    # Status
    ativo = models.BooleanField(default=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    dados_adicionais = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'cotistas'
        verbose_name = 'Cotista'
        verbose_name_plural = 'Cotistas'
        ordering = ['nome_razao_social']
        indexes = [
            models.Index(fields=['cpf_cnpj']),
            models.Index(fields=['tipo_pessoa']),
        ]
    
    def __str__(self):
        return f"{self.nome_razao_social} ({self.cpf_cnpj})"

# ============================================
# MODELO: MOVIMENTAÇÃO DE COTAS
# ============================================

class MovimentacaoCota(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    tipo_movimentacao = models.CharField(
        max_length=20, 
        choices=[
            ('APLICACAO', 'Aplicação'),
            ('RESGATE', 'Resgate'),
            ('COME_COTAS', 'Come-Cotas'),
        ]
    )
    
    fundo = models.ForeignKey(Fundo, on_delete=models.PROTECT, related_name='movimentacoes')
    cotista = models.ForeignKey(Cotista, on_delete=models.PROTECT, related_name='movimentacoes')
    
    # Datas
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    data_cotizacao = models.DateField()
    data_liquidacao = models.DateField()
    
    # Valores
    valor_financeiro = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    valor_cota = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    quantidade_cotas = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    
    # Tributos
    ir_retido = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    iof_retido = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    valor_liquido = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=25, choices=StatusMovimentacao.choices, default=StatusMovimentacao.SOLICITADO)
    
    dados_adicionais = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'movimentacoes_cotas'
        verbose_name = 'Movimentação de Cota'
        verbose_name_plural = 'Movimentações de Cotas'
        ordering = ['-data_solicitacao']
        indexes = [
            models.Index(fields=['fundo', 'data_cotizacao']),
            models.Index(fields=['cotista', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.tipo_movimentacao} - {self.fundo.razao_social} - {self.data_solicitacao.date()}"

# ============================================
# MODELO: HISTÓRICO DE COTAS
# ============================================

class CotaHistorico(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fundo = models.ForeignKey(Fundo, on_delete=models.CASCADE, related_name='cotas_historico')
    data_referencia = models.DateField(db_index=True)
    
    # Valores
    valor_cota = models.DecimalField(max_digits=16, decimal_places=6)
    patrimonio_liquido = models.DecimalField(max_digits=16, decimal_places=2)
    quantidade_cotas = models.DecimalField(max_digits=18, decimal_places=6)
    quantidade_cotistas = models.IntegerField(default=0)
    
    # Movimentações do dia
    captacao_dia = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    resgate_dia = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    
    # Rentabilidade
    rentabilidade_dia = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    rentabilidade_mes = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    rentabilidade_ano = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    
    # Envio ANBIMA
    enviado_anbima = models.BooleanField(default=False)
    data_envio_anbima = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'cotas_historico'
        verbose_name = 'Histórico de Cota'
        verbose_name_plural = 'Histórico de Cotas'
        ordering = ['-data_referencia']
        unique_together = [['fundo', 'data_referencia']]
        indexes = [
            models.Index(fields=['fundo', '-data_referencia']),
            models.Index(fields=['data_referencia']),
        ]
    
    def __str__(self):
        return f"{self.fundo.razao_social} - {self.data_referencia} - R$ {self.valor_cota}"

# ============================================
# MODELO: ATIVOS
# ============================================

class Ativo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fundo = models.ForeignKey(Fundo, on_delete=models.PROTECT, related_name='ativos')
    
    tipo_ativo = models.CharField(max_length=50)
    codigo_isin = models.CharField(max_length=12, blank=True)
    codigo_negociacao = models.CharField(max_length=20, blank=True)
    emissor_cnpj = models.CharField(max_length=14, blank=True)
    emissor_nome = models.CharField(max_length=200, blank=True)
    
    # Quantidade e valores
    quantidade = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    preco_aquisicao = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    preco_mercado = models.DecimalField(max_digits=16, decimal_places=6, null=True, blank=True)
    valor_mercado = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    
    data_aquisicao = models.DateField(null=True, blank=True)
    data_vencimento = models.DateField(null=True, blank=True)
    
    # Renda Fixa
    taxa_cupom = models.DecimalField(max_digits=8, decimal_places=6, null=True, blank=True)
    indexador = models.CharField(max_length=20, blank=True)
    
    # Status
    ativo = models.BooleanField(default=True)
    dados_adicionais = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'ativos'
        verbose_name = 'Ativo'
        verbose_name_plural = 'Ativos'
        ordering = ['-data_aquisicao']
        indexes = [
            models.Index(fields=['fundo', 'ativo']),
            models.Index(fields=['tipo_ativo']),
        ]
    
    def __str__(self):
        return f"{self.tipo_ativo} - {self.codigo_isin or self.codigo_negociacao}"

# ============================================
# MODELO: RECEBÍVEIS (ESPECÍFICO FIDC)
# ============================================

class Recebiveis(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fundo = models.ForeignKey(Fundo, on_delete=models.PROTECT, related_name='recebiveis')
    
    # Cedente
    cedente_cnpj = models.CharField(max_length=14, db_index=True)
    cedente_nome = models.CharField(max_length=200)
    
    # Sacado
    sacado_cpf_cnpj = models.CharField(max_length=14, db_index=True)
    sacado_nome = models.CharField(max_length=200)
    
    # Título
    tipo_credito = models.CharField(max_length=50)
    numero_titulo = models.CharField(max_length=50)
    data_vencimento = models.DateField(db_index=True)
    
    # Valores
    valor_nominal = models.DecimalField(max_digits=16, decimal_places=2)
    valor_cessao = models.DecimalField(max_digits=16, decimal_places=2)
    
    # Inadimplência
    status = models.CharField(
        max_length=30, 
        default='A_VENCER',
        choices=[
            ('A_ENVIAR', 'A Enviar'),
            ('EM_COBRANCA', 'Em Cobrança'),
            ('A_VENCER', 'A Vencer'),
            ('VENCIDO', 'Vencido'),
            ('PAGO', 'Pago'),
            ('BAIXADO', 'Baixado'),
            ('REJEITADO', 'Rejeitado'),
        ]
    )
    dias_atraso = models.IntegerField(default=0)
    pdd_percentual = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    pdd_valor = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    
    dados_adicionais = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'recebiveis'
        verbose_name = 'Recebível'
        verbose_name_plural = 'Recebíveis'
        ordering = ['data_vencimento']
        indexes = [
            models.Index(fields=['fundo', 'status']),
            models.Index(fields=['cedente_cnpj']),
            models.Index(fields=['sacado_cpf_cnpj']),
            models.Index(fields=['data_vencimento']),
        ]
    
    def __str__(self):
        return f"{self.numero_titulo} - {self.sacado_nome}"