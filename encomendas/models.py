from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal

# Imports moved from models_auth.py
from django.contrib.auth.models import AbstractUser
import uuid

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
        total = sum(item.valor_total for item in self.itens.all())
        self.valor_total = total
        self.save()
        return total


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
        self.valor_total = self.quantidade * self.preco_cotado
        super().save(*args, **kwargs)
        # Atualiza o valor total da encomenda
        self.encomenda.calcular_valor_total()

    def __str__(self):
        return f"{self.produto.nome} - Qtd: {self.quantidade}"


class Entrega(models.Model):
    encomenda = models.OneToOneField(Encomenda, on_delete=models.CASCADE, verbose_name="Encomenda")

    # Campos de programação da entrega (seção superior do formulário)
    data_entrega = models.DateField(verbose_name="Data Entrega",
                                  help_text="Campo 'Data Entrega' do formulário físico",
                                  default=timezone.now)
    responsavel_entrega = models.CharField(max_length=100, verbose_name="Responsável Entrega",
                                         help_text="Campo 'Responsável Entrega' do formulário físico",
                                         default="A definir")

    # Campos de pagamento
    valor_pago_adiantamento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Valor Pago Adiantamento",
        help_text="Campo 'Valor Pago Adiantamento' do formulário físico"
    )

    # Campos da seção inferior (caixa destacada)
    data_entrega_realizada = models.DateField(null=True, blank=True, verbose_name="Data",
                                            help_text="Data da entrega realizada (seção inferior)")
    hora_entrega = models.TimeField(null=True, blank=True, verbose_name="Hora",
                                  help_text="Hora da entrega (seção inferior)")
    entregue_por = models.CharField(max_length=100, blank=True, verbose_name="Entregue por",
                                  help_text="Campo 'Entregue por' da seção inferior")

    # Campo de assinatura
    assinatura_cliente = models.TextField(blank=True, verbose_name="Ass. do Cliente",
                                        help_text="Campo para assinatura do cliente")

    # Campos adicionais para controle interno
    data_prevista = models.DateField(null=True, blank=True, verbose_name="Data Prevista (controle)")
    data_realizada = models.DateTimeField(null=True, blank=True, verbose_name="Data/Hora Realizada (controle)")
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

    @property
    def valor_adiantamento(self):
        """Compatibilidade com templates existentes"""
        return self.valor_pago_adiantamento

# --- Models moved from models_auth.py ---

class Usuario(AbstractUser):
    """Modelo de usuário customizado com campos adicionais"""

    # Sobrescrever campos padrão
    email = models.EmailField(unique=True, verbose_name="Email")

    # Campos adicionais
    nome_completo = models.CharField(
        max_length=255,
        verbose_name="Nome Completo"
    )
    identificacao = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Identificação (CPF/CNPJ)"
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
        verbose_name="Usuário Ativo"
    )

    # Campos para redefinição de senha
    token_reset_senha = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        verbose_name="Token de Reset de Senha"
    )
    data_expiracao_token = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Data de Expiração do Token"
    )

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ['nome_completo']

    def __str__(self):
        return f"{self.nome_completo} ({self.email})"

    def gerar_token_reset(self):
        """Gera um token único para redefinição de senha"""
        self.token_reset_senha = str(uuid.uuid4())
        self.data_expiracao_token = timezone.now() + timezone.timedelta(hours=24)
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
        Usuario,
        on_delete=models.CASCADE,
        related_name='equipes_administradas',
        verbose_name="Administrador"
    )
    membros = models.ManyToManyField(
        Usuario,
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

    def eh_administrador(self, usuario):
        """Verifica se um usuário é administrador da equipe"""
        return self.administrador == usuario

    def eh_membro(self, usuario):
        """Verifica se um usuário é membro da equipe"""
        return self.membros.filter(id=usuario.id).exists()


class MembroEquipe(models.Model):
    """Modelo de relacionamento entre usuários e equipes"""

    PAPEL_CHOICES = (
        ('administrador', 'Administrador'),
        ('gerente', 'Gerente'),
        ('membro', 'Membro'),
    )

    equipe = models.ForeignKey(
        Equipe,
        on_delete=models.CASCADE,
        verbose_name="Equipe"
    )
    usuario = models.ForeignKey(
        Usuario,
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
        return f"{self.usuario.nome_completo} - {self.equipe.nome} ({self.papel})"


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
        choices=MembroEquipe.PAPEL_CHOICES,
        default='membro',
        verbose_name="Papel"
    )
    criado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
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
        verbose_name="Data de Expiração"
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
        if not self.eh_valido():
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
        self.status = 'rejeitado'
        self.data_resposta = timezone.now()
        self.save()