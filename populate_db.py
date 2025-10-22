#!/usr/bin/env python3
"""
Script para popular o banco de dados com dados de exemplo,
incluindo usuários, equipes e associação de encomendas a equipes.
"""
import os
import sys
import django
from decimal import Decimal
from datetime import date, datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_encomendas.settings')
django.setup()

# Importar modelos após o setup
from django.contrib.auth import get_user_model
# <<<--- ADICIONAR ESTAS IMPORTAÇÕES --->>>
from django.db.models import Sum
from django.db.models.functions import Coalesce
# <<<------------------------------------>>>
from encomendas.models import Cliente, Fornecedor, Produto, Encomenda, ItemEncomenda, Entrega, Equipe, MembroEquipe

# Obter o modelo de usuário customizado
Usuario = get_user_model()

def criar_dados_exemplo():
    print("🧹 Limpando dados antigos...")
    # Limpar dados para evitar duplicatas (opcional, mas recomendado para testes)
    ItemEncomenda.objects.all().delete()
    Entrega.objects.all().delete()
    Encomenda.objects.all().delete()
    Produto.objects.all().delete()
    Fornecedor.objects.all().delete()
    Cliente.objects.all().delete()
    MembroEquipe.objects.all().delete()
    Equipe.objects.all().delete()
    # Excluir usuários comuns (manter superusuários se houver)
    Usuario.objects.filter(is_superuser=False).delete()
    print("✅ Dados antigos limpos.")

    print("\n👤 Criando usuários de exemplo...")
    # Criar usuários de exemplo (Senha: 'senha123' para todos)
    # Senha deve ser definida usando set_password
    usuarios_data = [
        {
            'username': 'joao.farmaceutico@benfica.com',
            'email': 'joao.farmaceutico@benfica.com',
            'nome_completo': 'João Farmacêutico',
            'identificacao': '11122233344',
            'cargo': 'Farmacêutico Responsável',
            'password': 'senha123',
            'is_staff': False, # Não é admin do Django
        },
        {
            'username': 'maria.atendente@benfica.com',
            'email': 'maria.atendente@benfica.com',
            'nome_completo': 'Maria Atendente',
            'identificacao': '55566677788',
            'cargo': 'Atendente',
            'password': 'senha123',
            'is_staff': False,
        },
        {
            'username': 'carlos.gerente@benfica.com',
            'email': 'carlos.gerente@benfica.com',
            'nome_completo': 'Carlos Gerente',
            'identificacao': '99988877766',
            'cargo': 'Gerente de Loja',
            'password': 'senha123',
            'is_staff': False,
        }
    ]

    usuarios = []
    for data in usuarios_data:
        # Usar create_user para lidar com a senha corretamente
        try:
            usuario = Usuario.objects.create_user(
                username=data['username'],
                email=data['email'],
                password=data['password'],
                nome_completo=data['nome_completo'],
                identificacao=data['identificacao'],
                cargo=data['cargo'],
                is_staff=data.get('is_staff', False)
            )
            usuarios.append(usuario)
            print(f"   -> Usuário criado: {usuario.email}")
        except Exception as e:
            print(f"   ⚠️ Erro ao criar usuário {data['email']}: {e}. Pode já existir.")
            # Tentar buscar o usuário existente
            usuario_existente = Usuario.objects.filter(email=data['email']).first()
            if usuario_existente:
                usuarios.append(usuario_existente)
            else:
                print(f"   ❌ Não foi possível criar ou encontrar o usuário {data['email']}.")


    print("\n👥 Criando equipes de exemplo...")
    # Criar equipes
    equipes = []
    if len(usuarios) >= 2: # Precisa de pelo menos 2 usuários para admin e membro
        equipe_centro, created_centro = Equipe.objects.get_or_create(
            nome='Equipe Centro',
            defaults={
                'descricao': 'Equipe responsável pelas encomendas da região central.',
                'administrador': usuarios[0] # João será o admin
            }
        )
        equipes.append(equipe_centro)
        if created_centro: print(f"   -> Equipe criada: {equipe_centro.nome}")

        equipe_bairros, created_bairros = Equipe.objects.get_or_create(
            nome='Equipe Bairros',
            defaults={
                'descricao': 'Equipe focada nas entregas dos bairros adjacentes.',
                'administrador': usuarios[2] # Carlos será o admin
            }
        )
        equipes.append(equipe_bairros)
        if created_bairros: print(f"   -> Equipe criada: {equipe_bairros.nome}")

        print("\n🤝 Adicionando membros às equipes...")
        # Adicionar membros (incluindo o administrador)
        # Equipe Centro
        equipe_centro.adicionar_membro(usuarios[0], papel='administrador')
        equipe_centro.adicionar_membro(usuarios[1], papel='membro') # Maria na equipe Centro
        print(f"   -> Membros adicionados à Equipe Centro.")

        # Equipe Bairros
        equipe_bairros.adicionar_membro(usuarios[2], papel='administrador')
        # João também participa da Equipe Bairros como gerente
        equipe_bairros.adicionar_membro(usuarios[0], papel='gerente')
        print(f"   -> Membros adicionados à Equipe Bairros.")
    else:
        print("   ⚠️ Não há usuários suficientes para criar equipes e adicionar membros.")


    print("\n👤 Criando clientes...")
    # Criar clientes
    clientes_data = [
        {'nome': 'Maria Silva Santos', 'codigo': 'CLI001', 'endereco': 'Rua das Flores, 123, Apt 201', 'bairro': 'Centro', 'referencia': 'Próximo ao Banco do Brasil', 'telefone': '(32) 99999-1234'},
        {'nome': 'João Carlos Oliveira', 'codigo': 'CLI002', 'endereco': 'Av. Presidente Vargas, 456', 'bairro': 'São Mateus', 'referencia': 'Em frente à padaria', 'telefone': '(32) 98888-5678'},
        {'nome': 'Ana Paula Costa', 'codigo': 'CLI003', 'endereco': 'Rua São João, 789', 'bairro': 'Benfica', 'referencia': 'Casa azul com portão branco', 'telefone': '(32) 97777-9012'},
        {'nome': 'Carlos Eduardo Mendes', 'codigo': 'CLI004', 'endereco': 'Rua Marechal Deodoro, 321', 'bairro': 'Granbery', 'referencia': 'Próximo ao supermercado', 'telefone': '(32) 96666-3456'}
    ]
    clientes = []
    for data in clientes_data:
        cliente, created = Cliente.objects.get_or_create(codigo=data['codigo'], defaults=data)
        clientes.append(cliente)
        if created: print(f"   -> Cliente criado: {cliente.nome}")

    print("\n🚚 Criando fornecedores...")
    # Criar fornecedores
    fornecedores_data = [
        {'nome': 'Distribuidora Farmacêutica ABC', 'codigo': 'FOR001', 'contato': 'Roberto Silva', 'telefone': '(11) 3333-1111', 'email': 'vendas@abc.com.br'},
        {'nome': 'Laboratório XYZ Ltda', 'codigo': 'FOR002', 'contato': 'Fernanda Costa', 'telefone': '(21) 4444-2222', 'email': 'comercial@xyz.com.br'},
        {'nome': 'Medicamentos Nacional', 'codigo': 'FOR003', 'contato': 'Paulo Santos', 'telefone': '(31) 5555-3333', 'email': 'pedidos@nacional.com.br'}
    ]
    fornecedores = []
    for data in fornecedores_data:
        fornecedor, created = Fornecedor.objects.get_or_create(codigo=data['codigo'], defaults=data)
        fornecedores.append(fornecedor)
        if created: print(f"   -> Fornecedor criado: {fornecedor.nome}")

    print("\n💊 Criando produtos...")
    # Criar produtos
    produtos_data = [
        {'nome': 'Dipirona 500mg - Caixa com 20 comprimidos', 'codigo': 'MED001', 'descricao': 'Analgésico e antitérmico', 'preco_base': Decimal('12.50'), 'categoria': 'Analgésicos'},
        {'nome': 'Paracetamol 750mg - Caixa com 10 comprimidos', 'codigo': 'MED002', 'descricao': 'Analgésico e antitérmico', 'preco_base': Decimal('8.90'), 'categoria': 'Analgésicos'},
        {'nome': 'Omeprazol 20mg - Caixa com 14 cápsulas', 'codigo': 'MED003', 'descricao': 'Inibidor da bomba de prótons', 'preco_base': Decimal('25.80'), 'categoria': 'Gastroenterologia'},
        {'nome': 'Losartana 50mg - Caixa com 30 comprimidos', 'codigo': 'MED004', 'descricao': 'Anti-hipertensivo', 'preco_base': Decimal('18.70'), 'categoria': 'Cardiovascular'},
        {'nome': 'Vitamina D3 2000UI - Frasco com 60 cápsulas', 'codigo': 'VIT001', 'descricao': 'Suplemento vitamínico', 'preco_base': Decimal('35.90'), 'categoria': 'Vitaminas'},
        {'nome': 'Protetor Solar FPS 60 - 120ml', 'codigo': 'COS001', 'descricao': 'Proteção solar facial e corporal', 'preco_base': Decimal('42.50'), 'categoria': 'Cosméticos'}
    ]
    produtos = []
    for data in produtos_data:
        produto, created = Produto.objects.get_or_create(codigo=data['codigo'], defaults=data)
        produtos.append(produto)
        if created: print(f"   -> Produto criado: {produto.nome}")

    print("\n📋 Criando encomendas e associando a equipes...")
    # Criar encomendas, associando a equipes e responsáveis específicos
    encomendas = []
    if equipes and len(usuarios) >= 3: # Certifica que temos equipes e usuários
        encomenda1 = Encomenda.objects.create(
            cliente=clientes[0],
            equipe=equipes[0], # Associada à Equipe Centro
            responsavel_criacao=usuarios[0].nome_completo, # João criou
            status='criada',
            observacoes='Cliente solicitou entrega urgente'
        )
        encomendas.append(encomenda1)
        print(f"   -> Encomenda #{encomenda1.numero_encomenda} criada (Equipe: {encomenda1.equipe.nome})")

        encomenda2 = Encomenda.objects.create(
            cliente=clientes[1],
            equipe=equipes[0], # Associada à Equipe Centro
            responsavel_criacao=usuarios[1].nome_completo, # Maria criou
            status='cotacao',
            observacoes='Verificar disponibilidade no estoque'
        )
        encomendas.append(encomenda2)
        print(f"   -> Encomenda #{encomenda2.numero_encomenda} criada (Equipe: {encomenda2.equipe.nome})")

        encomenda3 = Encomenda.objects.create(
            cliente=clientes[2],
            equipe=equipes[1], # Associada à Equipe Bairros
            responsavel_criacao=usuarios[0].nome_completo, # João criou (ele é gerente aqui)
            status='aprovada',
            observacoes='Pagamento confirmado via PIX'
        )
        encomendas.append(encomenda3)
        print(f"   -> Encomenda #{encomenda3.numero_encomenda} criada (Equipe: {encomenda3.equipe.nome})")

        encomenda4 = Encomenda.objects.create(
            cliente=clientes[3],
            equipe=equipes[1], # Associada à Equipe Bairros
            responsavel_criacao=usuarios[2].nome_completo, # Carlos criou
            status='entregue',
            observacoes='Entrega realizada com sucesso'
        )
        encomendas.append(encomenda4)
        print(f"   -> Encomenda #{encomenda4.numero_encomenda} criada (Equipe: {encomenda4.equipe.nome})")

    else:
        print("   ⚠️ Não foi possível criar encomendas por falta de equipes ou usuários.")

    print("\n📦 Criando itens das encomendas...")
    # Criar itens das encomendas (verifica se encomendas foram criadas)
    if len(encomendas) == 4:
        itens_data = [
            {'encomenda': encomendas[0], 'produto': produtos[0], 'fornecedor': fornecedores[0], 'quantidade': 2, 'preco_cotado': Decimal('12.00')},
            {'encomenda': encomendas[0], 'produto': produtos[2], 'fornecedor': fornecedores[1], 'quantidade': 1, 'preco_cotado': Decimal('24.90')},
            {'encomenda': encomendas[1], 'produto': produtos[1], 'fornecedor': fornecedores[0], 'quantidade': 3, 'preco_cotado': Decimal('8.50')},
            {'encomenda': encomendas[1], 'produto': produtos[4], 'fornecedor': fornecedores[2], 'quantidade': 1, 'preco_cotado': Decimal('34.90')},
            {'encomenda': encomendas[2], 'produto': produtos[3], 'fornecedor': fornecedores[1], 'quantidade': 2, 'preco_cotado': Decimal('18.00')},
            {'encomenda': encomendas[2], 'produto': produtos[5], 'fornecedor': fornecedores[2], 'quantidade': 1, 'preco_cotado': Decimal('40.00')},
            {'encomenda': encomendas[3], 'produto': produtos[0], 'fornecedor': fornecedores[0], 'quantidade': 1, 'preco_cotado': Decimal('12.50')}
        ]
        itens_criados = []
        for data in itens_data:
            item = ItemEncomenda.objects.create(**data)
            itens_criados.append(item)
            # A função save do ItemEncomenda já calcula o valor_total do item
            print(f"   -> Item criado: {item.produto.nome} (Enc: #{item.encomenda.numero_encomenda})")

        print("\n💰 Recalculando valores totais das encomendas...")
        # Recalcular valores totais das encomendas após adicionar todos os itens
        total_itens = 0
        for encomenda in Encomenda.objects.all(): # Recalcular para todas
            # <<<--- LINHA CORRIGIDA COM AS IMPORTAÇÕES --->>>
            soma_itens = ItemEncomenda.objects.filter(encomenda=encomenda).aggregate(
                total=Coalesce(Sum('valor_total'), Decimal('0.00'))
            )['total']
            # <<<-------------------------------------------->>>
            if encomenda.valor_total != soma_itens:
                encomenda.valor_total = soma_itens
                encomenda.save(update_fields=['valor_total'])
                print(f"   -> Valor total da encomenda #{encomenda.numero_encomenda} atualizado para: R$ {encomenda.valor_total}")
            total_itens += ItemEncomenda.objects.filter(encomenda=encomenda).count()


        print("\n🚚 Criando entregas...")
        # Criar entregas
        entregas_data = [
            {'encomenda': encomendas[2], 'data_entrega': date.today() + timedelta(days=1), 'responsavel_entrega': 'Entregador Bairros', 'valor_pago_adiantamento': Decimal('50.00'), 'data_prevista': date.today() + timedelta(days=1)},
            {'encomenda': encomendas[3], 'data_entrega': date.today() - timedelta(days=1), 'responsavel_entrega': 'Entregador Centro', 'valor_pago_adiantamento': Decimal('10.00'), 'data_entrega_realizada': date.today() - timedelta(days=1), 'hora_entrega': datetime.now().time(), 'entregue_por': 'José Silva', 'assinatura_cliente': True, 'data_prevista': date.today() - timedelta(days=1), 'data_realizada': datetime.now() - timedelta(days=1)}
        ]
        entregas_criadas = []
        for data in entregas_data:
            entrega = Entrega.objects.create(**data)
            entregas_criadas.append(entrega)
            print(f"   -> Entrega criada para encomenda #{entrega.encomenda.numero_encomenda}")

        print("\n\n✅ Dados de exemplo criados com sucesso!")
        print(f"   -> {len(usuarios)} usuários")
        print(f"   -> {len(equipes)} equipes")
        print(f"   -> {len(clientes)} clientes")
        print(f"   -> {len(fornecedores)} fornecedores")
        print(f"   -> {len(produtos)} produtos")
        print(f"   -> {len(encomendas)} encomendas")
        print(f"   -> {total_itens} itens de encomenda")
        print(f"   -> {len(entregas_criadas)} entregas")
        print("\n   Logins de exemplo (senha 'senha123'):")
        for u in usuarios:
            print(f"      - {u.email}")

    else:
        print("\n⚠️ Processo interrompido pois não foi possível criar as encomendas.")


if __name__ == '__main__':
    criar_dados_exemplo()