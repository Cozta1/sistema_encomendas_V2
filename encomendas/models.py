# encomendas/models.py
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
from django.conf import settings # Import settings if needed later, e.g. for AUTH_USER_MODEL

# Imports moved from models_auth.py
from django.contrib.auth.models import AbstractUser
import uuid

# --- Cliente, Fornecedor, Produto Models remain the same ---
class Cliente(models.Model):
    nome = models.CharField(max_length=200, verbose_name="Nome do Cliente")
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código")
    endereco = models.TextField(verbose_name="Endereço")
    bairro = models.CharField(max_length=100, verbose_name="Bairro")
    referencia = models.CharField(max_length=200, blank=True, verbose_name="Referência")
    telefone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nome']

    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class Fornecedor(models.Model):
    nome = models.CharField(max_length=200, verbose_name="Nome do Fornecedor")
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código")
    contato = models.CharField(max_length=200, blank=True, verbose_name="Contato")
    telefone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    email = models.EmailField(blank=True, verbose_name="E-mail")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"
        ordering = ['nome']

    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class Produto(models.Model):
    nome = models.CharField(max_length=200, verbose_name="Nome do Produto")
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    preco_base = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Preço Base"
    )
    categoria = models.CharField(max_length=100, blank=True, verbose_name="Categoria")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ['nome']

    def __str__(self):
        return f"{self.codigo} - {self.nome}"

# --- Equipe Model (needed before Encomenda) ---
class Equipe(models.Model):
    """Modelo para equipes de usuários"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID da Equipe"
    )
    nome = models.CharField(
        max_length=200,
        verbose_name="Nome da Equipe"
    )
    descricao = models.TextField(
        blank=True,
        verbose_name="Descrição"
    )
    administrador = models.ForeignKey(
        # Use settings.AUTH_USER_MODEL for flexibility
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, # Consider PROTECT or SET_NULL if admin deletion shouldn't delete team
        related_name='equipes_administradas',
        verbose_name="Administrador"
    )
    membros = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='MembroEquipe',
        related_name='equipes',
        verbose_name="Membros"
    )
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação"
    )
    data_atualizacao = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Atualização"
    )
    ativa = models.BooleanField(
        default=True,
        verbose_name="Equipe Ativa"
    )

    class Meta:
        verbose_name = "Equipe"
        verbose_name_plural = "Equipes"
        ordering = ['nome']

    def __str__(self):
        return self.nome

    def adicionar_membro(self, usuario, papel='membro'):
        """Adiciona um membro à equipe"""
        membro, criado = MembroEquipe.objects.get_or_create(
            equipe=self,
            usuario=usuario,
            defaults={'papel': papel}
        )
        return membro, criado

    def remover_membro(self, usuario):
        """Remove um membro da equipe"""
        MembroEquipe.objects.filter(
            equipe=self,
            usuario=usuario
        ).delete()

    def get_membro(self, usuario):
        """Retorna o objeto MembroEquipe para um usuário, se existir."""
        try:
            return MembroEquipe.objects.get(equipe=self, usuario=usuario)
        except MembroEquipe.DoesNotExist:
            return None

    def eh_administrador(self, usuario):
        """Verifica se um usuário é o administrador principal da equipe"""
        return self.administrador == usuario

    def pode_gerenciar(self, usuario):
        """Verifica se um usuário tem permissão para gerenciar (admin ou gerente)."""
        if self.eh_administrador(usuario):
            return True
        membro = self.get_membro(usuario)
        return membro and membro.papel in ['administrador', 'gerente'] # Allow 'administrador' role too

    def eh_membro(self, usuario):
        """Verifica se um usuário é membro da equipe (qualquer papel)"""
        return self.membros.filter(id=usuario.id).exists()

# --- Encomenda Model ---
class Encomenda(models.Model):
    STATUS_CHOICES = [
        ('criada', 'Criada'),
        ('cotacao', 'Em Cotação'),
        ('aprovada', 'Aprovada'),
        ('em_andamento', 'Em Andamento'),
        ('pronta', 'Pronta para Entrega'),
        ('entregue', 'Entregue'),
        ('cancelada', 'Cancelada'),
    ]

    numero_encomenda = models.AutoField(primary_key=True, verbose_name="Número da Encomenda")
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, verbose_name="Cliente")

    # *** NEW FIELD: Link to Team ***
    # null=True, blank=True allows existing encomendas without a team
    # Consider null=False, blank=False for new projects, requiring a team always
    equipe = models.ForeignKey(
        Equipe,
        on_delete=models.SET_NULL, # Or CASCADE if orders should be deleted with team
        null=True,
        blank=True,
        related_name='encomendas',
        verbose_name="Equipe Responsável"
    )

    # Campos do cabeçalho do formulário físico
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação (sistema)")
    data_encomenda = models.DateField(verbose_name="Data", help_text="Data da encomenda (campo do cabeçalho)", default=timezone.now)
    responsavel_criacao = models.CharField(max_length=100, verbose_name="Responsável",
                                         help_text="Responsável pela criação da encomenda")

    # Status e observações
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='criada', verbose_name="Status")
    observacoes = models.TextField(blank=True, verbose_name="Observação",
                                 help_text="Campo 'Observação' do formulário físico")

    # Valores
    valor_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Valor do Produto",
        help_text="Valor total dos produtos da encomenda"
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Encomenda"
        verbose_name_plural = "Encomendas"
        ordering = ['-numero_encomenda']

    def __str__(self):
        return f"Encomenda {self.numero_encomenda} - {self.cliente.nome}"

    def calcular_valor_total(self):
        """Calcula o valor total baseado nos itens da encomenda"""
        total = sum(item.valor_total for item in self.itens.all() if item.valor_total is not None)
        self.valor_total = total
        # Note: Avoid calling self.save() within calculation if possible to prevent recursion.
        # Let the calling view handle the save after calculation.
        # However, keeping it here for consistency with original code for now.
        self.save()
        return total


# --- ItemEncomenda and Entrega Models remain the same ---
class ItemEncomenda(models.Model):
    encomenda = models.ForeignKey(Encomenda, related_name='itens', on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, verbose_name="Produto")
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.CASCADE, verbose_name="Fornecedor")
    quantidade = models.PositiveIntegerField(default=1, verbose_name="Quantidade")
    preco_cotado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Preço Cotado"
    )
    valor_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Valor Total"
    )
    observacoes = models.TextField(blank=True, verbose_name="Observações")

    class Meta:
        verbose_name = "Item da Encomenda"
        verbose_name_plural = "Itens da Encomenda"

    def save(self, *args, **kwargs):
        """Calcula o valor total do item automaticamente"""
        if self.quantidade is not None and self.preco_cotado is not None:
            self.valor_total = self.quantidade * self.preco_cotado
        else:
             self.valor_total = Decimal('0.00')
        super().save(*args, **kwargs)
        # Atualiza o valor total da encomenda AFTER saving the item
        # self.encomenda.calcular_valor_total() # Better called from the view after formset save

    def delete(self, *args, **kwargs):
        encomenda = self.encomenda
        super().delete(*args, **kwargs)
        # Recalculate after delete
        # encomenda.calcular_valor_total() # Better called from the view

    def __str__(self):
        return f"{self.produto.nome} - Qtd: {self.quantidade}"


class Entrega(models.Model):
    encomenda = models.OneToOneField(Encomenda, on_delete=models.CASCADE, verbose_name="Encomenda", related_name='entrega') # Added related_name

    # Campos de programação da entrega (seção superior do formulário)
    data_entrega = models.DateField(verbose_name="Data Entrega",
                                  help_text="Campo 'Data Entrega' do formulário físico",
                                  default=timezone.now) # Changed from data_prevista
    responsavel_entrega = models.CharField(max_length=100, verbose_name="Responsável Entrega",
                                         help_text="Campo 'Responsável Entrega' do formulário físico",
                                         default="A definir") # Changed from responsavel

    # Campos de pagamento
    valor_pago_adiantamento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Valor Pago Adiantamento",
        help_text="Campo 'Valor Pago Adiantamento' do formulário físico"
    ) # Changed from valor_adiantamento

    # Campos da seção inferior (caixa destacada)
    # Renamed from data_entrega_realizada_form for clarity
    data_entrega_realizada = models.DateField(null=True, blank=True, verbose_name="Data (Realizada)",
                                            help_text="Data da entrega realizada (seção inferior)")
    hora_entrega = models.TimeField(null=True, blank=True, verbose_name="Hora (Realizada)", # Changed from hora_prevista
                                  help_text="Hora da entrega (seção inferior)")
    entregue_por = models.CharField(max_length=100, blank=True, verbose_name="Entregue por",
                                  help_text="Campo 'Entregue por' da seção inferior")

    # Campo de assinatura - Changed to Boolean for simplicity, can be TextField if storing image/data URL
    assinatura_cliente = models.BooleanField(default=False, verbose_name="Ass. do Cliente", # Changed type
                                        help_text="Marcar se o cliente assinou")

    # Campos adicionais para controle interno
    data_prevista = models.DateField(null=True, blank=True, verbose_name="Data Prevista (Controle Interno)") # Kept for internal planning
    data_realizada = models.DateTimeField(null=True, blank=True, verbose_name="Data/Hora Realizada (Controle Interno)")
    observacoes_entrega = models.TextField(blank=True, verbose_name="Observações da Entrega")

    class Meta:
        verbose_name = "Entrega"
        verbose_name_plural = "Entregas"

    def __str__(self):
        return f"Entrega - Encomenda {self.encomenda.numero_encomenda}"

    @property
    def valor_restante(self):
        """Calcula o valor restante a ser pago"""
        return self.encomenda.valor_total - self.valor_pago_adiantamento

    # Keep for compatibility if needed elsewhere
    @property
    def valor_adiantamento(self):
        """Compatibilidade com templates existentes"""
        return self.valor_pago_adiantamento


# --- Models moved from models_auth.py ---

class Usuario(AbstractUser):
    """Modelo de usuário customizado com campos adicionais"""

    # Sobrescrever campos padrão
    email = models.EmailField(unique=True, verbose_name="Email")
    # Username is still required by AbstractUser but we'll use email for login
    # Set USERNAME_FIELD = 'email' if you haven't already

    # Campos adicionais
    nome_completo = models.CharField(
        max_length=255,
        verbose_name="Nome Completo"
    )
    identificacao = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Identificação (CPF/CNPJ)" # Add validators if needed
    )
    cargo = models.CharField(
        max_length=100,
        verbose_name="Cargo"
    )
    telefone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Telefone"
    )
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação"
    )
    data_atualizacao = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Atualização"
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name="Usuário Ativo" # Renamed from is_active for clarity, AbstractUser still has is_active
    )

    # Campos para redefinição de senha
    token_reset_senha = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True, # Ensure unique=True if it wasn't
        verbose_name="Token de Reset de Senha"
    )
    data_expiracao_token = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Data de Expiração do Token"
    )

    # Required settings for using email as username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'nome_completo', 'identificacao', 'cargo'] # username needed for createsuperuser

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ['nome_completo']

    def __str__(self):
        return f"{self.nome_completo} ({self.email})"

    def gerar_token_reset(self):
        """Gera um token único para redefinição de senha"""
        self.token_reset_senha = str(uuid.uuid4())
        self.data_expiracao_token = timezone.now() + timezone.timedelta(hours=24) # Use timezone.timedelta
        self.save()
        return self.token_reset_senha

    def token_reset_valido(self):
        """Verifica se o token de reset ainda é válido"""
        if not self.token_reset_senha or not self.data_expiracao_token:
            return False
        return timezone.now() < self.data_expiracao_token

    def limpar_token_reset(self):
        """Remove o token de reset de senha"""
        self.token_reset_senha = None
        self.data_expiracao_token = None
        self.save()


# --- MembroEquipe needs Usuario and Equipe defined first ---
class MembroEquipe(models.Model):
    """Modelo de relacionamento entre usuários e equipes"""

    PAPEL_CHOICES = (
        ('administrador', 'Administrador'), # Added admin role explicitly
        ('gerente', 'Gerente'),
        ('membro', 'Membro'),
    )

    equipe = models.ForeignKey(
        Equipe,
        on_delete=models.CASCADE,
        verbose_name="Equipe"
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Usuário"
    )
    papel = models.CharField(
        max_length=20,
        choices=PAPEL_CHOICES,
        default='membro',
        verbose_name="Papel"
    )
    data_adesao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Adesão"
    )
    data_atualizacao = models.DateTimeField(
        auto_now=True,
        verbose_name="Última Atualização"
    )

    class Meta:
        verbose_name = "Membro da Equipe"
        verbose_name_plural = "Membros da Equipe"
        unique_together = ('equipe', 'usuario')
        ordering = ['usuario__nome_completo']

    def __str__(self):
        # Use get_papel_display() for readable role name
        return f"{self.usuario.nome_completo} - {self.equipe.nome} ({self.get_papel_display()})"


class ConviteEquipe(models.Model):
    """Modelo para convites de equipe"""

    STATUS_CHOICES = (
        ('pendente', 'Pendente'),
        ('aceito', 'Aceito'),
        ('rejeitado', 'Rejeitado'),
        ('expirado', 'Expirado'),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID do Convite"
    )
    equipe = models.ForeignKey(
        Equipe,
        on_delete=models.CASCADE,
        related_name='convites',
        verbose_name="Equipe"
    )
    email = models.EmailField(
        verbose_name="Email do Convidado"
    )
    papel = models.CharField(
        max_length=20,
        choices=MembroEquipe.PAPEL_CHOICES, # Use choices from MembroEquipe
        default='membro',
        verbose_name="Papel"
    )
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Keep invite even if creator is deleted
        null=True,
        related_name='convites_enviados',
        verbose_name="Criado por"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendente',
        verbose_name="Status"
    )
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação"
    )
    data_expiracao = models.DateTimeField(
        verbose_name="Data de Expiração" # Set this when creating
    )
    data_resposta = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Data de Resposta"
    )

    class Meta:
        verbose_name = "Convite de Equipe"
        verbose_name_plural = "Convites de Equipe"
        ordering = ['-data_criacao']

    def __str__(self):
        return f"Convite para {self.email} - {self.equipe.nome}"

    def eh_valido(self):
        """Verifica se o convite ainda é válido"""
        return (
            self.status == 'pendente' and
            timezone.now() < self.data_expiracao
        )

    def aceitar(self, usuario):
        """Aceita o convite e adiciona o usuário à equipe"""
        if not self.eh_valido() or self.email != usuario.email: # Check email match
            return False

        # Adicionar membro à equipe
        self.equipe.adicionar_membro(usuario, self.papel)

        # Atualizar status do convite
        self.status = 'aceito'
        self.data_resposta = timezone.now()
        self.save()

        return True

    def rejeitar(self):
        """Rejeita o convite"""
        # Could add check if status is 'pendente'
        self.status = 'rejeitado'
        self.data_resposta = timezone.now()
        self.save()
        # Optionally, delete expired/rejected invites after some time via a task