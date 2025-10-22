# encomendas/forms_auth.py

"""
Formulários de autenticação e equipes
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model, password_validation
from django.conf import settings # Import settings
import re

# Import models from the main models file
from .models import Usuario, MembroEquipe

# No need for this if Usuario is imported directly
# Usuario = get_user_model()


class RegistroUsuarioForm(UserCreationForm):
    """Formulário para registro de novo usuário. Uses Usuario model."""

    # Define fields directly, inheriting validation logic is complex with custom User
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
        max_length=20, # Adjust max_length as needed
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'CPF ou CNPJ (apenas números)', # Clarify format
            'autocomplete': 'off'
        }),
        label='Identificação (CPF/CNPJ)'
        # Add clean_identificacao for validation/formatting if needed
    )

    cargo = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Seu cargo na empresa',
            'autocomplete': 'organization-title' # More appropriate autocomplete
        }),
        label='Cargo'
    )

    telefone = forms.CharField(
        max_length=20,
        required=False, # Make it optional
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
            'id': 'password-input' # Keep for JS hook if needed
        }),
        # Use Django's built-in password validation help text
        help_text=password_validation.password_validators_help_text_html(),
    )

    password2 = forms.CharField(
        label='Confirmar Senha',
        strip=False, # Keep whitespace for comparison
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme sua senha',
            'autocomplete': 'new-password'
        })
    )

    class Meta:
        model = Usuario
        # Fields handled by UserCreationForm: username (set from email later), password1, password2
        # Fields needed for our custom user: email, nome_completo, identificacao, cargo, telefone
        fields = ('nome_completo', 'email', 'identificacao', 'cargo', 'telefone')

    def clean_email(self):
        """Valida se o email já está registrado"""
        email = self.cleaned_data.get('email')
        # Case-insensitive check
        if Usuario.objects.filter(email__iexact=email).exists():
            raise ValidationError('Este email já está registrado.')
        return email

    def clean_identificacao(self):
        """Valida se a identificação já está registrada (optional formatting)"""
        identificacao = self.cleaned_data.get('identificacao')
        # Optional: Remove punctuation before checking/saving
        # identificacao_clean = re.sub(r'\D', '', identificacao) # Removes non-digits
        # Add validation for CPF/CNPJ format if desired
        if Usuario.objects.filter(identificacao=identificacao).exists():
            raise ValidationError('Esta identificação já está registrada.')
        return identificacao # Return original or cleaned version

    def clean_password2(self):
        """Valida se as senhas coincidem"""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError('As senhas não coincidem.', code='password_mismatch')

        return password2

    def save(self, commit=True):
        """Salva o usuário com os dados adicionais, uses email as username."""
        user = super().save(commit=False) # Creates user instance, sets password
        user.email = self.cleaned_data['email']
        # Set username = email for compatibility with AbstractUser
        user.username = self.cleaned_data['email']
        user.nome_completo = self.cleaned_data['nome_completo']
        user.identificacao = self.cleaned_data['identificacao']
        user.cargo = self.cleaned_data['cargo']
        user.telefone = self.cleaned_data.get('telefone', '')

        if commit:
            user.save()
            # If using ManyToManyFields directly on the form (not typical for UserCreationForm)
            # self.save_m2m()
        return user


class LoginForm(forms.Form):
    """Formulário de login using email."""

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'seu.email@exemplo.com',
            'autocomplete': 'email', # Standard autocomplete
            'autofocus': True, # Focus on email field
        }),
        label='Email'
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Sua senha',
            'autocomplete': 'current-password',
            'id': 'password-input' # Keep for JS hook
        }),
        label='Senha',
        strip=False, # Don't strip whitespace from password
    )

    lembrar_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input' # Ensure Bootstrap class is applied
        }),
        label='Lembrar-me neste navegador'
    )


class SolicitarResetSenhaForm(forms.Form):
    """Formulário para solicitar reset de senha"""

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email cadastrado na sua conta', # More specific placeholder
            'autocomplete': 'email',
            'autofocus': True,
        }),
        label='Email'
    )


class RedefinirSenhaForm(forms.Form):
    """Formulário para redefinir senha using token."""

    nova_senha = forms.CharField(
        label='Nova Senha',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite sua nova senha segura',
            'autocomplete': 'new-password',
            'id': 'password-input'
        }),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(), # Use Django's help text
    )

    confirmar_senha = forms.CharField(
        label='Confirmar Nova Senha',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme sua nova senha',
            'autocomplete': 'new-password'
        })
    )

    # Use Django's password validation
    def clean_nova_senha(self):
        password = self.cleaned_data.get('nova_senha')
        try:
            password_validation.validate_password(password)
        except ValidationError as error:
            self.add_error('nova_senha', error) # Add errors directly to the field
        return password

    def clean_confirmar_senha(self):
        """Valida se as senhas coincidem"""
        nova_senha = self.cleaned_data.get('nova_senha')
        confirmar_senha = self.cleaned_data.get('confirmar_senha')

        if nova_senha and confirmar_senha and nova_senha != confirmar_senha:
            raise ValidationError('As senhas não coincidem.', code='password_mismatch')

        return confirmar_senha


class AlterarSenhaForm(forms.Form):
    """Formulário para alterar senha do usuário logado"""

    senha_atual = forms.CharField(
        label='Senha Atual',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Sua senha atual',
            'autocomplete': 'current-password',
            'autofocus': True,
        })
    )

    nova_senha = forms.CharField(
        label='Nova Senha',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite sua nova senha',
            'autocomplete': 'new-password',
            'id': 'password-input' # Keep for JS
        }),
        help_text=password_validation.password_validators_help_text_html(),
    )

    confirmar_senha = forms.CharField(
        label='Confirmar Nova Senha',
        strip=False,
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
            raise ValidationError('Senha atual incorreta.', code='invalid_current_password')
        return senha_atual

    def clean_nova_senha(self):
        """Valida requisitos de senha e if it's different from current."""
        nova_senha = self.cleaned_data.get('nova_senha')
        senha_atual = self.cleaned_data.get('senha_atual') # Needed for comparison

        # Use Django's validation first
        try:
            password_validation.validate_password(nova_senha, self.user) # Pass user context
        except ValidationError as error:
            self.add_error('nova_senha', error)
            return nova_senha # Return early if validation fails

        # Check if it's different from the current password
        if senha_atual and nova_senha == senha_atual:
        # Simplified: Rely on check_password within validate_password (if configured)
        # Or explicitly check: if self.user.check_password(nova_senha):
            self.add_error('nova_senha', ValidationError('A nova senha deve ser diferente da senha atual.', code='password_same_as_current'))

        return nova_senha

    def clean_confirmar_senha(self):
        """Valida se as senhas coincidem"""
        nova_senha = self.cleaned_data.get('nova_senha')
        confirmar_senha = self.cleaned_data.get('confirmar_senha')

        # Only check if nova_senha passed its validation
        if nova_senha and confirmar_senha and nova_senha != confirmar_senha:
            raise ValidationError('As senhas não coincidem.', code='password_mismatch')

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
        required=False, # Optional description
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Descreva o propósito da equipe (opcional)',
            'rows': 3, # Reduced rows slightly
            'autocomplete': 'off'
        }),
        label='Descrição'
    )


class ConvidarMembroForm(forms.Form):
    """Formulário para convidar membro para equipe"""

    # Use choices from the model for consistency
    PAPEL_CHOICES = MembroEquipe.PAPEL_CHOICES

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email.do.convidado@exemplo.com',
            'autocomplete': 'off' # Turn off autocomplete for invites
        }),
        label='Email do Convidado'
    )

    papel = forms.ChoiceField(
        choices=PAPEL_CHOICES,
        initial='membro', # Default to 'membro'
        widget=forms.Select(attrs={
            'class': 'form-select' # Use form-select
        }),
        label='Papel na Equipe'
    )


class AlterarPapelForm(forms.Form):
    """Formulário simples para alterar o papel de um membro."""
    # Use choices from model
    PAPEL_CHOICES = MembroEquipe.PAPEL_CHOICES

    papel = forms.ChoiceField(
        choices=PAPEL_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-sm' # Small select
            }),
        label="Novo Papel" # Keep label simple, context is in the table
    )