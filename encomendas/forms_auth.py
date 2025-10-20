"""
Formulários de autenticação e equipes
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
import re

# Changed from .models_auth import Usuario to .models import Usuario
from .models import Usuario

# Usuario = get_user_model() # This line is no longer strictly necessary as we import directly


class RegistroUsuarioForm(UserCreationForm):
    """Formulário para registro de novo usuário"""

    nome_completo = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nome Completo',
            'autocomplete': 'name'
        }),
        label='Nome Completo'
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'seu.email@exemplo.com',
            'autocomplete': 'email'
        }),
        label='Email'
    )

    identificacao = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'CPF ou CNPJ (sem pontuação)',
            'autocomplete': 'off'
        }),
        label='Identificação (CPF/CNPJ)'
    )

    cargo = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Seu cargo na empresa',
            'autocomplete': 'off'
        }),
        label='Cargo'
    )

    telefone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '(XX) XXXXX-XXXX',
            'autocomplete': 'tel'
        }),
        label='Telefone (opcional)'
    )

    password1 = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite uma senha segura',
            'autocomplete': 'new-password',
            'id': 'password-input'
        }),
        help_text='Mínimo 6 caracteres, com letra maiúscula, minúscula e número'
    )

    password2 = forms.CharField(
        label='Confirmar Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme sua senha',
            'autocomplete': 'new-password'
        })
    )

    class Meta:
        model = Usuario
        fields = ('nome_completo', 'email', 'identificacao', 'cargo', 'telefone', 'password1', 'password2')

    def clean_email(self):
        """Valida se o email já está registrado"""
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise ValidationError('Este email já está registrado.')
        return email

    def clean_identificacao(self):
        """Valida se a identificação já está registrada"""
        identificacao = self.cleaned_data.get('identificacao')
        if Usuario.objects.filter(identificacao=identificacao).exists():
            raise ValidationError('Esta identificação já está registrada.')
        return identificacao

    def clean_password1(self):
        """Valida requisitos de senha"""
        password = self.cleaned_data.get('password1')

        if len(password) < 6:
            raise ValidationError('A senha deve ter no mínimo 6 caracteres.')

        if not re.search(r'[A-Z]', password):
            raise ValidationError('A senha deve conter pelo menos uma letra maiúscula.')

        if not re.search(r'[a-z]', password):
            raise ValidationError('A senha deve conter pelo menos uma letra minúscula.')

        if not re.search(r'\d', password):
            raise ValidationError('A senha deve conter pelo menos um número.')

        return password

    def clean_password2(self):
        """Valida se as senhas coincidem"""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError('As senhas não coincidem.')

        return password2

    def save(self, commit=True):
        """Salva o usuário com os dados adicionais"""
        user = super().save(commit=False)
        user.nome_completo = self.cleaned_data['nome_completo']
        user.identificacao = self.cleaned_data['identificacao']
        user.cargo = self.cleaned_data['cargo']
        user.telefone = self.cleaned_data.get('telefone', '')
        user.username = self.cleaned_data['email']  # Usar email como username

        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    """Formulário de login"""

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'seu.email@exemplo.com',
            'autocomplete': 'email'
        }),
        label='Email'
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Sua senha',
            'autocomplete': 'current-password',
            'id': 'password-input'
        }),
        label='Senha'
    )

    lembrar_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Lembrar-me neste navegador'
    )


class SolicitarResetSenhaForm(forms.Form):
    """Formulário para solicitar reset de senha"""

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'seu.email@exemplo.com',
            'autocomplete': 'email'
        }),
        label='Email'
    )


class RedefinirSenhaForm(forms.Form):
    """Formulário para redefinir senha"""

    nova_senha = forms.CharField(
        label='Nova Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite sua nova senha',
            'autocomplete': 'new-password',
            'id': 'password-input'
        }),
        help_text='Mínimo 6 caracteres, com letra maiúscula, minúscula e número'
    )

    confirmar_senha = forms.CharField(
        label='Confirmar Nova Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme sua nova senha',
            'autocomplete': 'new-password'
        })
    )

    def clean_nova_senha(self):
        """Valida requisitos de senha"""
        password = self.cleaned_data.get('nova_senha')

        if len(password) < 6:
            raise ValidationError('A senha deve ter no mínimo 6 caracteres.')

        if not re.search(r'[A-Z]', password):
            raise ValidationError('A senha deve conter pelo menos uma letra maiúscula.')

        if not re.search(r'[a-z]', password):
            raise ValidationError('A senha deve conter pelo menos uma letra minúscula.')

        if not re.search(r'\d', password):
            raise ValidationError('A senha deve conter pelo menos um número.')

        return password

    def clean_confirmar_senha(self):
        """Valida se as senhas coincidem"""
        nova_senha = self.cleaned_data.get('nova_senha')
        confirmar_senha = self.cleaned_data.get('confirmar_senha')

        if nova_senha and confirmar_senha and nova_senha != confirmar_senha:
            raise ValidationError('As senhas não coincidem.')

        return confirmar_senha


class AlterarSenhaForm(forms.Form):
    """Formulário para alterar senha do usuário logado"""

    senha_atual = forms.CharField(
        label='Senha Atual',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Sua senha atual',
            'autocomplete': 'current-password'
        })
    )

    nova_senha = forms.CharField(
        label='Nova Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite sua nova senha',
            'autocomplete': 'new-password',
            'id': 'password-input'
        }),
        help_text='Mínimo 6 caracteres, com letra maiúscula, minúscula e número'
    )

    confirmar_senha = forms.CharField(
        label='Confirmar Nova Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme sua nova senha',
            'autocomplete': 'new-password'
        })
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_senha_atual(self):
        """Valida se a senha atual está correta"""
        senha_atual = self.cleaned_data.get('senha_atual')

        if not self.user.check_password(senha_atual):
            raise ValidationError('Senha atual incorreta.')

        return senha_atual

    def clean_nova_senha(self):
        """Valida requisitos de senha"""
        password = self.cleaned_data.get('nova_senha')

        if len(password) < 6:
            raise ValidationError('A senha deve ter no mínimo 6 caracteres.')

        if not re.search(r'[A-Z]', password):
            raise ValidationError('A senha deve conter pelo menos uma letra maiúscula.')

        if not re.search(r'[a-z]', password):
            raise ValidationError('A senha deve conter pelo menos uma letra minúscula.')

        if not re.search(r'\d', password):
            raise ValidationError('A senha deve conter pelo menos um número.')

        # Verificar se é diferente da senha atual
        if self.user.check_password(password):
            raise ValidationError('A nova senha deve ser diferente da senha atual.')

        return password

    def clean_confirmar_senha(self):
        """Valida se as senhas coincidem"""
        nova_senha = self.cleaned_data.get('nova_senha')
        confirmar_senha = self.cleaned_data.get('confirmar_senha')

        if nova_senha and confirmar_senha and nova_senha != confirmar_senha:
            raise ValidationError('As senhas não coincidem.')

        return confirmar_senha


class CriarEquipeForm(forms.Form):
    """Formulário para criar nova equipe"""

    nome = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nome da Equipe',
            'autocomplete': 'off'
        }),
        label='Nome da Equipe'
    )

    descricao = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Descrição da equipe (opcional)',
            'rows': 4,
            'autocomplete': 'off'
        }),
        label='Descrição'
    )


class ConvidarMembroForm(forms.Form):
    """Formulário para convidar membro para equipe"""

    PAPEL_CHOICES = (
        ('membro', 'Membro'),
        ('gerente', 'Gerente'),
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@exemplo.com',
            'autocomplete': 'email'
        }),
        label='Email do Convidado'
    )

    papel = forms.ChoiceField(
        choices=PAPEL_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Papel na Equipe'
    )