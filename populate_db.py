#!/usr/bin/env python3
"""
Script para popular o banco de dados com dados de exemplo
"""
import os
import sys
import django
from decimal import Decimal
from datetime import date, datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_encomendas.settings')
django.setup()

from encomendas.models import Cliente, Fornecedor, Produto, Encomenda, ItemEncomenda, Entrega

def criar_dados_exemplo():
    print("Criando dados de exemplo...")
    
    # Criar clientes
    clientes_data = [
        {
            'nome': 'Maria Silva Santos',
            'codigo': 'CLI001',
            'endereco': 'Rua das Flores, 123, Apt 201',
            'bairro': 'Centro',
            'referencia': 'Próximo ao Banco do Brasil',
            'telefone': '(32) 99999-1234'
        },
        {
            'nome': 'João Carlos Oliveira',
            'codigo': 'CLI002',
            'endereco': 'Av. Presidente Vargas, 456',
            'bairro': 'São Mateus',
            'referencia': 'Em frente à padaria',
            'telefone': '(32) 98888-5678'
        },
        {
            'nome': 'Ana Paula Costa',
            'codigo': 'CLI003',
            'endereco': 'Rua São João, 789',
            'bairro': 'Benfica',
            'referencia': 'Casa azul com portão branco',
            'telefone': '(32) 97777-9012'
        },
        {
            'nome': 'Carlos Eduardo Mendes',
            'codigo': 'CLI004',
            'endereco': 'Rua Marechal Deodoro, 321',
            'bairro': 'Granbery',
            'referencia': 'Próximo ao supermercado',
            'telefone': '(32) 96666-3456'
        }
    ]
    
    clientes = []
    for data in clientes_data:
        cliente, created = Cliente.objects.get_or_create(
            codigo=data['codigo'],
            defaults=data
        )
        clientes.append(cliente)
        if created:
            print(f"Cliente criado: {cliente.nome}")
    
    # Criar fornecedores
    fornecedores_data = [
        {
            'nome': 'Distribuidora Farmacêutica ABC',
            'codigo': 'FOR001',
            'contato': 'Roberto Silva',
            'telefone': '(11) 3333-1111',
            'email': 'vendas@abc.com.br'
        },
        {
            'nome': 'Laboratório XYZ Ltda',
            'codigo': 'FOR002',
            'contato': 'Fernanda Costa',
            'telefone': '(21) 4444-2222',
            'email': 'comercial@xyz.com.br'
        },
        {
            'nome': 'Medicamentos Nacional',
            'codigo': 'FOR003',
            'contato': 'Paulo Santos',
            'telefone': '(31) 5555-3333',
            'email': 'pedidos@nacional.com.br'
        }
    ]
    
    fornecedores = []
    for data in fornecedores_data:
        fornecedor, created = Fornecedor.objects.get_or_create(
            codigo=data['codigo'],
            defaults=data
        )
        fornecedores.append(fornecedor)
        if created:
            print(f"Fornecedor criado: {fornecedor.nome}")
    
    # Criar produtos
    produtos_data = [
        {
            'nome': 'Dipirona 500mg - Caixa com 20 comprimidos',
            'codigo': 'MED001',
            'descricao': 'Analgésico e antitérmico',
            'preco_base': Decimal('12.50'),
            'categoria': 'Analgésicos'
        },
        {
            'nome': 'Paracetamol 750mg - Caixa com 10 comprimidos',
            'codigo': 'MED002',
            'descricao': 'Analgésico e antitérmico',
            'preco_base': Decimal('8.90'),
            'categoria': 'Analgésicos'
        },
        {
            'nome': 'Omeprazol 20mg - Caixa com 14 cápsulas',
            'codigo': 'MED003',
            'descricao': 'Inibidor da bomba de prótons',
            'preco_base': Decimal('25.80'),
            'categoria': 'Gastroenterologia'
        },
        {
            'nome': 'Losartana 50mg - Caixa com 30 comprimidos',
            'codigo': 'MED004',
            'descricao': 'Anti-hipertensivo',
            'preco_base': Decimal('18.70'),
            'categoria': 'Cardiovascular'
        },
        {
            'nome': 'Vitamina D3 2000UI - Frasco com 60 cápsulas',
            'codigo': 'VIT001',
            'descricao': 'Suplemento vitamínico',
            'preco_base': Decimal('35.90'),
            'categoria': 'Vitaminas'
        },
        {
            'nome': 'Protetor Solar FPS 60 - 120ml',
            'codigo': 'COS001',
            'descricao': 'Proteção solar facial e corporal',
            'preco_base': Decimal('42.50'),
            'categoria': 'Cosméticos'
        }
    ]
    
    produtos = []
    for data in produtos_data:
        produto, created = Produto.objects.get_or_create(
            codigo=data['codigo'],
            defaults=data
        )
        produtos.append(produto)
        if created:
            print(f"Produto criado: {produto.nome}")
    
    # Criar encomendas
    encomendas_data = [
        {
            'cliente': clientes[0],
            'responsavel_criacao': 'Farmacêutico João',
            'status': 'criada',
            'observacoes': 'Cliente solicitou entrega urgente'
        },
        {
            'cliente': clientes[1],
            'responsavel_criacao': 'Atendente Maria',
            'status': 'cotacao',
            'observacoes': 'Verificar disponibilidade no estoque'
        },
        {
            'cliente': clientes[2],
            'responsavel_criacao': 'Farmacêutico João',
            'status': 'aprovada',
            'observacoes': 'Pagamento confirmado via PIX'
        },
        {
            'cliente': clientes[3],
            'responsavel_criacao': 'Atendente Carlos',
            'status': 'entregue',
            'observacoes': 'Entrega realizada com sucesso'
        }
    ]
    
    encomendas = []
    for data in encomendas_data:
        encomenda = Encomenda.objects.create(**data)
        encomendas.append(encomenda)
        print(f"Encomenda criada: #{encomenda.numero_encomenda}")
    
    # Criar itens das encomendas
    itens_data = [
        # Encomenda 1
        {
            'encomenda': encomendas[0],
            'produto': produtos[0],  # Dipirona
            'fornecedor': fornecedores[0],
            'quantidade': 2,
            'preco_cotado': Decimal('12.00'),
            'observacoes': 'Desconto de 4%'
        },
        {
            'encomenda': encomendas[0],
            'produto': produtos[2],  # Omeprazol
            'fornecedor': fornecedores[1],
            'quantidade': 1,
            'preco_cotado': Decimal('24.90'),
            'observacoes': ''
        },
        # Encomenda 2
        {
            'encomenda': encomendas[1],
            'produto': produtos[1],  # Paracetamol
            'fornecedor': fornecedores[0],
            'quantidade': 3,
            'preco_cotado': Decimal('8.50'),
            'observacoes': 'Promoção'
        },
        {
            'encomenda': encomendas[1],
            'produto': produtos[4],  # Vitamina D3
            'fornecedor': fornecedores[2],
            'quantidade': 1,
            'preco_cotado': Decimal('34.90'),
            'observacoes': ''
        },
        # Encomenda 3
        {
            'encomenda': encomendas[2],
            'produto': produtos[3],  # Losartana
            'fornecedor': fornecedores[1],
            'quantidade': 2,
            'preco_cotado': Decimal('18.00'),
            'observacoes': 'Medicamento de uso contínuo'
        },
        {
            'encomenda': encomendas[2],
            'produto': produtos[5],  # Protetor Solar
            'fornecedor': fornecedores[2],
            'quantidade': 1,
            'preco_cotado': Decimal('40.00'),
            'observacoes': 'Desconto especial'
        },
        # Encomenda 4
        {
            'encomenda': encomendas[3],
            'produto': produtos[0],  # Dipirona
            'fornecedor': fornecedores[0],
            'quantidade': 1,
            'preco_cotado': Decimal('12.50'),
            'observacoes': ''
        }
    ]
    
    for data in itens_data:
        item = ItemEncomenda.objects.create(**data)
        print(f"Item criado: {item.produto.nome} - Qtd: {item.quantidade}")
    
    # Recalcular valores totais das encomendas
    for encomenda in encomendas:
        encomenda.calcular_valor_total()
        print(f"Valor total da encomenda #{encomenda.numero_encomenda}: R$ {encomenda.valor_total}")
    
    # Criar entregas
    entregas_data = [
        {
            'encomenda': encomendas[2],  # Encomenda aprovada
            'data_entrega': date.today() + timedelta(days=1),
            'responsavel_entrega': 'Entregador José',
            'valor_pago_adiantamento': Decimal('50.00'),
            'data_prevista': date.today() + timedelta(days=1),
            'observacoes_entrega': 'Entregar no período da manhã'
        },
        {
            'encomenda': encomendas[3],  # Encomenda entregue
            'data_entrega': date.today() - timedelta(days=1),
            'responsavel_entrega': 'Entregador José',
            'valor_pago_adiantamento': Decimal('10.00'),
            'data_entrega_realizada': date.today() - timedelta(days=1),
            'hora_entrega': datetime.now().time(),
            'entregue_por': 'José Silva',
            'assinatura_cliente': 'José Silva - Cliente',
            'data_prevista': date.today() - timedelta(days=1),
            'data_realizada': datetime.now() - timedelta(days=1),
            'observacoes_entrega': 'Entrega realizada sem problemas'
        }
    ]
    
    for data in entregas_data:
        entrega = Entrega.objects.create(**data)
        print(f"Entrega criada para encomenda #{entrega.encomenda.numero_encomenda}")
    
    print("\nDados de exemplo criados com sucesso!")
    print(f"- {len(clientes)} clientes")
    print(f"- {len(fornecedores)} fornecedores") 
    print(f"- {len(produtos)} produtos")
    print(f"- {len(encomendas)} encomendas")
    print(f"- {len(itens_data)} itens")
    print(f"- {len(entregas_data)} entregas")

if __name__ == '__main__':
    criar_dados_exemplo()
