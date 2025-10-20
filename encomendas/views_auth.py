"""
Views para autenticação e gerenciamento de equipes
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from datetime import timedelta
import uuid

from .forms_auth import (
    RegistroUsuarioForm, LoginForm, SolicitarResetSenhaForm,
    RedefinirSenhaForm, AlterarSenhaForm, CriarEquipeForm, ConvidarMembroForm
)
# Updated import to include Encomenda
from .models import Usuario, Equipe, MembroEquipe, ConviteEquipe, Encomenda

# This line is no longer strictly necessary as we import directly
Usuario = get_user_model()


def registro(request):
    """View para registro de novo usuário"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save()

            # Enviar email de boas-vindas
            enviar_email_boas_vindas(usuario)

            messages.success(request, 'Cadastro realizado com sucesso! Você pode fazer login agora.')
            return redirect('login')
        else:
            # Mostrar erros de validação
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = RegistroUsuarioForm()

    context = {
        'form': form,
        'title': 'Criar Conta'
    }
    return render(request, 'encomendas/auth/registro.html', context)


def login_view(request):
    """View para login de usuário"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            lembrar_me = form.cleaned_data.get('lembrar_me', False)

            # Autenticar usando email
            usuario = authenticate(request, username=email, password=password)

            if usuario is not None:
                if not usuario.ativo:
                    messages.error(request, 'Sua conta foi desativada. Contate o administrador.')
                    return redirect('login')

                login(request, usuario)

                if not lembrar_me:
                    # Sessão expira quando o navegador fecha
                    request.session.set_expiry(0)

                # Redirecionar para a equipe padrão ou dashboard
                equipes = usuario.equipes.all()
                if equipes.exists():
                    return redirect('dashboard_equipe', equipe_id=equipes.first().id)

                messages.success(request, f'Bem-vindo, {usuario.nome_completo}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Email ou senha incorretos.')
    else:
        form = LoginForm()

    context = {
        'form': form,
        'title': 'Login'
    }
    return render(request, 'encomendas/auth/login.html', context)


def logout_view(request):
    """View para logout de usuário"""
    logout(request)
    messages.success(request, 'Você foi desconectado com sucesso.')
    return redirect('login')


def solicitar_reset_senha(request):
    """View para solicitar reset de senha"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = SolicitarResetSenhaForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']

            try:
                usuario = Usuario.objects.get(email=email)

                # Gerar token de reset
                token = usuario.gerar_token_reset()

                # Enviar email com link de reset
                enviar_email_reset_senha(usuario, token)

                messages.success(request, 'Um email com instruções para redefinir sua senha foi enviado.')
                return redirect('login')
            except Usuario.DoesNotExist:
                # Não revelar se o email existe ou não por segurança
                messages.success(request, 'Se este email estiver registrado, você receberá instruções para redefinir a senha.')
                return redirect('login')
    else:
        form = SolicitarResetSenhaForm()

    context = {
        'form': form,
        'title': 'Redefinir Senha'
    }
    return render(request, 'encomendas/auth/solicitar_reset_senha.html', context)


def redefinir_senha(request, token):
    """View para redefinir senha com token"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    try:
        usuario = Usuario.objects.get(token_reset_senha=token)

        if not usuario.token_reset_valido():
            messages.error(request, 'Este link de redefinição de senha expirou.')
            return redirect('solicitar_reset_senha')
    except Usuario.DoesNotExist:
        messages.error(request, 'Link de redefinição de senha inválido.')
        return redirect('solicitar_reset_senha')

    if request.method == 'POST':
        form = RedefinirSenhaForm(request.POST)
        if form.is_valid():
            nova_senha = form.cleaned_data['nova_senha']

            usuario.set_password(nova_senha)
            usuario.limpar_token_reset()
            usuario.save()

            messages.success(request, 'Sua senha foi redefinida com sucesso. Você pode fazer login agora.')
            return redirect('login')
    else:
        form = RedefinirSenhaForm()

    context = {
        'form': form,
        'title': 'Redefinir Senha',
        'token': token
    }
    return render(request, 'encomendas/auth/redefinir_senha.html', context)


@login_required(login_url='login')
def alterar_senha(request):
    """View para alterar senha do usuário logado"""
    if request.method == 'POST':
        form = AlterarSenhaForm(request.user, request.POST)
        if form.is_valid():
            nova_senha = form.cleaned_data['nova_senha']

            request.user.set_password(nova_senha)
            request.user.save()

            # Re-autenticar o usuário para manter a sessão
            login(request, request.user)

            messages.success(request, 'Sua senha foi alterada com sucesso.')
            return redirect('perfil')
    else:
        form = AlterarSenhaForm(request.user)

    context = {
        'form': form,
        'title': 'Alterar Senha'
    }
    return render(request, 'encomendas/auth/alterar_senha.html', context)


@login_required(login_url='login')
def perfil(request):
    """View para visualizar e editar perfil do usuário"""
    context = {
        'usuario': request.user,
        'title': 'Meu Perfil'
    }
    return render(request, 'encomendas/auth/perfil.html', context)


# Views de Equipes

@login_required(login_url='login')
def listar_equipes(request):
    """View para listar equipes do usuário e convites pendentes"""
    equipes = request.user.equipes.all()
    equipes_administradas = request.user.equipes_administradas.all()

    # Query for pending invitations for the logged-in user
    convites_pendentes = ConviteEquipe.objects.filter(
        email=request.user.email,
        status='pendente'
    ).select_related('equipe', 'criado_por')

    context = {
        'equipes': equipes,
        'equipes_administradas': equipes_administradas,
        'convites_pendentes': convites_pendentes, # Add invitations to context
        'title': 'Minhas Equipes'
    }
    return render(request, 'encomendas/equipes/listar_equipes.html', context)


@login_required(login_url='login')
def criar_equipe(request):
    """View para criar nova equipe"""
    if request.method == 'POST':
        form = CriarEquipeForm(request.POST)
        if form.is_valid():
            equipe = Equipe.objects.create(
                nome=form.cleaned_data['nome'],
                descricao=form.cleaned_data['descricao'],
                administrador=request.user
            )

            # Adicionar o criador como membro administrador
            MembroEquipe.objects.create(
                equipe=equipe,
                usuario=request.user,
                papel='administrador'
            )

            messages.success(request, f'Equipe "{equipe.nome}" criada com sucesso!')
            return redirect('gerenciar_equipe', equipe_id=equipe.id)
    else:
        form = CriarEquipeForm()

    context = {
        'form': form,
        'title': 'Criar Nova Equipe'
    }
    return render(request, 'encomendas/equipes/criar_equipe.html', context)


@login_required(login_url='login')
def gerenciar_equipe(request, equipe_id):
    """View para gerenciar uma equipe"""
    equipe = get_object_or_404(Equipe, id=equipe_id)

    # Verificar se o usuário é administrador
    if not equipe.eh_administrador(request.user):
        messages.error(request, 'Você não tem permissão para gerenciar esta equipe.')
        return redirect('listar_equipes')

    membros = MembroEquipe.objects.filter(equipe=equipe)
    convites = ConviteEquipe.objects.filter(equipe=equipe, status='pendente')

    context = {
        'equipe': equipe,
        'membros': membros,
        'convites': convites,
        'title': f'Gerenciar Equipe: {equipe.nome}'
    }
    return render(request, 'encomendas/equipes/gerenciar_equipe.html', context)


@login_required(login_url='login')
def convidar_membro(request, equipe_id):
    """View para convidar membro para equipe"""
    equipe = get_object_or_404(Equipe, id=equipe_id)

    # Verificar se o usuário é administrador
    if not equipe.eh_administrador(request.user):
        messages.error(request, 'Você não tem permissão para convidar membros.')
        return redirect('listar_equipes')

    if request.method == 'POST':
        form = ConvidarMembroForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            papel = form.cleaned_data['papel']

            # Verificar se o usuário já é membro
            try:
                usuario = Usuario.objects.get(email=email)
                if equipe.eh_membro(usuario):
                    messages.warning(request, f'{usuario.nome_completo} já é membro desta equipe.')
                    return redirect('gerenciar_equipe', equipe_id=equipe.id)
            except Usuario.DoesNotExist:
                pass

            # Criar convite
            data_expiracao = timezone.now() + timedelta(days=7)
            ConviteEquipe.objects.create(
                equipe=equipe,
                email=email,
                papel=papel,
                criado_por=request.user,
                data_expiracao=data_expiracao
            )

            # Enviar email de convite
            enviar_email_convite_equipe(email, equipe, request.user)

            messages.success(request, f'Convite enviado para {email}.')
            return redirect('gerenciar_equipe', equipe_id=equipe.id)
    else:
        form = ConvidarMembroForm()

    context = {
        'form': form,
        'equipe': equipe,
        'title': f'Convidar Membro - {equipe.nome}'
    }
    return render(request, 'encomendas/equipes/convidar_membro.html', context)


@login_required(login_url='login')
def remover_membro(request, equipe_id, membro_id):
    """View para remover membro de equipe"""
    equipe = get_object_or_404(Equipe, id=equipe_id)

    # Verificar se o usuário é administrador
    if not equipe.eh_administrador(request.user):
        messages.error(request, 'Você não tem permissão para remover membros.')
        return redirect('listar_equipes')

    membro = get_object_or_404(MembroEquipe, equipe=equipe, usuario_id=membro_id)

    if request.method == 'POST':
        nome_membro = membro.usuario.nome_completo
        membro.delete()
        messages.success(request, f'{nome_membro} foi removido da equipe.')
        return redirect('gerenciar_equipe', equipe_id=equipe.id)

    context = {
        'membro': membro,
        'equipe': equipe,
        'title': 'Remover Membro'
    }
    return render(request, 'encomendas/equipes/remover_membro.html', context)


@login_required(login_url='login')
def aceitar_convite(request, convite_id):
    """View para aceitar convite de equipe"""
    convite = get_object_or_404(ConviteEquipe, id=convite_id)

    # Verificar se o email do convite corresponde ao do usuário
    if convite.email != request.user.email:
        messages.error(request, 'Este convite não é para você.')
        return redirect('listar_equipes')

    if not convite.eh_valido():
        messages.error(request, 'Este convite expirou.')
        return redirect('listar_equipes')

    if request.method == 'POST':
        convite.aceitar(request.user)
        messages.success(request, f'Você foi adicionado à equipe "{convite.equipe.nome}".')
        return redirect('dashboard_equipe', equipe_id=convite.equipe.id)

    # Redirect GET requests back to the list where the button is
    return redirect('listar_equipes')


@login_required(login_url='login')
def rejeitar_convite(request, convite_id):
    """View para rejeitar convite de equipe"""
    convite = get_object_or_404(ConviteEquipe, id=convite_id)

    # Verificar se o email do convite corresponde ao do usuário
    if convite.email != request.user.email:
        messages.error(request, 'Este convite não é para você.')
        return redirect('listar_equipes')

    if request.method == 'POST':
        convite.rejeitar()
        messages.success(request, f'Você rejeitou o convite da equipe "{convite.equipe.nome}".')
        return redirect('listar_equipes')

    # Redirect GET requests back to the list where the button is
    return redirect('listar_equipes')


@login_required(login_url='login')
def dashboard_equipe(request, equipe_id):
    """View para dashboard de uma equipe específica"""
    equipe = get_object_or_404(Equipe, id=equipe_id)

    # Verificar se o usuário é membro da equipe
    if not equipe.eh_membro(request.user):
        messages.error(request, 'Você não tem acesso a esta equipe.')
        return redirect('listar_equipes')

    # --- Logic from main dashboard view ---
    # NOTE: These are global stats. To make them team-specific,
    # you would need to add a relation from Encomenda to Equipe/Usuario.
    total_encomendas = Encomenda.objects.count()
    encomendas_pendentes = Encomenda.objects.filter(status__in=['criada', 'cotacao', 'aprovada', 'em_andamento']).count()
    encomendas_entregues = Encomenda.objects.filter(status='entregue').count()
    ultimas_encomendas = Encomenda.objects.select_related('cliente').order_by('-data_criacao')[:5]

    context = {
        'equipe': equipe,
        'title': f'Dashboard - {equipe.nome}',
        # Add stats to context
        'total_encomendas': total_encomendas,
        'encomendas_pendentes': encomendas_pendentes,
        'encomendas_entregues': encomendas_entregues,
        'ultimas_encomendas': ultimas_encomendas,
    }
    # Render the main dashboard template
    return render(request, 'encomendas/dashboard.html', context)


# Funções auxiliares para envio de email

def enviar_email_boas_vindas(usuario):
    """Envia email de boas-vindas ao novo usuário"""
    assunto = 'Bem-vindo ao Sistema de Encomendas!'
    mensagem = f"""
    Olá {usuario.nome_completo},
    
    Bem-vindo ao Sistema de Encomendas da Drogaria Benfica!
    
    Sua conta foi criada com sucesso. Você pode fazer login usando seu email e senha.
    
    Se tiver dúvidas, entre em contato com o administrador do sistema.
    
    Atenciosamente,
    Sistema de Encomendas
    """
    
    try:
        send_mail(
            assunto,
            mensagem,
            settings.DEFAULT_FROM_EMAIL,
            [usuario.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f'Erro ao enviar email: {e}')


def enviar_email_reset_senha(usuario, token):
    """Envia email com link para reset de senha"""
    assunto = 'Redefinir sua senha'
    link_reset = f"{settings.SITE_URL}/auth/redefinir-senha/{token}/"
    
    mensagem = f"""
    Olá {usuario.nome_completo},
    
    Você solicitou a redefinição de sua senha. Clique no link abaixo para criar uma nova senha:
    
    {link_reset}
    
    Este link é válido por 24 horas.
    
    Se você não solicitou esta redefinição, ignore este email.
    
    Atenciosamente,
    Sistema de Encomendas
    """
    
    try:
        send_mail(
            assunto,
            mensagem,
            settings.DEFAULT_FROM_EMAIL,
            [usuario.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f'Erro ao enviar email: {e}')


def enviar_email_convite_equipe(email, equipe, convidado_por):
    """Envia email de convite para equipe"""
    assunto = f'Você foi convidado para a equipe "{equipe.nome}"'
    
    mensagem = f"""
    Olá,
    
    {convidado_por.nome_completo} o convidou para participar da equipe "{equipe.nome}" no Sistema de Encomendas.
    
    Se você já tem uma conta, faça login para aceitar o convite.
    Se não tem uma conta, crie uma usando este email.
    
    Atenciosamente,
    Sistema de Encomendas
    """
    
    try:
        send_mail(
            assunto,
            mensagem,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
    except Exception as e:
        print(f'Erro ao enviar email: {e}')