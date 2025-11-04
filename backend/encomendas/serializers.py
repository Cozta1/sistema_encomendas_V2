# encomendas/serializers.py

from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from rest_framework import serializers
from decimal import Decimal # <-- IMPORTAÇÃO ADICIONADA
from .models import (
    Usuario, Equipe, MembroEquipe, ConviteEquipe, # <-- CORRIGIDO DE ConviteEquipe PARA Convite
    Cliente, Fornecedor, Produto,
    Encomenda, ItemEncomenda, Entrega
)

# --- Serializers para o Core de Encomendas (Primeiro) ---
# (Clientes, Fornecedores, Produtos, Itens, Entregas)

class ClienteSerializer(serializers.ModelSerializer):
    equipe_nome = serializers.CharField(source='equipe.nome', read_only=True)

    class Meta:
        model = Cliente
        exclude = ['equipe']
        read_only_fields = ['id', 'created_at', 'updated_at', 'equipe_nome']

class FornecedorSerializer(serializers.ModelSerializer):
    equipe_nome = serializers.CharField(source='equipe.nome', read_only=True)

    class Meta:
        model = Fornecedor
        exclude = ['equipe']
        read_only_fields = ['id', 'created_at', 'updated_at', 'equipe_nome']

class ProdutoSerializer(serializers.ModelSerializer):
    equipe_nome = serializers.CharField(source='equipe.nome', read_only=True)

    class Meta:
        model = Produto
        exclude = ['equipe']
        read_only_fields = ['id', 'created_at', 'updated_at', 'equipe_nome']

class ItemEncomendaSerializer(serializers.ModelSerializer):
    """Serializer para os itens DENTRO de uma encomenda."""
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)
    fornecedor_nome = serializers.CharField(source='fornecedor.nome', read_only=True)

    produto_id = serializers.PrimaryKeyRelatedField(
        queryset=Produto.objects.all(), source='produto', write_only=True
    )
    fornecedor_id = serializers.PrimaryKeyRelatedField(
        queryset=Fornecedor.objects.all(), source='fornecedor', write_only=True
    )

    class Meta:
        model = ItemEncomenda
        fields = [
            'id', 'produto_id', 'fornecedor_id',
            'produto_nome', 'fornecedor_nome',
            'quantidade', 'preco_cotado', 'valor_total', 'observacoes'
        ]
        read_only_fields = ['id', 'valor_total', 'produto_nome', 'fornecedor_nome']

    def validate(self, data):
        """Validação da equipe será feita no EncomendaSerializer."""
        equipe = self.context.get('equipe')
        if equipe:
            produto = data.get('produto')
            fornecedor = data.get('fornecedor')
            
            # Valida se os IDs passados (produto/fornecedor) pertencem à equipe
            if produto and produto.equipe != equipe:
                raise serializers.ValidationError(f"Produto '{produto.nome}' não pertence à equipe ativa.")
            if fornecedor and fornecedor.equipe != equipe:
                raise serializers.ValidationError(f"Fornecedor '{fornecedor.nome}' não pertence à equipe ativa.")
        
        return data


class EntregaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entrega
        exclude = ['encomenda']
        read_only_fields = ['id', 'data_realizada']

class EncomendaSerializer(serializers.ModelSerializer):
    """Serializer principal para Encomenda, incluindo itens e entrega."""
    itens = ItemEncomendaSerializer(many=True)
    entrega = EntregaSerializer(read_only=True, required=False)

    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    equipe_nome = serializers.CharField(source='equipe.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    cliente_id = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.all(), source='cliente', write_only=True
    )
    equipe_id = serializers.UUIDField(source='equipe.id', read_only=True)

    class Meta:
        model = Encomenda
        fields = [
            'id', 'numero_encomenda', 'cliente_id', 'cliente_nome',
            'equipe_id', 'equipe_nome',
            'data_criacao', 'data_encomenda', 'responsavel_criacao',
            'status', 'status_display', 'observacoes', 'valor_total', 'updated_at',
            'itens', 'entrega'
        ]
        read_only_fields = [
            'id', 'numero_encomenda', 'data_criacao', 'valor_total', 'updated_at',
            'cliente_nome', 'equipe_id', 'equipe_nome', 'status_display', 'entrega'
        ]

    def get_fields(self):
        """Passa o contexto (equipe) para serializers aninhados (ItemEncomendaSerializer)."""
        fields = super().get_fields()
        if 'itens' in fields and isinstance(fields['itens'], serializers.ListSerializer):
            fields['itens'].child.context.update(self.context)
        return fields

    def _validate_contexto(self, validated_data):
        """Valida cliente e itens contra a equipe (do contexto)."""
        equipe = self.context.get('equipe')
        if not equipe:
             raise serializers.ValidationError("Contexto 'equipe' não fornecido para o serializer.")

        cliente = validated_data.get('cliente')
        if cliente and cliente.equipe != equipe:
            raise serializers.ValidationError(f"Cliente '{cliente.nome}' não pertence à equipe '{equipe.nome}'.")
        
        return equipe

    def create(self, validated_data):
        """Cria a Encomenda e seus Itens aninhados."""
        itens_data = validated_data.pop('itens')
        equipe = self._validate_contexto(validated_data) # <-- CORREÇÃO (self. e _)
        
        encomenda = Encomenda.objects.create(**validated_data, equipe=equipe)
        total_encomenda = Decimal('0.00')

        # Validação de itens (feita no serializer aninhado, mas reforçada aqui)
        for item_data in itens_data:
            quantidade = item_data.get('quantidade', 1)
            preco = item_data.get('preco_cotado', Decimal('0.00'))
            valor_item = quantidade * preco
            ItemEncomenda.objects.create(encomenda=encomenda, valor_total=valor_item, **item_data)
            total_encomenda += valor_item

        encomenda.valor_total = total_encomenda
        encomenda.save()
        return encomenda

    def update(self, instance, validated_data):
        """Atualiza a Encomenda e gerencia os Itens aninhados."""
        itens_data = validated_data.pop('itens', None)
        # No update, a equipe é a da instância e não pode ser mudada
        equipe = instance.equipe
        # Passa a equipe para o contexto do serializer de itens
        self.context['equipe'] = equipe
        
        # Valida o cliente (se for alterado)
        cliente = validated_data.get('cliente', instance.cliente)
        if cliente.equipe != equipe:
            raise serializers.ValidationError(f"Cliente '{cliente.nome}' não pertence à equipe '{equipe.nome}'.")

        # Atualiza campos da Encomenda
        instance.cliente = cliente
        instance.data_encomenda = validated_data.get('data_encomenda', instance.data_encomenda)
        instance.responsavel_criacao = validated_data.get('responsavel_criacao', instance.responsavel_criacao)
        instance.status = validated_data.get('status', instance.status)
        instance.observacoes = validated_data.get('observacoes', instance.observacoes)

        if itens_data is not None:
            item_mapping = {item.id: item for item in instance.itens.all()}
            total_encomenda = Decimal('0.00')
            items_to_create = []
            items_to_update = []

            for item_data in itens_data:
                item_id = item_data.get('id', None)
                
                # Validação de equipe para produto/fornecedor (feita no validate do item serializer)
                
                quantidade = item_data.get('quantidade', 1)
                preco = item_data.get('preco_cotado', Decimal('0.00'))
                valor_item = quantidade * preco

                if item_id:
                    item = item_mapping.pop(item_id, None)
                    if item:
                        item.produto = item_data.get('produto', item.produto)
                        item.fornecedor = item_data.get('fornecedor', item.fornecedor)
                        item.quantidade = quantidade
                        item.preco_cotado = preco
                        item.valor_total = valor_item
                        item.observacoes = item_data.get('observacoes', item.observacoes)
                        items_to_update.append(item)
                        total_encomenda += valor_item
                else:
                     new_item = ItemEncomenda(
                         encomenda=instance,
                         produto=item_data.get('produto'),
                         fornecedor=item_data.get('fornecedor'),
                         quantidade=quantidade,
                         preco_cotado=preco,
                         valor_total=valor_item,
                         observacoes=item_data.get('observacoes', '')
                     )
                     items_to_create.append(new_item)
                     total_encomenda += valor_item

            if item_mapping:
                ItemEncomenda.objects.filter(id__in=item_mapping.keys()).delete()
            if items_to_update:
                ItemEncomenda.objects.bulk_update(items_to_update, ['produto', 'fornecedor', 'quantidade', 'preco_cotado', 'valor_total', 'observacoes'])
            if items_to_create:
                ItemEncomenda.objects.bulk_create(items_to_create)

            instance.valor_total = total_encomenda

        instance.save()
        return instance

# --- Serializers para Autenticação e Equipes ---
# (Definidos DEPOIS dos principais, pois são usados neles)

class UserSerializer(serializers.ModelSerializer): # Nome corrigido para UserSerializer
    """Serializer básico para informações do usuário (somente leitura)."""
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'nome_completo', 'cargo', 'telefone', 'identificacao', 'ativo', 'equipe_ativa_id']
        read_only_fields = fields

class MembroEquipeSerializer(serializers.ModelSerializer):
    """Serializer para exibir membros da equipe (inclui dados do usuário)."""
    usuario = UserSerializer(read_only=True) 
    equipe_id = serializers.UUIDField(source='equipe.id', read_only=True)

    class Meta:
        model = MembroEquipe
        fields = ['id', 'usuario', 'equipe_id', 'papel', 'data_adesao']
        read_only_fields = ['id', 'usuario', 'equipe_id', 'data_adesao']

class EquipeSerializer(serializers.ModelSerializer):
    """Serializer para exibir detalhes da equipe, incluindo membros."""
    membros = MembroEquipeSerializer(many=True, read_only=True, source='membroequipe_set') 
    administrador = UserSerializer(read_only=True) # Fonte corrigida

    class Meta:
        model = Equipe
        fields = ['id', 'nome', 'descricao', 'ativa', 'data_criacao', 'administrador', 'membros']
        read_only_fields = ['id', 'data_criacao', 'administrador', 'membros', 'ativa']

    def create(self, validated_data):
        # O administrador é definido na view (perform_create)
        administrador = self.context['request'].user
        equipe = Equipe.objects.create(administrador=administrador, **validated_data)
        # Adiciona o admin como membro
        equipe.adicionar_membro(administrador, papel='administrador')
        # Define como equipe ativa
        administrador.equipe_ativa = equipe
        administrador.save()
        return equipe

# --- SERIALIZER DE CONVITE (NOVO/CORRIGIDO) ---
# (Colocado AQUI, depois de UserSerializer e EquipeSerializer)

class ConviteEquipeSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Convite (para listagem, criação, etc. pelo ViewSet).
    """
    convidado_por = UserSerializer(read_only=True)
    equipe_nome = serializers.CharField(source='equipe.nome', read_only=True)

    class Meta:
        model = ConviteEquipe # <-- CORRIGIDO para Convite
        fields = [
            'id', 
            'equipe', 
            'equipe_nome',
            'email', 
            'papel', 
            'status', 
            'convidado_por', 
            'criado_em', 
            'atualizado_em'
        ]
        read_only_fields = ['equipe', 'convidado_por', 'status', 'criado_em', 'atualizado_em']

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("O email é obrigatório.")
        return value

    def validate_papel(self, value):
        if value not in ['leitor', 'editor', 'administrador']:
            raise serializers.ValidationError("Papel inválido. Escolha 'leitor', 'editor' ou 'administrador'.")
        return value

# --- Outros Serializers de Autenticação (Mantidos do arquivo anterior) ---

class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer para solicitar redefinição de senha."""
    email = serializers.EmailField()

    def validate_email(self, value):
        if not Usuario.objects.filter(email=value, ativo=True).exists():
            raise serializers.ValidationError("Nenhum usuário ativo encontrado com este email.")
        return value

class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer para confirmar a redefinição de senha."""
    token = serializers.CharField(write_only=True)
    uidb64 = serializers.CharField(write_only=True)
    nova_senha = serializers.CharField(write_only=True, style={'input_type': 'password'}, validators=[password_validation.validate_password])
    confirmar_nova_senha = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        if attrs['nova_senha'] != attrs['confirmar_nova_senha']:
            raise serializers.ValidationError({"confirmar_nova_senha": "As senhas não coincidem."})
        return attrs

class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para alterar a senha (usuário logado)."""
    senha_atual = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    nova_senha = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'}, validators=[password_validation.validate_password])
    confirmar_nova_senha = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        if attrs['nova_senha'] != attrs['confirmar_nova_senha']:
            raise serializers.ValidationError({"confirmar_nova_senha": "As senhas não coincidem."})
        return attrs

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer para registro de novos usuários."""
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}, validators=[password_validation.validate_password])
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}, label="Confirmar Senha")

    class Meta:
        model = Usuario
        fields = ['email', 'username', 'nome_completo', 'password', 'password2', 'cargo', 'telefone', 'identificacao']
        extra_kwargs = {
            'username': {'required': False} # Username será o email
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password2": "As senhas não coincidem."})
        
        if 'username' not in attrs or not attrs['username']:
            attrs['username'] = attrs['email']
            
        if Usuario.objects.filter(email=attrs['email']).exists():
             raise serializers.ValidationError({"email": "Este email já está em uso."})
        if Usuario.objects.filter(username=attrs['username']).exists():
             raise serializers.ValidationError({"username": "Este username já está em uso."})
             
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        
        user = Usuario(**validated_data)
        user.set_password(password)
        user.save()
        return user

# class ConvidarMembroSerializer(serializers.Serializer):
#     """Serializer simples para a view 'convidar_membro'."""
#     email = serializers.EmailField()
#     papel = serializers.ChoiceField(choices=MembroEquipe.PAPEIS_ESCOLHAS, default='leitor')

#     def validate_email(self, value):
#         # A lógica de validação (se já é membro, se já foi convidado)
#         # será tratada na view (views_auth.py), pois depende da equipe ativa.
#         return value

# class AceitarConviteSerializer(serializers.Serializer):
#     """Serializer simples para a view 'aceitar_convite'."""
#     token = serializers.CharField()