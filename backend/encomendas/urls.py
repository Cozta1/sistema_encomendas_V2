from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views
from . import views_auth

# --- Configuração do ViewSet Router ---
# O router cria automaticamente as URLs para ViewSets (ex: GET, POST, PUT, DELETE)
router = DefaultRouter()
router.register(r'equipes', views_auth.EquipeViewSet) # Gera /api/equipes/
router.register(r'clientes', views.ClienteViewSet) # Gera /api/clientes/
router.register(r'produtos', views.ProdutoViewSet) # Gera /api/produtos/
router.register(r'fornecedores', views.FornecedorViewSet) # Gera /api/fornecedores/
router.register(r'encomendas', views.EncomendaViewSet) # Gera /api/encomendas/
router.register(r'entregas', views.EntregaViewSet) # Gera /api/entregas/
router.register(r'convites', views_auth.ConviteViewSet, basename='convite') # Gera /api/convites/

# --- Lista de URLs ---
urlpatterns = [
    # 1. URLs do Router (CRUDs)
    # Inclui todas as URLs geradas pelo router (ex: /equipes/, /clientes/)
    path('', include(router.urls)),

    # 2. URLs de Autenticação (JWT)
    # (Ex: /api/auth/token/)
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # 3. URLs de Autenticação (Customizadas)
    # (Ex: /api/auth/register/)
    path('auth/register/', views_auth.RegisterView.as_view(), name='auth_register'),
    path('auth/user/', views_auth.UserProfileView.as_view(), name='auth_user_profile'),
    path('auth/alterar-senha/', views_auth.ChangePasswordView.as_view(), name='auth_change_password'),
    path('auth/solicitar-reset-senha/', views_auth.PasswordResetRequestView.as_view(), name='auth_reset_request'),
    path('auth/redefinir-senha/', views_auth.PasswordResetConfirmView.as_view(), name='auth_reset_confirm'),

    # 4. URLs de Equipes (Ações Específicas)
    # (Ex: /api/my-teams-invites/)
    path('my-teams-invites/', views_auth.MyTeamsAndInvitesView.as_view(), name='my_teams_invites'),
    path('equipes/<uuid:equipe_id>/dashboard-data/', views_auth.TeamDashboardDataView.as_view(), name='team_dashboard_data'),
    path('equipes/<uuid:equipe_id>/membros/', views_auth.MembroEquipeListView.as_view(), name='team_member_list'),
    path('equipes/<uuid:equipe_id>/convidar/', views_auth.ConvidarMembroView.as_view(), name='team_invite'),
    path('convites/<uuid:convite_id>/aceitar/', views_auth.AceitarConviteView.as_view(), name='invite_accept'),
    path('equipes/<uuid:equipe_id>/alterar-papel/<int:membro_id>/', views_auth.AlterarPapelMembroView.as_view(), name='alterar_papel_membro'),
    path('equipes/<uuid:equipe_id>/remover/<int:membro_id>/', views_auth.RemoverMembroView.as_view(), name='remover_membro'),
    path('equipes/<uuid:equipe_id>/sair/', views_auth.SairEquipeView.as_view(), name='sair_equipe'),
]