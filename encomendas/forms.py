from django import forms
from django.forms import inlineformset_factory
from .models import Encomenda, Cliente, Produto, Fornecedor, ItemEncomenda, Entrega
from datetime import date


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'codigo', 'endereco', 'bairro', 'referencia', 'telefone']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo do cliente'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Código único do cliente'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Endereço completo'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bairro'}),
            'referencia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ponto de referência (opcional)'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(XX) XXXXX-XXXX'}),
        }


class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = ['nome', 'codigo', 'contato', 'telefone', 'email']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do fornecedor'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Código único do fornecedor'}),
            'contato': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do contato'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(XX) XXXXX-XXXX'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemplo.com'}),
        }


class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ['nome', 'codigo', 'descricao', 'preco_base', 'categoria']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do produto'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Código único do produto'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição detalhada (opcional)'}),
            'preco_base': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'categoria': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Categoria do produto (opcional)'}),
        }


class EncomendaForm(forms.ModelForm):
    class Meta:
        model = Encomenda
        fields = ['cliente', 'data_encomenda', 'responsavel_criacao', 'status', 'observacoes']
        widgets = {
            # Use form-select for dropdowns
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'data_encomenda': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'responsavel_criacao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do responsável'}),
             # Use form-select for dropdowns
            'status': forms.Select(attrs={'class': 'form-select'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Observações gerais sobre a encomenda (campo Observação do formulário físico)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.all().order_by('nome')
        self.fields['cliente'].empty_label = "Selecione um cliente"

        # Definir data padrão como hoje se não especificada
        if not self.instance.pk and 'data_encomenda' not in self.initial:
            self.initial['data_encomenda'] = date.today()


class ItemEncomendaForm(forms.ModelForm):
    class Meta:
        model = ItemEncomenda
        fields = ['produto', 'fornecedor', 'quantidade', 'preco_cotado', 'observacoes']
        widgets = {
             # Use form-select for dropdowns
            'produto': forms.Select(attrs={'class': 'form-select produto-select'}),
             # Use form-select for dropdowns
            'fornecedor': forms.Select(attrs={'class': 'form-select'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'value': '1'}),
            'preco_cotado': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'observacoes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Observações do item (opcional)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['produto'].queryset = Produto.objects.all().order_by('nome')
        self.fields['fornecedor'].queryset = Fornecedor.objects.all().order_by('nome')
        self.fields['produto'].empty_label = "Selecione um produto"
        self.fields['fornecedor'].empty_label = "Selecione um fornecedor"


# Formset for encomenda items
ItemEncomendaFormSet = inlineformset_factory(
    Encomenda,
    ItemEncomenda,
    form=ItemEncomendaForm,
    extra=0, # Changed from 0 back to 1
    can_delete=True,
    min_num=1, # Keep minimum as 1
    validate_min=True
)


class EntregaForm(forms.ModelForm):
    class Meta:
        model = Entrega
        fields = [
            'data_entrega', 'responsavel_entrega', 'valor_pago_adiantamento',
            'data_entrega_realizada', 'hora_entrega', 'entregue_por', 'assinatura_cliente',
            'data_prevista', 'observacoes_entrega'
        ]
        widgets = {
            'data_entrega': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'responsavel_entrega': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Responsável pela entrega'}),
            'valor_pago_adiantamento': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'data_entrega_realizada': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hora_entrega': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'entregue_por': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome de quem entregou'}),
            'assinatura_cliente': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Assinatura do cliente'}),
            'data_prevista': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observacoes_entrega': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observações sobre a entrega'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['data_entrega'].required = True
        self.fields['responsavel_entrega'].required = True
        self.fields['data_entrega_realizada'].required = False
        self.fields['hora_entrega'].required = False
        self.fields['entregue_por'].required = False
        self.fields['assinatura_cliente'].required = False
        self.fields['data_prevista'].required = False
        self.fields['observacoes_entrega'].required = False

        if not self.instance.pk and 'data_entrega' not in self.initial:
            self.initial['data_entrega'] = date.today()


class FiltroEncomendaForm(forms.Form):
    """Formulário para filtros na listagem de encomendas"""
    STATUS_CHOICES = [('', 'Todos os status')] + list(Encomenda.STATUS_CHOICES)

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        # Use form-select for dropdowns
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.all().order_by('nome'),
        required=False,
        empty_label="Todos os clientes",
        # Use form-select for dropdowns
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por número, cliente ou código...'
        })
    )