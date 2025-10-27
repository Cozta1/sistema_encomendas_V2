# encomendas/serializers.py

from django.contrib.auth import password_validation # Importar validação de senha
from django.core.exceptions import ValidationError # Para a validação
from rest_framework import serializers
from .models import (
    Usuario, Equipe, MembroEquipe, ConviteEquipe,
    Cliente, Fornecedor, Produto,
    Encomenda, ItemEncomenda, Entrega
)

# --- Serializers para Autenticação e Equipes ---

class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer básico para informações do usuário (somente leitura)."""
    class Meta:
        model = Usuario
        # Exclua campos sensíveis como password, tokens, is_staff, is_superuser
        fields = ['id', 'username', 'email', 'nome_completo', 'cargo', 'telefone', 'identificacao', 'ativo']
        read_only_fields = fields # Tornar todos somente leitura neste serializer

class MembroEquipeSerializer(serializers.ModelSerializer):
    """Serializer para exibir membros da equipe (inclui dados do usuário)."""
    # Exibe informações detalhadas do usuário em vez de apenas o ID
    usuario = UsuarioSerializer(read_only=True)
    # Mostra apenas o ID da equipe (o contexto da equipe geralmente vem da URL)
    equipe_id = serializers.UUIDField(source='equipe.id', read_only=True)

    class Meta:
        model = MembroEquipe
        fields = ['id', 'usuario', 'equipe_id', 'papel', 'data_adesao']
        read_only_fields = ['id', 'usuario', 'equipe_id', 'data_adesao'] # Papel pode ser alterado por outra view

class EquipeSerializer(serializers.ModelSerializer):
    """Serializer para exibir detalhes da equipe, incluindo membros."""
    # Aninha o serializer de MembroEquipe para mostrar a lista de membros
    membros = MembroEquipeSerializer(many=True, read_only=True, source='membroequipe_set') # Usa related_name
    # Exibe informações resumidas do administrador
    administrador_info = UsuarioSerializer(source='administrador', read_only=True)

    class Meta:
        model = Equipe
        fields = ['id', 'nome', 'descricao', 'ativa', 'data_criacao', 'administrador_info', 'membros']
        read_only_fields = ['id', 'data_criacao', 'administrador_info', 'membros'] # Nome e descrição podem ser editáveis

class ConviteEquipeSerializer(serializers.ModelSerializer):
    """Serializer para exibir convites pendentes."""
    # Exibe informações resumidas de quem criou o convite
    criado_por_info = UsuarioSerializer(source='criado_por', read_only=True)
    equipe_nome = serializers.CharField(source='equipe.nome', read_only=True)

    class Meta:
        model = ConviteEquipe
        fields = ['id', 'email', 'papel', 'status', 'data_criacao', 'data_expiracao', 'criado_por_info', 'equipe_nome']
        read_only_fields = fields # Convites geralmente não são editados via API CRUD padrão

# --- Serializers para o Core de Encomendas ---

class ClienteSerializer(serializers.ModelSerializer):
    # Exibe o nome da equipe em vez do ID (somente leitura)
    equipe_nome = serializers.CharField(source='equipe.nome', read_only=True)

    class Meta:
        model = Cliente
        # Inclui todos os campos do modelo, exceto 'equipe' (usamos equipe_nome)
        exclude = ['equipe']
        read_only_fields = ['created_at', 'updated_at', 'equipe_nome']

class FornecedorSerializer(serializers.ModelSerializer):
    equipe_nome = serializers.CharField(source='equipe.nome', read_only=True)

    class Meta:
        model = Fornecedor
        exclude = ['equipe']
        read_only_fields = ['created_at', 'updated_at', 'equipe_nome']

class ProdutoSerializer(serializers.ModelSerializer):
    equipe_nome = serializers.CharField(source='equipe.nome', read_only=True)

    class Meta:
        model = Produto
        exclude = ['equipe']
        read_only_fields = ['created_at', 'updated_at', 'equipe_nome']

class ItemEncomendaSerializer(serializers.ModelSerializer):
    """Serializer para os itens DENTRO de uma encomenda."""
    # Para exibição, mostra nomes em vez de IDs
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)
    fornecedor_nome = serializers.CharField(source='fornecedor.nome', read_only=True)

    # Para criação/atualização, permite enviar apenas os IDs
    produto_id = serializers.PrimaryKeyRelatedField(
        queryset=Produto.objects.all(), source='produto', write_only=True
    )
    fornecedor_id = serializers.PrimaryKeyRelatedField(
        queryset=Fornecedor.objects.all(), source='fornecedor', write_only=True
    )

    class Meta:
        model = ItemEncomenda
        # Exclui 'encomenda' pois será aninhado, inclui campos de leitura e escrita
        fields = [
            'id', 'produto_id', 'fornecedor_id', # Write-only
            'produto_nome', 'fornecedor_nome', # Read-only
            'quantidade', 'preco_cotado', 'valor_total', 'observacoes'
        ]
        read_only_fields = ['id', 'valor_total', 'produto_nome', 'fornecedor_nome'] # Valor total é calculado

    def validate(self, data):
        """Validação extra: Garante que Produto e Fornecedor pertencem à mesma equipe."""
        # Esta validação é importante, mas depende do contexto da Encomenda.
        # Será mais fácil validar isso no serializer da Encomenda ou na view.
        # No entanto, podemos fazer uma verificação básica aqui se tivermos o contexto.
        # Se 'equipe' for passada no contexto do serializer:
        # equipe = self.context.get('equipe')
        # if equipe:
        #     produto = data.get('produto')
        #     fornecedor = data.get('fornecedor')
        #     if produto and produto.equipe != equipe:
        #         raise serializers.ValidationError(f"Produto '{produto.nome}' não pertence à equipe '{equipe.nome}'.")
        #     if fornecedor and fornecedor.equipe != equipe:
        #         raise serializers.ValidationError(f"Fornecedor '{fornecedor.nome}' não pertence à equipe '{equipe.nome}'.")
        return data


class EntregaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entrega
        # Exclui 'encomenda' pois geralmente será um campo relacionado ou aninhado
        exclude = ['encomenda']
        read_only_fields = ['data_realizada'] # Controlado pelo sistema

class EncomendaSerializer(serializers.ModelSerializer):
    """Serializer principal para Encomenda, incluindo itens e entrega."""
    # Aninha o serializer de Itens (permite criar/atualizar itens junto com a encomenda)
    itens = ItemEncomendaSerializer(many=True)
    # Aninha o serializer de Entrega (somente leitura aqui, edição pode ser separada)
    entrega = EntregaSerializer(read_only=True, required=False)

    # Campos de leitura para exibir nomes em vez de IDs
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    equipe_nome = serializers.CharField(source='equipe.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    # Campo de escrita para permitir associar cliente por ID
    cliente_id = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.all(), source='cliente', write_only=True
    )
    # Equipe será definida pela view, não pela API diretamente neste serializer
    equipe_id = serializers.UUIDField(source='equipe.id', read_only=True)

    class Meta:
        model = Encomenda
        # Inclui campos relevantes, aninhados e de leitura/escrita
        fields = [
            'numero_encomenda', 'cliente_id', 'cliente_nome', # Cliente
            'equipe_id', 'equipe_nome', # Equipe
            'data_criacao', 'data_encomenda', 'responsavel_criacao',
            'status', 'status_display', 'observacoes', 'valor_total', 'updated_at',
            'itens', # Itens aninhados
            'entrega' # Entrega aninhada (somente leitura)
        ]
        read_only_fields = [
            'numero_encomenda', 'data_criacao', 'valor_total', 'updated_at',
            'cliente_nome', 'equipe_id', 'equipe_nome', 'status_display', 'entrega'
        ]

    def create(self, validated_data):
        """Cria a Encomenda e seus Itens aninhados."""
        itens_data = validated_data.pop('itens')
        # A equipe deve ser adicionada aqui a partir do contexto passado pela view
        equipe = self.context['equipe']
        cliente = validated_data.get('cliente')

        # Validações de Equipe
        if cliente.equipe != equipe:
            raise serializers.ValidationError(f"Cliente '{cliente.nome}' não pertence à equipe '{equipe.nome}'.")

        encomenda = Encomenda.objects.create(**validated_data, equipe=equipe)
        total_encomenda = Decimal('0.00')

        for item_data in itens_data:
            produto = item_data.get('produto')
            fornecedor = item_data.get('fornecedor')
            if produto.equipe != equipe:
                 raise serializers.ValidationError(f"Produto '{produto.nome}' não pertence à equipe '{equipe.nome}'.")
            if fornecedor.equipe != equipe:
                 raise serializers.ValidationError(f"Fornecedor '{fornecedor.nome}' não pertence à equipe '{equipe.nome}'.")

            quantidade = item_data.get('quantidade', 1)
            preco = item_data.get('preco_cotado', Decimal('0.00'))
            valor_item = quantidade * preco
            ItemEncomenda.objects.create(encomenda=encomenda, valor_total=valor_item, **item_data)
            total_encomenda += valor_item

        encomenda.valor_total = total_encomenda
        encomenda.save()
        return encomenda

    def update(self, instance, validated_data):
        """Atualiza a Encomenda e gerencia os Itens aninhados (criação, atualização, exclusão)."""
        itens_data = validated_data.pop('itens', None)
        # A equipe é fixa na atualização
        equipe = instance.equipe
        cliente = validated_data.get('cliente', instance.cliente)

        # Validação de Cliente (se foi alterado)
        if cliente.equipe != equipe:
            raise serializers.ValidationError(f"Cliente '{cliente.nome}' não pertence à equipe '{equipe.nome}'.")

        # Atualiza campos da Encomenda
        instance.cliente = cliente
        instance.data_encomenda = validated_data.get('data_encomenda', instance.data_encomenda)
        instance.responsavel_criacao = validated_data.get('responsavel_criacao', instance.responsavel_criacao)
        instance.status = validated_data.get('status', instance.status)
        instance.observacoes = validated_data.get('observacoes', instance.observacoes)
        # O valor_total será recalculado

        if itens_data is not None:
            # Gerenciamento de itens: identificar itens a criar, atualizar ou deletar
            item_mapping = {item.id: item for item in instance.itens.all()}
            total_encomenda = Decimal('0.00')

            items_to_create = []
            items_to_update = []

            for item_data in itens_data:
                item_id = item_data.get('id', None)
                produto = item_data.get('produto')
                fornecedor = item_data.get('fornecedor')

                # Validações de Equipe para cada item
                if produto.equipe != equipe:
                     raise serializers.ValidationError(f"Produto '{produto.nome}' não pertence à equipe '{equipe.nome}'.")
                if fornecedor.equipe != equipe:
                     raise serializers.ValidationError(f"Fornecedor '{fornecedor.nome}' não pertence à equipe '{equipe.nome}'.")

                quantidade = item_data.get('quantidade', 1)
                preco = item_data.get('preco_cotado', Decimal('0.00'))
                valor_item = quantidade * preco

                if item_id: # Item existente para atualizar
                    item = item_mapping.pop(item_id, None)
                    if item:
                        item.produto = produto
                        item.fornecedor = fornecedor
                        item.quantidade = quantidade
                        item.preco_cotado = preco
                        item.valor_total = valor_item
                        item.observacoes = item_data.get('observacoes', item.observacoes)
                        items_to_update.append(item)
                        total_encomenda += valor_item
                    # else: Item ID inválido enviado? Ignorar ou levantar erro?
                else: # Novo item para criar
                    # Cria a instância mas não salva ainda (bulk_create depois)
                     new_item = ItemEncomenda(
                         encomenda=instance,
                         produto=produto,
                         fornecedor=fornecedor,
                         quantidade=quantidade,
                         preco_cotado=preco,
                         valor_total=valor_item,
                         observacoes=item_data.get('observacoes', '')
                     )
                     items_to_create.append(new_item)
                     total_encomenda += valor_item

            # Itens que estavam no mapping mas não vieram no request devem ser deletados
            if item_mapping:
                ItemEncomenda.objects.filter(id__in=item_mapping.keys()).delete()

            # Salva atualizações e criações
            if items_to_update:
                ItemEncomenda.objects.bulk_update(items_to_update, ['produto', 'fornecedor', 'quantidade', 'preco_cotado', 'valor_total', 'observacoes'])
            if items_to_create:
                ItemEncomenda.objects.bulk_create(items_to_create)

            instance.valor_total = total_encomenda

        instance.save()
        return instance

    def get_fields(self):
        """Passa o contexto para serializers aninhados."""
        fields = super().get_fields()
        # Garante que o contexto (contendo a equipe) seja passado para o ItemEncomendaSerializer
        if 'itens' in fields and isinstance(fields['itens'], serializers.ListSerializer):
            fields['itens'].child.context.update(self.context)
        return fields
    


class UserRegistrationSerializer(serializers.ModelSerializer):
    # Campo extra para confirmação de senha (não fica no modelo)
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True, label="Confirmar Senha")

    class Meta:
        model = Usuario
        # Campos que esperamos receber da API
        fields = ['email', 'nome_completo', 'identificacao', 'cargo', 'telefone', 'password', 'password2']
        extra_kwargs = {
            'password': {'write_only': True, 'style': {'input_type': 'password'}, 'help_text': password_validation.password_validators_help_text_html()}
        }

    def validate(self, attrs):
        """Validações customizadas."""
        password = attrs.get('password')
        password2 = attrs.get('password2') # Mantenha a leitura aqui

        # 1. Verifica se as senhas coincidem ANTES de remover password2
        if password != password2:
            raise serializers.ValidationError({"password2": "As senhas não coincidem."})

        # --- CORREÇÃO: Criar cópia e remover password2 ANTES de validate_password ---
        temp_user_attrs = attrs.copy()
        temp_user_attrs.pop('password2', None) # Remove password2 da cópia
        temp_user_attrs.pop('password', None) # A senha em si não é necessária no objeto user para validação
        # ------------------------------------------------------------------------

        # 2. Aplica as validações de senha padrão do Django
        try:
            # Passa um usuário temporário criado SEM password2
            password_validation.validate_password(password, user=Usuario(**temp_user_attrs))
        except ValidationError as e:
            # Retorna o erro associado ao campo 'password'
            raise serializers.ValidationError({'password': list(e.messages)})

        # Não precisamos mais remover 'password2' aqui, pois já foi feito na cópia
        # e o 'create' fará o pop final.

        return attrs # Retorna os atributos originais (incluindo password e password2)

    def create(self, validated_data):
        """Cria e retorna um novo usuário."""
        # --- CORREÇÃO: Remover password2 ANTES de criar o usuário ---
        validated_data.pop('password2')
        # -----------------------------------------------------------

        # Extrai a senha para usar set_password
        password = validated_data.pop('password')

        # Define o 'username' como sendo o email (conforme seu modelo Usuario)
        validated_data['username'] = validated_data['email']

        # Cria a instância do usuário SEM a senha e SEM password2
        user = Usuario(**validated_data)

        # Define a senha HASHED corretamente
        user.set_password(password)
        user.save()
        return user