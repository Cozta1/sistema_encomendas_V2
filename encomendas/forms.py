# encomendas/forms.py
from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import Encomenda, Cliente, Produto, Fornecedor, ItemEncomenda, Entrega, Equipe # Import Equipe
from datetime import date

# --- Base Forms for Cliente, Fornecedor, Produto ---
# These might not need changes if 'equipe' is set in the view
# Or, add 'equipe' to fields/exclude if needed.
class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        # Exclude equipe, it will be set in the view based on context
        exclude = ['equipe', 'created_at', 'updated_at']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo do cliente'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Código único do cliente (na equipe)'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Endereço completo'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bairro'}),
            'referencia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ponto de referência (opcional)'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(XX) XXXXX-XXXX'}),
        }

class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        # Exclude equipe
        exclude = ['equipe', 'created_at', 'updated_at']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do fornecedor'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Código único do fornecedor (na equipe)'}),
            'contato': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do contato'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(XX) XXXXX-XXXX'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemplo.com'}),
        }


class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        # Exclude equipe
        exclude = ['equipe', 'created_at', 'updated_at']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do produto'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Código único do produto (na equipe)'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição detalhada (opcional)'}),
            'preco_base': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'categoria': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Categoria do produto (opcional)'}),
        }

# --- Encomenda Form (Updated to filter choices by team) ---
class EncomendaForm(forms.ModelForm):
    class Meta:
        model = Encomenda
        # Exclude 'equipe' as it's set by the view context
        fields = ['cliente', 'data_encomenda', 'responsavel_criacao', 'status', 'observacoes']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}), # Choices filtered in __init__
            'data_encomenda': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'responsavel_criacao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do responsável'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Observações gerais sobre a encomenda...'}),
        }

    # Accept equipe as an argument
    def __init__(self, *args, **kwargs):
        equipe = kwargs.pop('equipe', None) # Get equipe from kwargs passed by view
        super().__init__(*args, **kwargs)

        if equipe:
            # Filter cliente choices to only those belonging to the specified equipe
            self.fields['cliente'].queryset = Cliente.objects.filter(equipe=equipe).order_by('nome')
        else:
            # If no equipe provided (e.g., editing an old record?), show all or none?
            self.fields['cliente'].queryset = Cliente.objects.none() # Safer default

        self.fields['cliente'].empty_label = "Selecione um cliente da equipe"

        if not self.instance.pk and 'data_encomenda' not in self.initial:
            self.initial['data_encomenda'] = date.today()


# --- ItemEncomenda Form (Updated to filter choices by team) ---
class ItemEncomendaForm(forms.ModelForm):
    class Meta:
        model = ItemEncomenda
        fields = ['produto', 'fornecedor', 'quantidade', 'preco_cotado', 'observacoes']
        widgets = {
            'produto': forms.Select(attrs={'class': 'form-select produto-select'}), # Filtered in __init__
            'fornecedor': forms.Select(attrs={'class': 'form-select'}), # Filtered in __init__
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'value': '1'}),
            'preco_cotado': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'observacoes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Observações do item (opcional)'}),
        }

    # Accept equipe as an argument
    def __init__(self, *args, **kwargs):
        equipe = kwargs.pop('equipe', None) # Get equipe from kwargs
        super().__init__(*args, **kwargs)

        if equipe:
            # Filter produto and fornecedor choices by the specified equipe
            self.fields['produto'].queryset = Produto.objects.filter(equipe=equipe).order_by('nome')
            self.fields['fornecedor'].queryset = Fornecedor.objects.filter(equipe=equipe).order_by('nome')
        else:
            self.fields['produto'].queryset = Produto.objects.none()
            self.fields['fornecedor'].queryset = Fornecedor.objects.none()

        self.fields['produto'].empty_label = "Selecione um produto da equipe"
        self.fields['fornecedor'].empty_label = "Selecione um fornecedor da equipe"

# --- Base FormSet to pass kwargs to forms ---
class BaseItemEncomendaFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        # Pop the custom kwarg before passing to super
        self.form_kwargs = kwargs.pop('form_kwargs', {})
        super().__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        # Pass the stored kwargs to each form instance
        kwargs.update(self.form_kwargs)
        return super()._construct_form(i, **kwargs)


# --- ItemEncomenda Formset (Using the base class) ---
ItemEncomendaFormSet = inlineformset_factory(
    Encomenda,
    ItemEncomenda,
    form=ItemEncomendaForm,
    formset=BaseItemEncomendaFormSet, # Use the custom base class
    extra=1, # Start with one empty form
    can_delete=True,
    min_num=1,
    validate_min=True
)


# --- Entrega Form remains the same ---
class EntregaForm(forms.ModelForm):
    class Meta:
        model = Entrega
        # Define fields explicitly matching the model
        fields = [
            'data_entrega', 'responsavel_entrega', 'valor_pago_adiantamento',
            'data_entrega_realizada', 'hora_entrega', 'entregue_por',
            'assinatura_cliente', 'data_prevista', 'observacoes_entrega'
        ]
        widgets = {
            # Use 'date' and 'time' types for better browser UI
            'data_entrega': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'responsavel_entrega': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Responsável pela entrega'}),
            'valor_pago_adiantamento': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00', 'min': '0'}),
            'data_entrega_realizada': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hora_entrega': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'entregue_por': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome de quem entregou'}),
            # Use CheckboxInput for BooleanField
            'assinatura_cliente': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'data_prevista': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}), # Internal field, maybe hide?
            'observacoes_entrega': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observações sobre a entrega'}),
        }
        # Add labels if they differ from model verbose_name
        labels = {
            'data_entrega': "Data Programada (Entrega)",
            'valor_pago_adiantamento': "Valor Adiantado (R$)",
            'data_entrega_realizada': "Data Efetiva (Realizada)",
            'hora_entrega': "Hora Efetiva (Realizada)",
            'assinatura_cliente': "Cliente Assinou Recebimento?",
            'data_prevista': "Data Prevista (Interno)", # Clarify internal use
        }

    # Set required fields if not handled by model definition
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # These match the physical form's requirements more closely
        self.fields['data_entrega'].required = True
        self.fields['responsavel_entrega'].required = True
        # Fields related to actual delivery are not required initially
        self.fields['data_entrega_realizada'].required = False
        self.fields['hora_entrega'].required = False
        self.fields['entregue_por'].required = False
        self.fields['assinatura_cliente'].required = False
        # Internal fields are likely not required
        self.fields['data_prevista'].required = False
        self.fields['observacoes_entrega'].required = False

        # Set default date for new instances
        if not self.instance.pk and 'data_entrega' not in self.initial:
            self.initial['data_entrega'] = date.today()


# --- Filter Forms ---
class FiltroEncomendaForm(forms.Form):
    """Filtro para listagem de encomendas, adaptado para equipes."""
    STATUS_CHOICES = [('', 'Todos os status')] + list(Encomenda.STATUS_CHOICES)

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    # Cliente choices filtered based on user's teams
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.none(), # Set in __init__
        required=False,
        empty_label="Todos os clientes",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    # Team filter
    equipe = forms.ModelChoiceField(
        queryset=Equipe.objects.none(), # Set in __init__
        required=False,
        empty_label="Todas as minhas equipes",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Filtrar por Equipe"
    )
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por número, cliente, produto...'
        })
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) # Get user passed from view
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated:
            user_equipes = user.equipes.all()
            # Filter cliente choices based on the user's teams
            self.fields['cliente'].queryset = Cliente.objects.filter(equipe__in=user_equipes).order_by('nome')
            # Populate team filter choices with the user's teams
            self.fields['equipe'].queryset = user_equipes.order_by('nome')


# Simple search forms for team-specific lists
class FiltroClienteForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Buscar cliente...'})
    )

class FiltroProdutoForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Buscar produto...'})
    )

class FiltroFornecedorForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Buscar fornecedor...'})
    )