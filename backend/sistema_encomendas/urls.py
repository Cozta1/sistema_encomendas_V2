# sistema_encomendas/urls.py

from django.contrib import admin
from django.urls import path, include
# Imports para os endpoints de token JWT
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # Mantenha o admin do Django
    path('admin/', admin.site.urls),

    # --- Endpoints da API ---
    # URLs de autenticação JWT (Login e Refresh Token)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Inclui as URLs da API do app 'encomendas' sob o prefixo /api/
    path('api/', include('encomendas.urls')), # Novo include para a API

    # --- REMOVA ou COMENTE o include antigo que apontava para as views HTML ---
    # path('', include('encomendas.urls')), # REMOVA ou COMENTE esta linha

    # (Opcional) Mantenha URLs de autenticação baseadas em sessão se ainda precisar delas
    # Ou mova-as para um include separado se preferir
    # Exemplo: path('auth/', include('encomendas.urls_auth')),
]

# (Opcional) Adicione configurações para servir arquivos de mídia em desenvolvimento
# from django.conf import settings
# from django.conf.urls.static import static
# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)