#!/usr/bin/env python3
"""
Script para popular o banco de dados com dados de exemplo,
incluindo usuários, equipes e associação de clientes, fornecedores,
produtos e encomendas a equipes.
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
from django.db.models import Sum
from django.db.models.functions import Coalesce
# Import all models from the single models.py file
from encomendas.models import (
    Cliente, Fornecedor, Produto, Encomenda, ItemEncomenda, Entrega,
    Equipe, MembroEquipe, Usuario
)

# Obter o modelo de usuário customizado (already done via import)
# Usuario = get_user_model() # Not needed if imported directly

def criar_dados_exemplo():
    print("🧹 Limpando dados antigos...")
    # Limpar dados para evitar duplicatas
    ItemEncomenda.objects.all().delete()
    Entrega.objects.all().delete()
    Encomenda.objects.all().delete()
    Produto.objects.all().delete()
    Fornecedor.objects.all().delete()
    Cliente.objects.all().delete()
    MembroEquipe.objects.all().delete()
    Equipe.objects.all().delete()
    Usuario.objects.filter(is_superuser=False).delete()
    print("✅ Dados antigos limpos.")

    print("\n👤 Criando usuários de exemplo...")
    usuarios_data = [
        {'username': 'joao.farmaceutico@benfica.com', 'email': 'joao.farmaceutico@benfica.com', 'nome_completo': 'João Farmacêutico', 'identificacao': '11122233344', 'cargo': 'Farmacêutico Responsável', 'password': 'senha123'},
        {'username': 'maria.atendente@benfica.com', 'email': 'maria.atendente@benfica.com', 'nome_completo': 'Maria Atendente', 'identificacao': '55566677788', 'cargo': 'Atendente', 'password': 'senha123'},
        {'username': 'carlos.gerente@benfica.com', 'email': 'carlos.gerente@benfica.com', 'nome_completo': 'Carlos Gerente', 'identificacao': '99988877766', 'cargo': 'Gerente de Loja', 'password': 'senha123'}
    ]
    usuarios = []
    for data in usuarios_data:
        try:
            usuario, created = Usuario.objects.get_or_create(
                email=data['email'],
                defaults={
                    'username': data['username'],
                    'nome_completo': data['nome_completo'],
                    'identificacao': data['identificacao'],
                    'cargo': data['cargo'],
                    'is_staff': data.get('is_staff', False)
                }
            )
            # Set password only if user is newly created or needs reset
            if created:
                usuario.set_password(data['password'])
                usuario.save()
                print(f"   -> Usuário criado: {usuario.email}")
            else:
                 # Optionally update existing user details or just ensure password is set if they exist but have no password
                 # For simplicity, we assume existing users have passwords or reset if needed
                 # usuario.set_password(data['password']) # Uncomment to force password reset on existing users
                 # usuario.save()
                 print(f"   -> Usuário encontrado: {usuario.email}")
            usuarios.append(usuario)
        except Exception as e:
            print(f"   ⚠️ Erro ao criar/buscar usuário {data['email']}: {e}.")

    print("\n👥 Criando equipes de exemplo...")
    equipes = []
    if len(usuarios) >= 3: # Need at least 3 distinct users for the example setup
        try:
            equipe_centro, created_centro = Equipe.objects.get_or_create(
                nome='Equipe Centro',
                defaults={'descricao': 'Equipe responsável pelas encomendas da região central.', 'administrador': usuarios[0]} # João admin
            )
            if created_centro: print(f"   -> Equipe criada: {equipe_centro.nome}")
            equipes.append(equipe_centro)

            equipe_bairros, created_bairros = Equipe.objects.get_or_create(
                nome='Equipe Bairros',
                defaults={'descricao': 'Equipe focada nas entregas dos bairros adjacentes.', 'administrador': usuarios[2]} # Carlos admin
            )
            if created_bairros: print(f"   -> Equipe criada: {equipe_bairros.nome}")
            equipes.append(equipe_bairros)

            print("\n🤝 Adicionando membros às equipes...")
            # Ensure members are added correctly using the model method
            equipe_centro.adicionar_membro(usuarios[0], papel='administrador')
            equipe_centro.adicionar_membro(usuarios[1], papel='membro') # Maria na equipe Centro
            print(f"   -> Membros adicionados/verificados na Equipe Centro.")

            equipe_bairros.adicionar_membro(usuarios[2], papel='administrador')
            equipe_bairros.adicionar_membro(usuarios[0], papel='gerente') # João gerente na Equipe Bairros
            print(f"   -> Membros adicionados/verificados na Equipe Bairros.")
        except IndexError:
             print("   ⚠️ Não há usuários suficientes (índice fora do alcance) para criar equipes e adicionar membros conforme exemplo.")
        except Exception as e:
            print(f"   ⚠️ Erro ao criar equipes ou adicionar membros: {e}")
    else:
        print("   ⚠️ Não há usuários suficientes criados/encontrados para formar as equipes de exemplo.")


    # --- Associate Clientes, Fornecedores, Produtos with Equipes ---
    # Proceed only if equipes were created
    if equipes:
        print("\n👤 Criando clientes e associando a equipes...")
        clientes_data = [
            {'nome': 'Maria Silva Santos', 'codigo': 'CLI001', 'endereco': 'Rua das Flores, 123, Apt 201', 'bairro': 'Centro', 'referencia': 'Próximo ao Banco do Brasil', 'telefone': '(32) 99999-1234', 'equipe': equipes[0]}, # Equipe Centro
            {'nome': 'João Carlos Oliveira', 'codigo': 'CLI002', 'endereco': 'Av. Presidente Vargas, 456', 'bairro': 'São Mateus', 'referencia': 'Em frente à padaria', 'telefone': '(32) 98888-5678', 'equipe': equipes[1]}, # Equipe Bairros
            {'nome': 'Ana Paula Costa', 'codigo': 'CLI003', 'endereco': 'Rua São João, 789', 'bairro': 'Benfica', 'referencia': 'Casa azul com portão branco', 'telefone': '(32) 97777-9012', 'equipe': equipes[1]}, # Equipe Bairros
            {'nome': 'Carlos Eduardo Mendes', 'codigo': 'CLI004', 'endereco': 'Rua Marechal Deodoro, 321', 'bairro': 'Granbery', 'referencia': 'Próximo ao supermercado', 'telefone': '(32) 96666-3456', 'equipe': equipes[0]} # Equipe Centro
        ]
        clientes = []
        for data in clientes_data:
            cliente, created = Cliente.objects.get_or_create(
                equipe=data['equipe'], # Use equipe in lookup if unique_together is set
                codigo=data['codigo'],
                defaults=data
            )
            clientes.append(cliente)
            if created: print(f"   -> Cliente criado: {cliente.nome} (Equipe: {cliente.equipe.nome})")

        print("\n🚚 Criando fornecedores e associando a equipes...")
        fornecedores_data = [
            {'nome': 'Distribuidora Farmacêutica ABC', 'codigo': 'FOR001', 'contato': 'Roberto Silva', 'telefone': '(11) 3333-1111', 'email': 'vendas@abc.com.br', 'equipe': equipes[0]}, # Equipe Centro
            {'nome': 'Laboratório XYZ Ltda', 'codigo': 'FOR002', 'contato': 'Fernanda Costa', 'telefone': '(21) 4444-2222', 'email': 'comercial@xyz.com.br', 'equipe': equipes[1]}, # Equipe Bairros
            {'nome': 'Medicamentos Nacional', 'codigo': 'FOR003', 'contato': 'Paulo Santos', 'telefone': '(31) 5555-3333', 'email': 'pedidos@nacional.com.br', 'equipe': equipes[0]}, # Equipe Centro
            {'nome': 'Suprimentos Médicos Sul', 'codigo': 'FOR004', 'contato': 'Ana Lima', 'telefone': '(41) 6666-4444', 'email': 'contato@smsul.com.br', 'equipe': equipes[1]} # Equipe Bairros
        ]
        fornecedores = []
        for data in fornecedores_data:
            fornecedor, created = Fornecedor.objects.get_or_create(
                equipe=data['equipe'], # Use equipe in lookup if unique_together is set
                codigo=data['codigo'],
                defaults=data
            )
            fornecedores.append(fornecedor)
            if created: print(f"   -> Fornecedor criado: {fornecedor.nome} (Equipe: {fornecedor.equipe.nome})")

        print("\n💊 Criando produtos e associando a equipes...")
        produtos_data = [
            {'nome': 'Dipirona 500mg - 20cps', 'codigo': 'MED001', 'descricao': 'Analgésico/antitérmico', 'preco_base': Decimal('12.50'), 'categoria': 'Analgésicos', 'equipe': equipes[0]}, # Equipe Centro
            {'nome': 'Paracetamol 750mg - 10cps', 'codigo': 'MED002', 'descricao': 'Analgésico/antitérmico', 'preco_base': Decimal('8.90'), 'categoria': 'Analgésicos', 'equipe': equipes[0]}, # Equipe Centro
            {'nome': 'Omeprazol 20mg - 14caps', 'codigo': 'MED003', 'descricao': 'Inibidor bomba prótons', 'preco_base': Decimal('25.80'), 'categoria': 'Gastro', 'equipe': equipes[1]}, # Equipe Bairros
            {'nome': 'Losartana 50mg - 30cps', 'codigo': 'MED004', 'descricao': 'Anti-hipertensivo', 'preco_base': Decimal('18.70'), 'categoria': 'Cardio', 'equipe': equipes[1]}, # Equipe Bairros
            {'nome': 'Vitamina D3 2000UI - 60caps', 'codigo': 'VIT001', 'descricao': 'Suplemento vitamínico', 'preco_base': Decimal('35.90'), 'categoria': 'Vitaminas', 'equipe': equipes[0]}, # Equipe Centro
            {'nome': 'Protetor Solar FPS 60 - 120ml', 'codigo': 'COS001', 'descricao': 'Proteção solar', 'preco_base': Decimal('42.50'), 'categoria': 'Cosméticos', 'equipe': equipes[1]} # Equipe Bairros
        ]
        produtos = []
        for data in produtos_data:
            produto, created = Produto.objects.get_or_create(
                equipe=data['equipe'], # Use equipe in lookup if unique_together is set
                codigo=data['codigo'],
                defaults=data
            )
            produtos.append(produto)
            if created: print(f"   -> Produto criado: {produto.nome} (Equipe: {produto.equipe.nome})")


        print("\n📋 Criando encomendas (já associadas a equipes)...")
        # Ensure enough clientes and usuarios exist before creating encomendas
        encomendas = []
        if len(clientes) >= 4 and len(usuarios) >= 3:
            try:
                encomenda1 = Encomenda.objects.create(cliente=clientes[0], equipe=equipes[0], responsavel_criacao=usuarios[0].nome_completo, status='criada', observacoes='Cliente solicitou entrega urgente') # Cliente[0] -> Centro, Equipe[0] -> Centro
                encomendas.append(encomenda1)
                print(f"   -> Encomenda #{encomenda1.numero_encomenda} criada (Equipe: {encomenda1.equipe.nome})")

                encomenda2 = Encomenda.objects.create(cliente=clientes[1], equipe=equipes[1], responsavel_criacao=usuarios[2].nome_completo, status='cotacao', observacoes='Verificar disponibilidade') # Cliente[1] -> Bairros, Equipe[1] -> Bairros
                encomendas.append(encomenda2)
                print(f"   -> Encomenda #{encomenda2.numero_encomenda} criada (Equipe: {encomenda2.equipe.nome})")

                encomenda3 = Encomenda.objects.create(cliente=clientes[2], equipe=equipes[1], responsavel_criacao=usuarios[0].nome_completo, status='aprovada', observacoes='Pagamento confirmado') # Cliente[2] -> Bairros, Equipe[1] -> Bairros
                encomendas.append(encomenda3)
                print(f"   -> Encomenda #{encomenda3.numero_encomenda} criada (Equipe: {encomenda3.equipe.nome})")

                encomenda4 = Encomenda.objects.create(cliente=clientes[3], equipe=equipes[0], responsavel_criacao=usuarios[1].nome_completo, status='entregue', observacoes='Entrega OK') # Cliente[3] -> Centro, Equipe[0] -> Centro
                encomendas.append(encomenda4)
                print(f"   -> Encomenda #{encomenda4.numero_encomenda} criada (Equipe: {encomenda4.equipe.nome})")
            except IndexError:
                 print("   ⚠️ Não foi possível criar encomendas por falta de clientes/usuários suficientes nos índices esperados.")
            except Exception as e:
                 print(f"   ⚠️ Erro ao criar encomendas: {e}")
        else:
             print("   ⚠️ Não foi possível criar encomendas por falta de clientes ou usuários suficientes.")


        # --- Create Items, ensuring Product/Supplier match Encomenda's team ---
        print("\n📦 Criando itens das encomendas (verificando consistência de equipe)...")
        itens_criados = []
        if len(encomendas) == 4 and len(produtos) >= 6 and len(fornecedores) >= 4:
            # Helper to find items by code *within a specific team*
            def find_prod(codigo, equipe):
                return next((p for p in produtos if p.codigo == codigo and p.equipe == equipe), None)
            def find_forn(codigo, equipe):
                return next((f for f in fornecedores if f.codigo == codigo and f.equipe == equipe), None)

            # Items for Encomenda 1 (Equipe Centro)
            prod1 = find_prod('MED001', equipes[0])
            forn1 = find_forn('FOR001', equipes[0])
            prod2 = find_prod('VIT001', equipes[0]) # Changed Vit D to Centro
            forn3 = find_forn('FOR003', equipes[0]) # Changed Forn Nac to Centro
            if encomenda1 and prod1 and forn1:
                itens_criados.append(ItemEncomenda(encomenda=encomenda1, produto=prod1, fornecedor=forn1, quantidade=2, preco_cotado=Decimal('12.00')))
            if encomenda1 and prod2 and forn3:
                 itens_criados.append(ItemEncomenda(encomenda=encomenda1, produto=prod2, fornecedor=forn3, quantidade=1, preco_cotado=Decimal('34.90'))) # Vit D

            # Items for Encomenda 2 (Equipe Bairros)
            prod3 = find_prod('MED003', equipes[1]) # Omeprazol from Bairros
            forn2 = find_forn('FOR002', equipes[1]) # Lab XYZ from Bairros
            if encomenda2 and prod3 and forn2:
                itens_criados.append(ItemEncomenda(encomenda=encomenda2, produto=prod3, fornecedor=forn2, quantidade=1, preco_cotado=Decimal('25.00')))

            # Items for Encomenda 3 (Equipe Bairros)
            prod4 = find_prod('MED004', equipes[1]) # Losartana from Bairros
            prod6 = find_prod('COS001', equipes[1]) # Protetor from Bairros
            forn4 = find_forn('FOR004', equipes[1]) # Suprimentos Sul from Bairros
            if encomenda3 and prod4 and forn2: # Losartana from XYZ
                itens_criados.append(ItemEncomenda(encomenda=encomenda3, produto=prod4, fornecedor=forn2, quantidade=2, preco_cotado=Decimal('18.00')))
            if encomenda3 and prod6 and forn4: # Protetor from Suprimentos Sul
                itens_criados.append(ItemEncomenda(encomenda=encomenda3, produto=prod6, fornecedor=forn4, quantidade=1, preco_cotado=Decimal('41.50')))

            # Item for Encomenda 4 (Equipe Centro)
            # prod1 and forn1 already defined for Centro
            if encomenda4 and prod1 and forn1:
                itens_criados.append(ItemEncomenda(encomenda=encomenda4, produto=prod1, fornecedor=forn1, quantidade=1, preco_cotado=Decimal('12.50'))) # Dipirona


            if itens_criados:
                # Calculate value_total before bulk creating
                for item in itens_criados:
                    if item.quantidade and item.preco_cotado:
                         item.valor_total = item.quantidade * item.preco_cotado
                    else:
                         item.valor_total = Decimal('0.00')

                ItemEncomenda.objects.bulk_create(itens_criados)
                print(f"   -> {len(itens_criados)} itens criados com sucesso.")

                print("\n💰 Recalculando valores totais das encomendas...")
                total_itens = 0
                for encomenda in Encomenda.objects.all():
                    soma_itens = ItemEncomenda.objects.filter(encomenda=encomenda).aggregate(
                        total=Coalesce(Sum('valor_total'), Decimal('0.00'))
                    )['total']
                    if encomenda.valor_total != soma_itens:
                        encomenda.valor_total = soma_itens
                        encomenda.save(update_fields=['valor_total'])
                        print(f"   -> Valor total da encomenda #{encomenda.numero_encomenda} atualizado para: R$ {encomenda.valor_total}")
                    total_itens += ItemEncomenda.objects.filter(encomenda=encomenda).count()


                print("\n🚚 Criando entregas...")
                entregas_criadas = []
                if len(encomendas) >= 4: # Need at least 4 encomendas
                    try:
                        entrega1, c1 = Entrega.objects.get_or_create(
                            encomenda=encomendas[2], # Entrega para Enc 3 (Bairros)
                            defaults={
                                'data_entrega': date.today() + timedelta(days=1),
                                'responsavel_entrega': 'Entregador Bairros',
                                'valor_pago_adiantamento': Decimal('50.00'),
                                'data_prevista': date.today() + timedelta(days=1)}
                        )
                        if c1: entregas_criadas.append(entrega1)

                        entrega2, c2 = Entrega.objects.get_or_create(
                            encomenda=encomendas[3], # Entrega para Enc 4 (Centro)
                             defaults={
                                'data_entrega': date.today() - timedelta(days=1),
                                'responsavel_entrega': 'Entregador Centro',
                                'valor_pago_adiantamento': Decimal('10.00'),
                                'data_entrega_realizada': date.today() - timedelta(days=1),
                                'hora_entrega': (datetime.now() - timedelta(hours=1)).time(), # Some time yesterday
                                'entregue_por': 'José Silva',
                                'assinatura_cliente': True,
                                'data_prevista': date.today() - timedelta(days=1),
                                'data_realizada': timezone.now() - timedelta(days=1)} # Make timezone aware
                        )
                        if c2: entregas_criadas.append(entrega2)

                        for entrega in entregas_criadas:
                            print(f"   -> Entrega criada/encontrada para encomenda #{entrega.encomenda.numero_encomenda}")
                    except IndexError:
                        print("   ⚠️ Não foi possível criar entregas, índice de encomenda fora do alcance.")
                    except Exception as e:
                        print(f"   ⚠️ Erro ao criar entregas: {e}")
                else:
                    print("   ⚠️ Não há encomendas suficientes para criar as entregas de exemplo.")


                print("\n\n✅ Dados de exemplo criados com sucesso!")
                print(f"   -> {Usuario.objects.count()} usuários (incluindo superusuários)")
                print(f"   -> {Equipe.objects.count()} equipes")
                print(f"   -> {Cliente.objects.count()} clientes")
                print(f"   -> {Fornecedor.objects.count()} fornecedores")
                print(f"   -> {Produto.objects.count()} produtos")
                print(f"   -> {Encomenda.objects.count()} encomendas")
                print(f"   -> {ItemEncomenda.objects.count()} itens de encomenda")
                print(f"   -> {Entrega.objects.count()} entregas")
                print("\n   Logins de exemplo (senha 'senha123'):")
                for u in usuarios: # Only print non-superusers created here
                    print(f"      - {u.email}")

            else:
                 print("\n⚠️ Não foi possível criar itens de encomenda válidos devido a inconsistências de equipe ou dados ausentes.")
        else:
             print("\n⚠️ Não foi possível criar itens de encomenda por falta de encomendas, produtos ou fornecedores suficientes.")

    else:
         print("\n⚠️ Processo interrompido pois não foi possível criar as equipes (falta de usuários). Clientes, Fornecedores, Produtos e Encomendas não foram criados.")


if __name__ == '__main__':
    criar_dados_exemplo()