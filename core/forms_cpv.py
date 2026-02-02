from django import forms
from decimal import Decimal
from fundos.models import Fundo

# =====================================================
# FORM — OPERAÇÃO CPV (dados gerais)
# =====================================================

class CpvOperacaoForm(forms.Form):
    # -------- Upload --------
    xml_file = forms.FileField(
        label="XML da NF-e",
        required=True
    )

    fundo = forms.ModelChoiceField(
        queryset=Fundo.objects.filter(ativo=True),
        label="Fundo FIDC",
        required=True
    )

    # -------- Dados da operação --------

    data_contrato = forms.DateField(
        label="Data do Contrato",
        widget=forms.DateInput(attrs={"type": "date"})
    )

    preco_aquisicao = forms.DecimalField(
        label="Preço de Aquisição",
        max_digits=16,
        decimal_places=2
    )

    banco = forms.CharField(max_length=100)
    agencia = forms.CharField(max_length=20)
    conta = forms.CharField(max_length=30)

    cessionario_nome = forms.CharField(max_length=200)
    cessionario_doc = forms.CharField(max_length=20)


# =====================================================
# FORM — LINHA DE TÍTULO (editável)
# =====================================================

class TituloCessaoForm(forms.Form):
    numero = forms.CharField(
        label="Número",
        max_length=50,
        required=False
    )

    sacado_nome = forms.CharField(max_length=200)

    sacado_doc = forms.CharField(max_length=20)

    valor = forms.DecimalField(
        max_digits=16,
        decimal_places=2
    )

    vencimento = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"})
    )

    tipo = forms.CharField(
        max_length=50,
        initial="Duplicata"
    )

    excluir = forms.BooleanField(
        required=False,
        label="Excluir"
    )

# =====================================================
# FORMSET — MÚLTIPLOS TÍTULOS
# =====================================================
TituloCessaoFormSet = forms.formset_factory(
    TituloCessaoForm,
    extra=0,
    can_delete=False
)
