# Guia de Integração - Sistema de Autenticação e Equipes

Este documento descreve como integrar o sistema de autenticação e equipes ao projeto Django existente.

## 📋 Arquivos Criados

### Modelos (Models)
- `encomendas/models_auth.py` - Modelos de usuário, equipe e convites

### Formulários (Forms)
- `encomendas/forms_auth.py` - Formulários de registro, login, reset de senha e equipes

### Views
- `encomendas/views_auth.py` - Views de autenticação e gerenciamento de equipes

### Templates
- `encomendas/templates/encomendas/auth/` - Templates de autenticação
  - `registro.html` - Formulário de registro
  - `login.html` - Formulário de login
  - `solicitar_reset_senha.html` - Solicitar reset de senha
  - `redefinir_senha.html` - Redefinir senha
  
- `encomendas/templates/encomendas/equipes/` - Templates de equipes
  - `listar_equipes.html` - Listar equipes do usuário
  - `criar_equipe.html` - Criar nova equipe
  - `gerenciar_equipe.html` - Gerenciar membros da equipe
  - `convidar_membro.html` - Convidar membro para equipe

## 🔧 Passos de Integração

### 1. Atualizar settings.py

Adicione as seguintes configurações ao arquivo `sistema_encomendas/settings.py`:

```python
# Modelo de usuário customizado
AUTH_USER_MODEL = 'encomendas.Usuario'

# Configurações de login
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# Configurações de email (para reset de senha)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Para desenvolvimento
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # Para produção
EMAIL_HOST = 'seu-servidor-smtp.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'seu-email@exemplo.com'
EMAIL_HOST_PASSWORD = 'sua-senha'
DEFAULT_FROM_EMAIL = 'seu-email@exemplo.com'

# URL do site para links de reset de senha
SITE_URL = 'http://localhost:8000'  # Mudar para URL de produção
```

### 2. Atualizar urls.py

Adicione as URLs de autenticação ao arquivo `sistema_encomendas/urls.py`:

```python
from django.urls import path, include
from encomendas import views_auth

urlpatterns = [
    # ... URLs existentes ...
    
    # URLs de autenticação
    path('auth/registro/', views_auth.registro, name='registro'),
    path('auth/login/', views_auth.login_view, name='login'),
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
```

### 3. Criar Migrações

Execute os seguintes comandos:

```bash
python manage.py makemigrations encomendas
python manage.py migrate
```

### 4. Criar Superusuário

```bash
python manage.py createsuperuser
```

Nota: O superusuário será criado com o modelo `Usuario` customizado.

### 5. Atualizar Admin

Adicione o seguinte ao arquivo `encomendas/admin.py`:

```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models_auth import Usuario, Equipe, MembroEquipe, ConviteEquipe

@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informações Adicionais', {'fields': ('nome_completo', 'identificacao', 'cargo', 'telefone', 'ativo')}),
    )
    list_display = ('email', 'nome_completo', 'cargo', 'ativo')

@admin.register(Equipe)
class EquipeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'administrador', 'ativa')
    filter_horizontal = ('membros',)

@admin.register(MembroEquipe)
class MembroEquipeAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'equipe', 'papel')

@admin.register(ConviteEquipe)
class ConviteEquipeAdmin(admin.ModelAdmin):
    list_display = ('email', 'equipe', 'status', 'data_criacao')
```

### 6. Atualizar requirements.txt

Adicione a dependência de email (se necessário):

```
Django==5.2.7
django-extensions==3.2.3
```

## 🔐 Funcionalidades de Segurança

### Validação de Senha

A senha deve conter:
- Mínimo 6 caracteres
- Pelo menos uma letra maiúscula
- Pelo menos uma letra minúscula
- Pelo menos um número

### Reset de Senha

- Token válido por 24 horas
- Token único e aleatório
- Email de confirmação enviado ao usuário
- Nova senha deve ser diferente da anterior

### Equipes

- Apenas administradores podem gerenciar membros
- Convites expiram em 7 dias
- Múltiplos usuários podem acessar a mesma dashboard via equipe
- Controle de acesso baseado em membros da equipe

## 📝 Exemplo de Uso

### Registro de Novo Usuário

1. Acesse `http://localhost:8000/auth/registro/`
2. Preencha o formulário com:
   - Nome Completo
   - Email
   - Identificação (CPF/CNPJ)
   - Cargo
   - Telefone (opcional)
   - Senha (com requisitos)
   - Confirmar Senha

### Login

1. Acesse `http://localhost:8000/auth/login/`
2. Digite email e senha
3. Opcionalmente, marque "Lembrar-me"

### Criar Equipe

1. Após login, acesse `http://localhost:8000/equipes/`
2. Clique em "Nova Equipe"
3. Preencha nome e descrição
4. Clique em "Criar Equipe"

### Convidar Membro

1. Na página de gerenciamento da equipe, clique em "Convidar Membro"
2. Digite o email do usuário
3. Selecione o papel (Membro ou Gerente)
4. Clique em "Enviar Convite"

## 🌐 Integração com Dashboard

Para integrar com a dashboard existente:

1. Adicione `@login_required` aos decoradores das views de encomendas
2. Modifique as views para filtrar dados por equipe do usuário
3. Atualize os templates para mostrar a equipe atual

Exemplo:

```python
from django.contrib.auth.decorators import login_required

@login_required(login_url='login')
def dashboard(request):
    # Obter equipe do usuário
    equipes = request.user.equipes.all()
    
    if equipes.exists():
        equipe = equipes.first()
        # Filtrar encomendas por equipe
        encomendas = Encomenda.objects.filter(equipe=equipe)
    else:
        encomendas = Encomenda.objects.none()
    
    context = {
        'encomendas': encomendas,
        'equipe': equipes.first() if equipes.exists() else None,
    }
    return render(request, 'encomendas/dashboard.html', context)
```

## 📧 Configuração de Email

Para produção, configure um servidor SMTP:

```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'seu-email@gmail.com'
EMAIL_HOST_PASSWORD = 'sua-senha-app'  # Use App Password para Gmail
DEFAULT_FROM_EMAIL = 'seu-email@gmail.com'
```

## 🐛 Troubleshooting

### Erro: "No module named 'encomendas.models_auth'"

Certifique-se de que os arquivos `models_auth.py` e `forms_auth.py` estão no diretório `encomendas/`.

### Erro: "AUTH_USER_MODEL refers to model 'encomendas.Usuario' that has not been installed"

Verifique se `encomendas` está em `INSTALLED_APPS` no settings.py.

### Emails não são enviados

Para desenvolvimento, use `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'` para ver os emails no console.

## 📚 Referências

- [Django Authentication System](https://docs.djangoproject.com/en/5.2/topics/auth/)
- [Django Custom User Model](https://docs.djangoproject.com/en/5.2/topics/auth/customizing/#substituting-a-custom-user-model)
- [Django Password Validation](https://docs.djangoproject.com/en/5.2/topics/auth/passwords/)

