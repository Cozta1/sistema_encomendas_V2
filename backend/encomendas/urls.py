# encomendas/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
# (Opcional) Importe routers aninhados se precisar de URLs como /equipes/ID/encomendas/
# from rest_framework_nested import routers

# Importe as views que contêm os ViewSets e as APIs antigas/separadas
from . import views
from .views_auth import UserRegisterView # Importe a nova view
# Importe as views de autenticação/equipes se for incluí-las aqui (opcional)
# from . import views_auth

# --- Router Principal para ViewSets ---
router = DefaultRouter()
# Registra os ViewSets. O DRF criará as URLs CRUD automaticamente:
# /api/encomendas/
# /api/encomendas/{pk}/
router.register(r'encomendas', views.EncomendaViewSet, basename='encomenda')
router.register(r'clientes', views.ClienteViewSet, basename='cliente')
router.register(r'produtos', views.ProdutoViewSet, basename='produto')
router.register(r'fornecedores', views.FornecedorViewSet, basename='fornecedor')
router.register(r'entregas', views.EntregaViewSet, basename='entrega') # ViewSet ReadOnly

# --- (Opcional) Router Aninhado para recursos dentro de Equipes ---
# Exemplo: /api/equipes/{equipe_pk}/clientes/
# equipes_router = routers.SimpleRouter()
# equipes_router.register(r'equipes', views_auth.EquipeViewSet, basename='equipe') # Supondo que exista um EquipeViewSet

# nested_router = routers.NestedSimpleRouter(equipes_router, r'equipes', lookup='equipe')
# nested_router.register(r'clientes', views.ClienteViewSet, basename='equipe-clientes')
# nested_router.register(r'produtos', views.ProdutoViewSet, basename='equipe-produtos')
# nested_router.register(r'fornecedores', views.FornecedorViewSet, basename='equipe-fornecedores')
# nested_router.register(r'encomendas', views.EncomendaViewSet, basename='equipe-encomendas')

urlpatterns = [
    # --- URLs Geradas pelo Router Principal ---
    path('', include(router.urls)),

    # --- (Opcional) URLs Geradas pelo Router Aninhado ---
    # path('', include(nested_router.urls)),

    # --- NOVA URL DE REGISTRO ---
    path('users/register/', UserRegisterView.as_view(), name='user_register'), # Ex: /api/users/register/
    
    # --- Mantenha as URLs das APIs Antigas/Separadas ---
    # Certifique-se de que os nomes ('api_produto_info', etc.) não conflitem
    path('produto/<int:produto_id>/info/', views.api_produto_info, name='api_produto_info'), # Ex: /api/produto/1/info/
    path('encomenda/<int:encomenda_pk>/status/', views.api_update_status, name='api_update_status'), # Ex: /api/encomenda/1/status/
    path('search-produtos/', views.search_produtos, name='search_produtos'), # Ex: /api/search-produtos/
    path('search-clientes/', views.search_clientes, name='search_clientes'), # Ex: /api/search-clientes/
    path('search-fornecedores/', views.search_fornecedores, name='search_fornecedores'), # Ex: /api/search-fornecedores/

    # Mantenha a URL do PDF (se a view foi mantida)
    path('encomendas/<int:pk>/pdf/', views.encomenda_pdf, name='encomenda_pdf_api'), # Renomeado para evitar conflito

    # --- REMOVA ou COMENTE TODAS as URLs antigas que apontavam para views HTML ---
    # Exemplo: path('encomendas/lista/', views.encomenda_list_html_view, name='encomenda_list_html'), # REMOVA
    # Exemplo: path('clientes/novo/', views.cliente_create_html_view, name='cliente_create_html'), # REMOVA
    # ... remover todas as outras ...

    # --- URLs de Autenticação e Equipes ---
    # É melhor mantê-las separadas, talvez no urls.py principal ou em 'urls_auth.py'
    # Se decidir incluí-las aqui, ficaria algo como:
    # path('auth/registro/', views_auth.registro, name='registro_api'), # Renomear para evitar conflitos
    # path('auth/login/', views_auth.login_view, name='login_api'), # Não faz sentido via API aqui (usar /api/token/)
    # ...
]