# encomendas/models.py
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
from django.conf import settings # Import settings if needed later, e.g. for AUTH_USER_MODEL

# Imports moved from models_auth.py
from django.contrib.auth.models import AbstractUser
import uuid

# --- Equipe Model (needed before Cliente, Fornecedor, Produto if FK is mandatory) ---
# Assuming Equipe model exists as previously defined
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
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
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

    # Methods like adicionar_membro, remover_membro, get_membro, eh_administrador, pode_gerenciar, eh_membro remain the same
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

# --- Cliente, Fornecedor, Produto Models updated ---
class Cliente(models.Model):
    # Added ForeignKey to Equipe
    equipe = models.ForeignKey(
        Equipe,
        on_delete=models.CASCADE, # Or models.SET_NULL if a client can exist without a team
        related_name='clientes',
        verbose_name="Equipe",
        null=True, # Make optional initially for easier migration
        blank=True # Make optional initially for easier migration
    )
    nome = models.CharField(max_length=200, verbose_name="Nome do Cliente")
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código") # Consider making unique_together with equipe
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
        # unique_together = ('equipe', 'codigo') # Enforce code uniqueness per team if needed

    def __str__(self):
        team_name = f" ({self.equipe.nome})" if self.equipe else ""
        return f"{self.codigo} - {self.nome}{team_name}"


class Fornecedor(models.Model):
    # Added ForeignKey to Equipe
    equipe = models.ForeignKey(
        Equipe,
        on_delete=models.CASCADE,
        related_name='fornecedores',
        verbose_name="Equipe",
        null=True, # Make optional initially for easier migration
        blank=True # Make optional initially for easier migration
    )
    nome = models.CharField(max_length=200, verbose_name="Nome do Fornecedor")
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código") # Consider making unique_together with equipe
    contato = models.CharField(max_length=200, blank=True, verbose_name="Contato")
    telefone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    email = models.EmailField(blank=True, verbose_name="E-mail")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"
        ordering = ['nome']
        # unique_together = ('equipe', 'codigo') # Enforce code uniqueness per team if needed

    def __str__(self):
        team_name = f" ({self.equipe.nome})" if self.equipe else ""
        return f"{self.codigo} - {self.nome}{team_name}"


class Produto(models.Model):
    # Added ForeignKey to Equipe
    equipe = models.ForeignKey(
        Equipe,
        on_delete=models.CASCADE,
        related_name='produtos',
        verbose_name="Equipe",
        null=True, # Make optional initially for easier migration
        blank=True # Make optional initially for easier migration
    )
    nome = models.CharField(max_length=200, verbose_name="Nome do Produto")
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código") # Consider making unique_together with equipe
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
        # unique_together = ('equipe', 'codigo') # Enforce code uniqueness per team if needed

    def __str__(self):
        team_name = f" ({self.equipe.nome})" if self.equipe else ""
        return f"{self.codigo} - {self.nome}{team_name}"

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
    # Make sure Cliente FK points to the updated Cliente model
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, verbose_name="Cliente")

    equipe = models.ForeignKey(
        Equipe,
        on_delete=models.SET_NULL, # Keep encomenda if team is deleted? Or CASCADE?
        null=True, # Must allow null if SET_NULL
        blank=False, # Encomenda must belong to a team
        related_name='encomendas',
        verbose_name="Equipe Responsável"
    )

    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação (sistema)")
    data_encomenda = models.DateField(verbose_name="Data", help_text="Data da encomenda (campo do cabeçalho)", default=timezone.now)
    responsavel_criacao = models.CharField(max_length=100, verbose_name="Responsável",
                                         help_text="Responsável pela criação da encomenda")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='criada', verbose_name="Status")
    observacoes = models.TextField(blank=True, verbose_name="Observação",
                                 help_text="Campo 'Observação' do formulário físico")
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

    # calcular_valor_total method remains the same


# --- ItemEncomenda and Entrega Models need adjustment for FKs ---
class ItemEncomenda(models.Model):
    encomenda = models.ForeignKey(Encomenda, related_name='itens', on_delete=models.CASCADE)
    # Ensure Produto and Fornecedor FKs point to the updated models
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

    # save, delete, __str__ methods remain the same


class Entrega(models.Model):
    encomenda = models.OneToOneField(Encomenda, on_delete=models.CASCADE, verbose_name="Encomenda", related_name='entrega')
    # Other fields remain the same
    data_entrega = models.DateField(verbose_name="Data Entrega",
                                  help_text="Campo 'Data Entrega' do formulário físico",
                                  default=timezone.now)
    responsavel_entrega = models.CharField(max_length=100, verbose_name="Responsável Entrega",
                                         help_text="Campo 'Responsável Entrega' do formulário físico",
                                         default="A definir")
    valor_pago_adiantamento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Valor Pago Adiantamento",
        help_text="Campo 'Valor Pago Adiantamento' do formulário físico"
    )
    data_entrega_realizada = models.DateField(null=True, blank=True, verbose_name="Data (Realizada)",
                                            help_text="Data da entrega realizada (seção inferior)")
    hora_entrega = models.TimeField(null=True, blank=True, verbose_name="Hora (Realizada)",
                                  help_text="Hora da entrega (seção inferior)")
    entregue_por = models.CharField(max_length=100, blank=True, verbose_name="Entregue por",
                                  help_text="Campo 'Entregue por' da seção inferior")
    assinatura_cliente = models.BooleanField(default=False, verbose_name="Ass. do Cliente",
                                        help_text="Marcar se o cliente assinou")
    data_prevista = models.DateField(null=True, blank=True, verbose_name="Data Prevista (Controle Interno)")
    data_realizada = models.DateTimeField(null=True, blank=True, verbose_name="Data/Hora Realizada (Controle Interno)")
    observacoes_entrega = models.TextField(blank=True, verbose_name="Observações da Entrega")

    class Meta:
        verbose_name = "Entrega"
        verbose_name_plural = "Entregas"

    # __str__, valor_restante, valor_adiantamento methods remain the same


# --- Auth Models (Usuario, MembroEquipe, ConviteEquipe) remain the same ---
class Usuario(AbstractUser):
    email = models.EmailField(unique=True, verbose_name="Email")
    nome_completo = models.CharField(max_length=255, verbose_name="Nome Completo")
    identificacao = models.CharField(max_length=20, unique=True, verbose_name="Identificação (CPF/CNPJ)")
    cargo = models.CharField(max_length=100, verbose_name="Cargo")
    telefone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")
    ativo = models.BooleanField(default=True, verbose_name="Usuário Ativo")
    token_reset_senha = models.CharField(max_length=100, blank=True, null=True, unique=True, verbose_name="Token de Reset de Senha")
    data_expiracao_token = models.DateTimeField(blank=True, null=True, verbose_name="Data de Expiração do Token")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'nome_completo', 'identificacao', 'cargo']

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ['nome_completo']

    def __str__(self):
        return f"{self.nome_completo} ({self.email})"

    # gerar_token_reset, token_reset_valido, limpar_token_reset methods remain the same

class MembroEquipe(models.Model):
    PAPEL_CHOICES = (
        ('administrador', 'Administrador'),
        ('gerente', 'Gerente'),
        ('membro', 'Membro'),
    )
    equipe = models.ForeignKey(Equipe, on_delete=models.CASCADE, verbose_name="Equipe")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Usuário")
    papel = models.CharField(max_length=20, choices=PAPEL_CHOICES, default='membro', verbose_name="Papel")
    data_adesao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Adesão")
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")

    class Meta:
        verbose_name = "Membro da Equipe"
        verbose_name_plural = "Membros da Equipe"
        unique_together = ('equipe', 'usuario')
        ordering = ['usuario__nome_completo']

    def __str__(self):
        return f"{self.usuario.nome_completo} - {self.equipe.nome} ({self.get_papel_display()})"

class ConviteEquipe(models.Model):
    STATUS_CHOICES = (
        ('pendente', 'Pendente'),
        ('aceito', 'Aceito'),
        ('rejeitado', 'Rejeitado'),
        ('expirado', 'Expirado'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="ID do Convite")
    equipe = models.ForeignKey(Equipe, on_delete=models.CASCADE, related_name='convites', verbose_name="Equipe")
    email = models.EmailField(verbose_name="Email do Convidado")
    papel = models.CharField(max_length=20, choices=MembroEquipe.PAPEL_CHOICES, default='membro', verbose_name="Papel")
    criado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='convites_enviados', verbose_name="Criado por")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente', verbose_name="Status")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    data_expiracao = models.DateTimeField(verbose_name="Data de Expiração")
    data_resposta = models.DateTimeField(blank=True, null=True, verbose_name="Data de Resposta")

    class Meta:
        verbose_name = "Convite de Equipe"
        verbose_name_plural = "Convites de Equipe"
        ordering = ['-data_criacao']

    def __str__(self):
        return f"Convite para {self.email} - {self.equipe.nome}"

    # eh_valido, aceitar, rejeitar methods remain the same