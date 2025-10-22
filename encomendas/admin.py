# encomendas/admin.py
from django.contrib import admin
from .models import (
    Cliente, Fornecedor, Produto, Encomenda, ItemEncomenda, Entrega,
    Usuario, Equipe, MembroEquipe, ConviteEquipe
)
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.urls import reverse # Import reverse
from django.utils.html import format_html # Import format_html

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nome', 'bairro', 'telefone', 'equipe']
    list_filter = ['equipe', 'bairro', 'created_at']
    search_fields = ['nome', 'codigo', 'endereco', 'equipe__nome']
    ordering = ['equipe', 'nome']
    # If using Django 4.0+, you might need list_select_related = ['equipe'] for performance

@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nome', 'telefone', 'email', 'equipe']
    list_filter = ['equipe', 'created_at']
    search_fields = ['nome', 'codigo', 'contato', 'equipe__nome']
    ordering = ['equipe', 'nome']

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nome', 'categoria', 'preco_base', 'equipe']
    list_filter = ['equipe', 'categoria', 'created_at']
    search_fields = ['nome', 'codigo', 'descricao', 'equipe__nome']
    ordering = ['equipe', 'nome']


class ItemEncomendaInline(admin.TabularInline):
    model = ItemEncomenda
    extra = 0
    fields = ['produto', 'fornecedor', 'quantidade', 'preco_cotado', 'valor_total', 'observacoes']
    readonly_fields = ['valor_total']
    autocomplete_fields = ['produto', 'fornecedor']

    # Limit choices based on Encomenda's equipe
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if obj and obj.equipe: # obj is the Encomenda instance
             # Ensure base_fields exists before modifying
            if hasattr(formset.form, 'base_fields'):
                formset.form.base_fields['produto'].queryset = Produto.objects.filter(equipe=obj.equipe)
                formset.form.base_fields['fornecedor'].queryset = Fornecedor.objects.filter(equipe=obj.equipe)
        else:
             if hasattr(formset.form, 'base_fields'):
                 formset.form.base_fields['produto'].queryset = Produto.objects.none()
                 formset.form.base_fields['fornecedor'].queryset = Fornecedor.objects.none()
        return formset


class EntregaInline(admin.StackedInline):
    model = Entrega
    extra = 0
    fields = [
        ('data_entrega', 'responsavel_entrega'),
        ('valor_pago_adiantamento'),
        ('data_entrega_realizada', 'hora_entrega'),
        ('entregue_por', 'assinatura_cliente'),
        ('observacoes_entrega'),
        ('data_prevista', 'data_realizada')
    ]
    readonly_fields = ['data_realizada']


@admin.register(Encomenda)
class EncomendaAdmin(admin.ModelAdmin):
    list_display = ['numero_encomenda', 'cliente', 'equipe', 'status', 'valor_total', 'data_criacao']
    list_filter = ['equipe', 'status', 'data_criacao', 'responsavel_criacao']
    search_fields = ['numero_encomenda', 'cliente__nome', 'cliente__codigo', 'equipe__nome']
    ordering = ['-numero_encomenda']
    readonly_fields = ['numero_encomenda', 'data_criacao', 'valor_total', 'updated_at']
    inlines = [ItemEncomendaInline, EntregaInline]
    autocomplete_fields = ['cliente']

    fieldsets = (
        ('Informações Básicas', {
            'fields': ('numero_encomenda', 'equipe', 'cliente', 'data_encomenda', 'data_criacao', 'responsavel_criacao', 'updated_at')
        }),
        ('Status e Valores', {
            'fields': ('status', 'valor_total', 'observacoes')
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Ensure base_fields exists before modifying
        if hasattr(form, 'base_fields'):
            if obj and obj.equipe:
                form.base_fields['cliente'].queryset = Cliente.objects.filter(equipe=obj.equipe)
            elif not obj: # If creating new, limit choices based on user's teams?
                 # This part can be complex in admin, requires knowing which team is being selected
                 # For simplicity, maybe filter based on the *first* team the user belongs to?
                 user_teams = request.user.equipes.all()
                 if user_teams.exists():
                      # Initially filter clients based on the first team or handle via JS
                      # form.base_fields['cliente'].queryset = Cliente.objects.filter(equipe=user_teams.first())
                      # You might also need to filter the 'equipe' field itself if it's editable
                      form.base_fields['equipe'].queryset = user_teams

                 else: # User not in any team, show no clients
                      form.base_fields['cliente'].queryset = Cliente.objects.none()
                      form.base_fields['equipe'].queryset = Equipe.objects.none()

        return form


@admin.register(ItemEncomenda)
class ItemEncomendaAdmin(admin.ModelAdmin):
    list_display = ['get_encomenda_link', 'produto', 'fornecedor', 'quantidade', 'preco_cotado', 'valor_total']
    list_filter = ['encomenda__equipe', 'encomenda__status', 'produto__categoria']
    search_fields = ['encomenda__numero_encomenda', 'produto__nome', 'fornecedor__nome', 'encomenda__equipe__nome']
    readonly_fields = ['valor_total']
    autocomplete_fields = ['encomenda', 'produto', 'fornecedor']

    def get_encomenda_link(self, obj):
        link = reverse("admin:encomendas_encomenda_change", args=[obj.encomenda.pk])
        return format_html('<a href="{}">#{}</a>', link, obj.encomenda.numero_encomenda)
    get_encomenda_link.short_description = 'Encomenda'


@admin.register(Entrega)
class EntregaAdmin(admin.ModelAdmin):
    list_display = ['get_encomenda_link', 'data_entrega', 'responsavel_entrega', 'data_entrega_realizada', 'entregue_por']
    list_filter = ['encomenda__equipe', 'data_entrega', 'data_entrega_realizada', 'responsavel_entrega']
    search_fields = ['encomenda__numero_encomenda', 'responsavel_entrega', 'entregue_por', 'encomenda__equipe__nome']
    # --- UPDATED readonly_fields ---
    readonly_fields = ['display_valor_restante', 'data_realizada'] # Use the method name here
    autocomplete_fields = ['encomenda']

    fieldsets = (
        (None, {
            'fields': ('encomenda',)
        }),
        ('Programação (Formulário Físico)', {
            'fields': ('data_entrega', 'responsavel_entrega', 'valor_pago_adiantamento')
        }),
        ('Execução da Entrega', {
            'fields': ('data_entrega_realizada', 'hora_entrega', 'entregue_por', 'assinatura_cliente')
        }),
        ('Controle Interno / Observações', {
            # --- UPDATED fieldsets ---
            'fields': ('data_prevista', 'data_realizada', 'display_valor_restante', 'observacoes_entrega'), # Use the method name here too
            'classes': ('collapse',)
        }),
    )

    def get_encomenda_link(self, obj):
        link = reverse("admin:encomendas_encomenda_change", args=[obj.encomenda.pk])
        return format_html('<a href="{}">#{}</a>', link, obj.encomenda.numero_encomenda)
    get_encomenda_link.short_description = 'Encomenda'

    # --- ADDED METHOD ---
    @admin.display(description='Valor Restante (R$)') # Set a nice column header
    def display_valor_restante(self, obj):
        # This method calls the @property on the model instance (obj)
        return obj.valor_restante
    # --- END ADDED METHOD ---


# --- Auth Admin classes remain the same ---
@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informações Adicionais', {'fields': ('nome_completo', 'identificacao', 'cargo', 'telefone', 'ativo')}),
    )
    list_display = ('email', 'nome_completo', 'cargo', 'ativo', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'ativo')
    search_fields = ('nome_completo', 'email', 'identificacao')


@admin.register(Equipe)
class EquipeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'administrador', 'ativa', 'get_member_count')
    list_filter = ('ativa',)
    search_fields = ('nome', 'administrador__nome_completo', 'administrador__email')
    filter_horizontal = ('membros',)

    def get_member_count(self, obj):
        return obj.membros.count()
    get_member_count.short_description = 'Nº Membros'


@admin.register(MembroEquipe)
class MembroEquipeAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'equipe', 'papel')
    list_filter = ('equipe', 'papel')
    search_fields = ('usuario__nome_completo', 'usuario__email', 'equipe__nome')
    autocomplete_fields = ['usuario', 'equipe']


@admin.register(ConviteEquipe)
class ConviteEquipeAdmin(admin.ModelAdmin):
    list_display = ('email', 'equipe', 'papel', 'status', 'criado_por', 'data_criacao', 'data_expiracao')
    list_filter = ('equipe', 'status', 'papel')
    search_fields = ('email', 'equipe__nome', 'criado_por__nome_completo')
    readonly_fields = ('data_criacao', 'data_resposta')
    autocomplete_fields = ['equipe', 'criado_por']