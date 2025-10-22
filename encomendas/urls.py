# encomendas/urls.py
from django.urls import path, include
from django.views.generic.base import RedirectView
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect # <<<--- ADD THIS IMPORT

from encomendas import views_auth # Views related to auth and teams
from . import views # Views related to core encomenda logic

urlpatterns = [
    # --- Root Redirect ---
    # Redirect '/' to login if not authenticated, otherwise to team list/dashboard
    path('', lambda request: redirect('listar_equipes') if request.user.is_authenticated else redirect('login'), name='root_redirect'),

    # --- Core Encomenda/CRUD URLs (Assumed team context via views) ---
    path('dashboard-global/', views.dashboard, name='dashboard_global'), # Keep old global dashboard if needed, maybe rename

    path('encomendas/', views.encomenda_list, name='encomenda_list'),
    path('encomendas/nova/', views.encomenda_create, name='encomenda_create'), # View needs team context
    path('encomendas/<int:pk>/', views.encomenda_detail, name='encomenda_detail'), # View checks team membership
    path('encomendas/<int:pk>/editar/', views.encomenda_edit, name='encomenda_edit'), # View checks team membership
    path('encomendas/<int:pk>/excluir/', views.encomenda_delete, name='encomenda_delete'), # View checks team membership

    # Entrega URLs (relative to encomenda usually, views check team membership)
    path('encomendas/<int:encomenda_pk>/entrega/nova/', views.entrega_create, name='entrega_create'),
    path('entregas/<int:pk>/editar/', views.entrega_edit, name='entrega_edit'),
    path('entregas/<int:pk>/marcar-realizada/', views.marcar_entrega_realizada, name='marcar_entrega_realizada'), # POST only view

    # Clientes, Produtos, Fornecedores (Assuming Global for now)
    path('clientes/', views.cliente_list, name='cliente_list'),
    path('clientes/novo/', views.cliente_create, name='cliente_create'),
    # Add edit/delete URLs for clientes if needed

    path('produtos/', views.produto_list, name='produto_list'),
    path('produtos/novo/', views.produto_create, name='produto_create'),
    # Add edit/delete URLs for produtos if needed

    path('fornecedores/', views.fornecedor_list, name='fornecedor_list'),
    path('fornecedores/novo/', views.fornecedor_create, name='fornecedor_create'),
    # Add edit/delete URLs for fornecedores if needed

    # PDF & API (Views check team membership where applicable)
    path('encomendas/<int:pk>/pdf/', views.encomenda_pdf, name='encomenda_pdf'),
    path('api/produto/<int:produto_id>/', views.api_produto_info, name='api_produto_info'), # Product global
    path('api/encomenda/<int:encomenda_pk>/status/', views.api_update_status, name='api_update_status'), # Checks team
    path('api/search-produtos/', views.search_produtos, name='search_produtos'), # Product global


    # --- Authentication URLs (Using views_auth) ---
    path('auth/registro/', views_auth.registro, name='registro'),
    path('auth/login/', views_auth.login_view, name='login'),
    path('auth/logout/', views_auth.logout_view, name='logout'),
    path('auth/solicitar-reset-senha/', views_auth.solicitar_reset_senha, name='solicitar_reset_senha'),
    path('auth/redefinir-senha/<str:token>/', views_auth.redefinir_senha, name='redefinir_senha'),
    path('auth/alterar-senha/', views_auth.alterar_senha, name='alterar_senha'),
    path('auth/perfil/', views_auth.perfil, name='perfil'),

    # --- URLs de Equipes (Using views_auth) ---
    path('equipes/', views_auth.listar_equipes, name='listar_equipes'), # List teams and invites
    path('equipes/criar/', views_auth.criar_equipe, name='criar_equipe'),

    # Team-specific actions/views
    path('equipes/<uuid:equipe_id>/dashboard/', views_auth.dashboard_equipe, name='dashboard_equipe'), # Main entry point for a team
    path('equipes/<uuid:equipe_id>/gerenciar/', views_auth.gerenciar_equipe, name='gerenciar_equipe'),
    path('equipes/<uuid:equipe_id>/convidar/', views_auth.convidar_membro, name='convidar_membro'),
    # Management actions (POST requests handled by views)
    path('equipes/<uuid:equipe_id>/alterar-papel/<int:membro_id>/', views_auth.alterar_papel_membro, name='alterar_papel_membro'),
    path('equipes/<uuid:equipe_id>/remover/<int:membro_id>/', views_auth.remover_membro, name='remover_membro'), # GET shows confirmation, POST removes
    path('equipes/<uuid:equipe_id>/sair/', views_auth.sair_equipe, name='sair_equipe'), # POST only

    # Invitation actions (POST requests handled by views)
    path('convites/<uuid:convite_id>/aceitar/', views_auth.aceitar_convite, name='aceitar_convite'),
    path('convites/<uuid:convite_id>/rejeitar/', views_auth.rejeitar_convite, name='rejeitar_convite'),

]