from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- ESTA É A ÚNICA LINHA NECESSÁRIA PARA A API ---
    # Ela diz: "Qualquer URL que comece com 'api/' 
    # deve ser tratada pelo arquivo 'encomendas.urls'".
    path('api/', include('encomendas.urls')), 
]

# (Opcional, mas recomendado) Adicione isto no final 
# para servir arquivos de mídia em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)