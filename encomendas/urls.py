from django.urls import path, include
# Import RedirectView
from django.views.generic.base import RedirectView
from encomendas import views_auth
from . import views

urlpatterns = [
    # Change the root path '' to redirect to the login page
    path('', RedirectView.as_view(pattern_name='login', permanent=False), name='root_redirect'),

    # Give the dashboard its own path
    path('dashboard/', views.dashboard, name='dashboard'),

    # Encomendas (paths remain the same relative to the include)
    path('encomendas/', views.encomenda_list, name='encomenda_list'),
    path('encomendas/nova/', views.encomenda_create, name='encomenda_create'),
    path('encomendas/<int:pk>/', views.encomenda_detail, name='encomenda_detail'),
    path('encomendas/<int:pk>/editar/', views.encomenda_edit, name='encomenda_edit'),
    path('encomendas/<int:pk>/excluir/', views.encomenda_delete, name='encomenda_delete'),

    # Entregas
    path('encomendas/<int:encomenda_pk>/entrega/nova/', views.entrega_create, name='entrega_create'),
    path('entregas/<int:pk>/editar/', views.entrega_edit, name='entrega_edit'),

    # Clientes
    path('clientes/', views.cliente_list, name='cliente_list'),
    path('clientes/novo/', views.cliente_create, name='cliente_create'),

    # Produtos
    path('produtos/', views.produto_list, name='produto_list'),
    path('produtos/novo/', views.produto_create, name='produto_create'),

    # Fornecedores
    path('fornecedores/', views.fornecedor_list, name='fornecedor_list'),
    path('fornecedores/novo/', views.fornecedor_create, name='fornecedor_create'),

    # PDF e funcionalidades extras
    path('encomendas/<int:pk>/pdf/', views.encomenda_pdf, name='encomenda_pdf'),
    path('entregas/<int:pk>/marcar-realizada/', views.marcar_entrega_realizada, name='marcar_entrega_realizada'),

    # API endpoints
    path('api/produto/<int:produto_id>/', views.api_produto_info, name='api_produto_info'),
    path('api/encomenda/<int:encomenda_pk>/status/', views.api_update_status, name='api_update_status'),

    # --- Authentication URLs ---
    path('auth/registro/', views_auth.registro, name='registro'),
    path('auth/login/', views_auth.login_view, name='login'), # This is the target
    path('auth/logout/', views_auth.logout_view, name='logout'),
    path('auth/solicitar-reset-senha/', views_auth.solicitar_reset_senha, name='solicitar_reset_senha'),
    path('auth/redefinir-senha/<str:token>/', views_auth.redefinir_senha, name='redefinir_senha'),
    path('auth/alterar-senha/', views_auth.alterar_senha, name='alterar_senha'),
    path('auth/perfil/', views_auth.perfil, name='perfil'),

    # URLs de equipes
    path('equipes/', views_auth.listar_equipes, name='listar_equipes'),
    path('equipes/criar/', views_auth.criar_equipe, name='criar_equipe'),
    path('equipes/<uuid:equipe_id>/gerenciar/', views_auth.gerenciar_equipe, name='gerenciar_equipe'),
    path('equipes/<uuid:equipe_id>/convidar/', views_auth.convidar_membro, name='convidar_membro'),
    path('equipes/<uuid:equipe_id>/remover/<int:membro_id>/', views_auth.remover_membro, name='remover_membro'),
    path('equipes/<uuid:equipe_id>/dashboard/', views_auth.dashboard_equipe, name='dashboard_equipe'),
    path('convites/<uuid:convite_id>/aceitar/', views_auth.aceitar_convite, name='aceitar_convite'),
    path('convites/<uuid:convite_id>/rejeitar/', views_auth.rejeitar_convite, name='rejeitar_convite'),
]