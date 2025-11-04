from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
# Importe AMBOS os ficheiros de views
from . import views
from . import views_auth

# --- Configuração do ViewSet Router ---
router = DefaultRouter()

# --- CORREÇÃO APLICADA ---
# 1. ViewSets de 'views.py' (CRUDs principais)
router.register(r'equipes', views_auth.EquipeViewSet, basename='equipe') # Gera /api/equipes/
router.register(r'clientes', views.ClienteViewSet)
router.register(r'produtos', views.ProdutoViewSet)
router.register(r'fornecedores', views.FornecedorViewSet)
router.register(r'encomendas', views.EncomendaViewSet)
router.register(r'entregas', views.EntregaViewSet) 

# 2. ViewSets de 'views_auth.py' (Autenticação/Convites)
router.register(r'convites', views_auth.ConviteViewSet, basename='convite') # <-- CORRETO

# --- Lista de URLs ---
urlpatterns = [
    # 1. URLs do Router (CRUDs)
    path('', include(router.urls)),

    # 2. URLs de Autenticação (JWT)
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # 3. URLs de Autenticação (Customizadas de views_auth.py)
    path('auth/register/', views_auth.UserRegisterView.as_view(), name='auth_register'),
    path('auth/user/', views_auth.UserDetailView.as_view(), name='auth_user_profile'),
    path('auth/alterar-senha/', views_auth.ChangePasswordView.as_view(), name='auth_change_password'),
    path('auth/solicitar-reset-senha/', views_auth.PasswordResetRequestView.as_view(), name='auth_reset_request'),
    path('auth/redefinir-senha/', views_auth.PasswordResetConfirmView.as_view(), name='auth_reset_confirm'),

    # 4. URLs de Equipes (Ações Específicas de views_auth.py)
    path('my-teams-invites/', views_auth.MyTeamsAndInvitesView.as_view(), name='my_teams_invites'),
    path('equipes/<uuid:equipe_id>/dashboard-data/', views_auth.TeamDashboardDataView.as_view(), name='team_dashboard_data'),
    path('equipes/<uuid:equipe_id>/membros/', views_auth.MembroEquipeListView.as_view(), name='team_member_list'),
    path('equipes/<uuid:equipe_id>/convidar/', views_auth.ConvidarMembroView.as_view(), name='team_invite'),
    path('convites/<uuid:convite_id>/aceitar/', views_auth.AceitarConviteView.as_view(), name='invite_accept'),
    path('equipes/<uuid:equipe_id>/alterar-papel/<int:membro_id>/', views_auth.AlterarPapelMembroView.as_view(), name='alterar_papel_membro'),
    path('equipes/<uuid:equipe_id>/remover/<int:membro_id>/', views_auth.RemoverMembroView.as_view(), name='remover_membro'),
    path('equipes/<uuid:equipe_id>/sair/', views_auth.SairEquipeView.as_view(), name='sair_equipe'),
]