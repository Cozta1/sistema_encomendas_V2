# encomendas/views_auth.py

"""
Views para autenticação e gerenciamento de equipes
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from datetime import timedelta
import uuid
from django.urls import reverse
from django.http import Http404, HttpResponseForbidden
from django.utils.http import url_has_allowed_host_and_scheme # Import for 'next' check

# Use ..forms_auth to ensure correct import path if structure changes
from .forms_auth import (
    RegistroUsuarioForm, LoginForm, SolicitarResetSenhaForm,
    RedefinirSenhaForm, AlterarSenhaForm, CriarEquipeForm, ConvidarMembroForm,
    AlterarPapelForm
)
# Make sure all models are imported, including Encomenda
from .models import Usuario, Equipe, MembroEquipe, ConviteEquipe, Encomenda
# Import helper function if needed elsewhere
from .views import get_equipe_atual

# --- Other views (registro, logout_view, solicitar_reset_senha, etc.) remain the same ---

# NO @login_required here
def login_view(request):
    """View para login de usuário"""
    if request.user.is_authenticated:
        # Redirect authenticated users away from login
        messages.info(request, "Você já está logado.")
        # *** CORRECTED REDIRECT HERE ***
        return redirect('root_redirect') # Use the root redirect which handles team logic

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            lembrar_me = form.cleaned_data.get('lembrar_me', False)

            usuario = authenticate(request, username=email, password=password)

            if usuario is not None:
                if not usuario.is_active:
                    messages.error(request, 'Sua conta foi desativada. Contate o administrador.')
                    return redirect('login')

                login(request, usuario)

                if not lembrar_me:
                    request.session.set_expiry(0)
                else:
                    request.session.set_expiry(settings.SESSION_COOKIE_AGE)

                # --- Handle the 'next' parameter ---
                next_url = request.GET.get('next')
                if next_url:
                    if url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()}):
                         return redirect(next_url)
                # If no 'next' or it's unsafe, Django will use LOGIN_REDIRECT_URL ('root_redirect')
                # No explicit redirect needed here unless 'next' logic fails
                # return redirect('root_redirect') # This is handled by Django if 'next' is not present/valid

            else:
                messages.error(request, 'Email ou senha incorretos.')
    else:
        form = LoginForm()

    context = {
        'form': form,
        'title': 'Login'
    }
    return render(request, 'encomendas/auth/login.html', context)

# --- Other views (logout_view, solicitar_reset_senha, etc.) remain the same ---
@login_required(login_url='login')
@require_http_methods(["POST"]) # Ensure logout is always via POST
def logout_view(request):
    """View para logout de usuário"""
    logout(request)
    messages.success(request, 'Você foi desconectado com sucesso.')
    return redirect('login')


# NO @login_required here
def registro(request):
    """View para registro de novo usuário"""
    if request.user.is_authenticated:
        messages.info(request, "Você já está logado.")
        # *** CORRECTED REDIRECT ***
        return redirect('root_redirect') # Redirect to the main dashboard router view

    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            # Check if function exists before calling
            if callable(globals().get('enviar_email_boas_vindas')):
                enviar_email_boas_vindas(request, usuario)
            messages.success(request, 'Cadastro realizado com sucesso! Você pode fazer login agora.')
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    field_name = form.fields.get(field).label if form.fields.get(field) else field
                    messages.error(request, f'{field_name}: {error}')
    else:
        form = RegistroUsuarioForm()

    context = {
        'form': form,
        'title': 'Criar Conta'
    }
    return render(request, 'encomendas/auth/registro.html', context)


# NO @login_required here
def solicitar_reset_senha(request):
    """View para solicitar reset de senha"""
    if request.user.is_authenticated:
        messages.info(request, "Você já está logado.")
        # *** CORRECTED REDIRECT ***
        return redirect('root_redirect') # Redirect authenticated users

    if request.method == 'POST':
        form = SolicitarResetSenhaForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']

            try:
                usuario = Usuario.objects.get(email__iexact=email, is_active=True)
                token = usuario.gerar_token_reset()
                # Check if function exists before calling
                if callable(globals().get('enviar_email_reset_senha')):
                    enviar_email_reset_senha(request, usuario, token)
                messages.success(request, 'Um email com instruções para redefinir sua senha foi enviado (se o email estiver registrado e ativo).')
                return redirect('login')
            except Usuario.DoesNotExist:
                messages.success(request, 'Se este email estiver registrado e ativo, você receberá instruções para redefinir a senha.')
                return redirect('login')
    else:
        form = SolicitarResetSenhaForm()

    context = {
        'form': form,
        'title': 'Solicitar Redefinição de Senha'
    }
    return render(request, 'encomendas/auth/solicitar_reset_senha.html', context)


# NO @login_required here
def redefinir_senha(request, token):
    """View para redefinir senha com token"""
    if request.user.is_authenticated:
        messages.info(request, "Você já está logado.")
        # *** CORRECTED REDIRECT ***
        return redirect('root_redirect') # Redirect authenticated users

    try:
        usuario = Usuario.objects.get(token_reset_senha=token, is_active=True)
        if not usuario.token_reset_valido():
            messages.error(request, 'Este link de redefinição de senha expirou ou é inválido. Solicite novamente.')
            return redirect('solicitar_reset_senha')
    except Usuario.DoesNotExist:
        messages.error(request, 'Link de redefinição de senha inválido ou usuário inativo.')
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
        'title': 'Criar Nova Senha',
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
            update_session_auth_hash(request, request.user)
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
    """View para visualizar perfil do usuário"""
    context = {
        'usuario': request.user,
        'title': 'Meu Perfil'
    }
    return render(request, 'encomendas/auth/perfil.html', context)


# ==================================
# Views de Equipes
# ==================================

@login_required(login_url='login')
def listar_equipes(request):
    """View para listar equipes do usuário e convites pendentes"""
    user_membros = MembroEquipe.objects.filter(usuario=request.user).select_related('equipe').order_by('equipe__nome')
    equipes_com_papeis = []
    for membro_info in user_membros:
        equipe = membro_info.equipe
        equipe.meu_papel = membro_info.papel
        equipes_com_papeis.append(equipe)

    equipes_administradas = request.user.equipes_administradas.order_by('nome')
    convites_pendentes = ConviteEquipe.objects.filter(
        email__iexact=request.user.email,
        status='pendente'
    ).select_related('equipe', 'criado_por').order_by('-data_criacao')

    context = {
        'equipes': equipes_com_papeis,
        'equipes_administradas': equipes_administradas,
        'convites_pendentes': convites_pendentes,
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
            equipe.adicionar_membro(request.user, papel='administrador')
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
    """View para gerenciar uma equipe (membros e convites)"""
    equipe = get_object_or_404(Equipe, id=equipe_id)
    membro_atual = equipe.get_membro(request.user)
    if not membro_atual or membro_atual.papel not in ['administrador', 'gerente']:
        messages.error(request, 'Você não tem permissão para gerenciar esta equipe.')
        return redirect('listar_equipes')

    membros = MembroEquipe.objects.filter(equipe=equipe).select_related('usuario').order_by('usuario__nome_completo')
    convites = ConviteEquipe.objects.filter(equipe=equipe, status='pendente').select_related('criado_por').order_by('-data_criacao')

    papel_forms = {
        membro.usuario.id: AlterarPapelForm(initial={'papel': membro.papel})
        for membro in membros if membro.usuario != request.user and membro.usuario != equipe.administrador
     }

    context = {
        'equipe': equipe,
        'membros': membros,
        'convites': convites,
        'title': f'Gerenciar Equipe: {equipe.nome}',
        'papel_forms': papel_forms,
        'PAPEIS_MEMBRO': MembroEquipe.PAPEL_CHOICES,
        'pode_gerenciar': True,
        'is_admin_principal': equipe.eh_administrador(request.user),
    }
    return render(request, 'encomendas/equipes/gerenciar_equipe.html', context)


@login_required(login_url='login')
def convidar_membro(request, equipe_id):
    """View para convidar membro para equipe (Admin/Gerente only)"""
    equipe = get_object_or_404(Equipe, id=equipe_id)
    if not equipe.pode_gerenciar(request.user):
        messages.error(request, 'Você não tem permissão para convidar membros para esta equipe.')
        return redirect('listar_equipes')

    if request.method == 'POST':
        form = ConvidarMembroForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            papel = form.cleaned_data['papel']

            if papel == 'administrador' and not equipe.eh_administrador(request.user):
                 messages.error(request, "Apenas o administrador principal pode convidar outros administradores.")
                 context = {'form': form, 'equipe': equipe, 'title': f'Convidar Membro - {equipe.nome}'}
                 return render(request, 'encomendas/equipes/convidar_membro.html', context)

            try:
                usuario_existente = Usuario.objects.get(email__iexact=email)
                if equipe.eh_membro(usuario_existente):
                    messages.warning(request, f'{usuario_existente.nome_completo or email} já é membro desta equipe.')
                    return redirect('gerenciar_equipe', equipe_id=equipe.id)
            except Usuario.DoesNotExist:
                pass

            if ConviteEquipe.objects.filter(equipe=equipe, email__iexact=email, status='pendente').exists():
                messages.warning(request, f'Já existe um convite pendente para {email} nesta equipe.')
                return redirect('gerenciar_equipe', equipe_id=equipe.id)

            dias_expiracao = getattr(settings, 'CONVITE_EXPIRACAO_DIAS', 7)
            data_expiracao = timezone.now() + timedelta(days=dias_expiracao)

            convite = ConviteEquipe.objects.create(
                equipe=equipe,
                email=email,
                papel=papel,
                criado_por=request.user,
                data_expiracao=data_expiracao
            )

            # Check if function exists before calling
            if callable(globals().get('enviar_email_convite_equipe')):
                enviar_email_convite_equipe(request, convite)

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
@require_http_methods(["POST"])
def alterar_papel_membro(request, equipe_id, membro_id):
    """View para promover/rebaixar membro (Admin/Gerente only)."""
    equipe = get_object_or_404(Equipe, id=equipe_id)
    membro_alvo = get_object_or_404(MembroEquipe, equipe=equipe, usuario_id=membro_id)

    if not equipe.pode_gerenciar(request.user):
        messages.error(request, "Você não tem permissão para alterar papéis nesta equipe.")
        return redirect('gerenciar_equipe', equipe_id=equipe.id)

    if membro_alvo.usuario == request.user:
         messages.error(request, "Você não pode alterar seu próprio papel aqui.")
         return redirect('gerenciar_equipe', equipe_id=equipe.id)
    if membro_alvo.usuario == equipe.administrador:
         messages.error(request, "Não é possível alterar o papel do administrador principal da equipe.")
         return redirect('gerenciar_equipe', equipe_id=equipe.id)

    form = AlterarPapelForm(request.POST)
    if form.is_valid():
        novo_papel = form.cleaned_data['papel']

        if novo_papel == 'administrador' and not equipe.eh_administrador(request.user):
            messages.error(request, "Apenas o administrador principal pode definir outros administradores.")
            return redirect('gerenciar_equipe', equipe_id=equipe.id)

        if membro_alvo.papel != novo_papel:
            membro_alvo.papel = novo_papel
            membro_alvo.save(update_fields=['papel', 'data_atualizacao'])
            messages.success(request, f"Papel de {membro_alvo.usuario.nome_completo} alterado para {membro_alvo.get_papel_display()}.")
        else:
            messages.info(request, f"{membro_alvo.usuario.nome_completo} já possui o papel de {membro_alvo.get_papel_display()}.")
    else:
        messages.error(request, "Seleção de papel inválida.")

    return redirect('gerenciar_equipe', equipe_id=equipe.id)


@login_required(login_url='login')
def remover_membro(request, equipe_id, membro_id):
    """View para remover/expulsar membro de equipe (Admin/Gerente only)."""
    equipe = get_object_or_404(Equipe, id=equipe_id)
    membro_alvo = get_object_or_404(MembroEquipe, equipe=equipe, usuario_id=membro_id)

    if not equipe.pode_gerenciar(request.user):
        messages.error(request, 'Você não tem permissão para remover membros desta equipe.')
        return redirect('gerenciar_equipe', equipe_id=equipe.id)

    if membro_alvo.usuario == request.user:
        messages.error(request, "Você não pode remover a si mesmo. Use a opção 'Sair da Equipe'.")
        return redirect('gerenciar_equipe', equipe_id=equipe.id)
    if membro_alvo.usuario == equipe.administrador:
         messages.error(request, "O administrador principal não pode ser removido da equipe.")
         return redirect('gerenciar_equipe', equipe_id=equipe.id)

    if request.method == 'POST':
        nome_membro = membro_alvo.usuario.nome_completo
        membro_alvo.delete()
        messages.success(request, f'{nome_membro} foi removido da equipe "{equipe.nome}".')
        return redirect('gerenciar_equipe', equipe_id=equipe.id)

    context = {
        'membro': membro_alvo,
        'equipe': equipe,
        'title': f'Confirmar Remoção de {membro_alvo.usuario.nome_completo}'
    }
    return render(request, 'encomendas/equipes/remover_membro.html', context)


@login_required(login_url='login')
@require_http_methods(["POST"])
def sair_equipe(request, equipe_id):
    """View para um membro sair da equipe."""
    equipe = get_object_or_404(Equipe, id=equipe_id)
    membro = equipe.get_membro(request.user)

    if not membro:
        messages.error(request, "Você não é membro desta equipe.")
        return redirect('listar_equipes')

    if equipe.eh_administrador(request.user):
        num_outros_admins = MembroEquipe.objects.filter(
            equipe=equipe,
            papel='administrador'
        ).exclude(usuario=request.user).count()

        if num_outros_admins == 0:
            messages.error(request, "Você é o único administrador. Transfira a administração (promova outro membro) antes de sair.")
            return redirect('gerenciar_equipe', equipe_id=equipe.id)

    nome_equipe = equipe.nome
    membro.delete()
    messages.success(request, f'Você saiu da equipe "{nome_equipe}".')
    return redirect('listar_equipes')


@login_required(login_url='login')
@require_http_methods(["POST"])
def aceitar_convite(request, convite_id):
    """View para aceitar convite de equipe"""
    convite = get_object_or_404(ConviteEquipe, id=convite_id, email__iexact=request.user.email)

    if not convite.eh_valido():
        messages.error(request, 'Este convite expirou ou não é mais válido.')
        if convite.status == 'pendente':
            convite.status = 'expirado'
            convite.save(update_fields=['status'])
        return redirect('listar_equipes')

    if convite.equipe.eh_membro(request.user):
        messages.warning(request, f'Você já é membro da equipe "{convite.equipe.nome}".')
        convite.status = 'aceito' # Or 'redundante'
        convite.data_resposta = timezone.now()
        convite.save(update_fields=['status', 'data_resposta'])
        return redirect('listar_equipes')


    if convite.aceitar(request.user):
        messages.success(request, f'Você foi adicionado à equipe "{convite.equipe.nome}" como {convite.get_papel_display()}.')
        return redirect('dashboard_equipe', equipe_id=convite.equipe.id)
    else:
         messages.error(request, 'Não foi possível aceitar o convite. Verifique se o convite ainda é válido.')
         return redirect('listar_equipes')


@login_required(login_url='login')
@require_http_methods(["POST"])
def rejeitar_convite(request, convite_id):
    """View para rejeitar convite de equipe"""
    convite = get_object_or_404(ConviteEquipe, id=convite_id, email__iexact=request.user.email)

    if convite.status != 'pendente':
        messages.warning(request, f'Este convite já foi respondido ou expirou.')
        return redirect('listar_equipes')

    convite.rejeitar()
    messages.info(request, f'Você rejeitou o convite para a equipe "{convite.equipe.nome}".')
    return redirect('listar_equipes')


@login_required(login_url='login')
def dashboard_equipe(request, equipe_id):
    """View para dashboard de uma equipe específica"""
    try:
        equipe = get_equipe_atual(request, equipe_id)
        if equipe is None: # Should not happen if URL requires ID, but handle defensively
             messages.error(request, "ID da equipe não especificado ou acesso negado.")
             return redirect('listar_equipes')
    except Http404 as e:
        messages.error(request, str(e))
        return redirect('listar_equipes')

    encomendas_da_equipe = Encomenda.objects.filter(equipe=equipe)

    total_encomendas = encomendas_da_equipe.count()
    encomendas_pendentes = encomendas_da_equipe.filter(status__in=['criada', 'cotacao', 'aprovada', 'em_andamento', 'pronta']).count()
    encomendas_entregues = encomendas_da_equipe.filter(status='entregue').count()
    ultimas_encomendas = encomendas_da_equipe.select_related('cliente').order_by('-data_criacao')[:5]

    context = {
        'equipe': equipe,
        'title': f'Dashboard - {equipe.nome}',
        'total_encomendas': total_encomendas,
        'encomendas_pendentes': encomendas_pendentes,
        'encomendas_entregues': encomendas_entregues,
        'ultimas_encomendas': ultimas_encomendas,
    }
    return render(request, 'encomendas/dashboard.html', context)


# ============================================
# Funções auxiliares para envio de email
# ============================================
# NOTE: These functions are defined here for simplicity. In larger projects,
# they might live in a separate 'utils.py' or 'services.py' file.

def enviar_email_boas_vindas(request, usuario):
    """Envia email de boas-vindas ao novo usuário"""
    assunto = 'Bem-vindo ao Sistema de Encomendas!'
    try:
        login_url = request.build_absolute_uri(reverse('login'))
        mensagem = f"""
        Olá {usuario.nome_completo or usuario.username},

        Bem-vindo ao Sistema de Encomendas da Drogaria Benfica!

        Sua conta foi criada com sucesso. Você pode fazer login usando seu email ({usuario.email}) e a senha que definiu.

        Acesse o sistema em: {login_url}

        Atenciosamente,
        Sistema de Encomendas
        """
        send_mail(
            assunto,
            mensagem,
            settings.DEFAULT_FROM_EMAIL,
            [usuario.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f'Erro ao enviar email de boas-vindas para {usuario.email}: {e}')
        messages.warning(request, f"Conta criada, mas houve um erro ao enviar o email de boas-vindas para {usuario.email}.")


def enviar_email_reset_senha(request, usuario, token):
    """Envia email com link para reset de senha"""
    assunto = 'Redefinir sua senha - Sistema de Encomendas'
    try:
        link_reset = request.build_absolute_uri(reverse('redefinir_senha', kwargs={'token': token}))
        mensagem = f"""
        Olá {usuario.nome_completo or usuario.username},

        Recebemos uma solicitação para redefinir a senha da sua conta ({usuario.email}).

        Clique no link abaixo para criar uma nova senha:
        {link_reset}

        Este link é válido por 24 horas. Se expirar, você precisará solicitar a redefinição novamente.

        Se você não solicitou esta redefinição, ignore este email. Sua senha permanecerá a mesma.

        Atenciosamente,
        Sistema de Encomendas
        """
        send_mail(
            assunto,
            mensagem,
            settings.DEFAULT_FROM_EMAIL,
            [usuario.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f'Erro ao enviar email de reset de senha para {usuario.email}: {e}')
        # messages.error(request, "Houve um erro ao tentar enviar o email de redefinição.")


def enviar_email_convite_equipe(request, convite):
    """Envia email de convite para equipe"""
    assunto = f'Convite para a equipe "{convite.equipe.nome}" - Sistema de Encomendas'
    try:
        login_url = request.build_absolute_uri(reverse('login'))
        registro_url = request.build_absolute_uri(reverse('registro'))
        listar_equipes_url = request.build_absolute_uri(reverse('listar_equipes'))

        mensagem = f"""
        Olá,

        {convite.criado_por.nome_completo or convite.criado_por.username} convidou você ({convite.email}) para participar da equipe "{convite.equipe.nome}" no Sistema de Encomendas como {convite.get_papel_display()}.

        Para aceitar ou rejeitar este convite:
        1. Acesse o Sistema de Encomendas: {login_url}
        2. Faça login com o email {convite.email}. Se você não tem uma conta, crie uma usando este email: {registro_url}
        3. Vá para a seção "Minhas Equipes": {listar_equipes_url}
        4. Você encontrará o convite pendente lá com as opções para aceitar ou rejeitar.

        Este convite expira em {convite.data_expiracao.strftime('%d/%m/%Y às %H:%M')}.

        Atenciosamente,
        Sistema de Encomendas
        """
        send_mail(
            assunto,
            mensagem,
            settings.DEFAULT_FROM_EMAIL,
            [convite.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f'Erro ao enviar email de convite para {convite.email}: {e}')
        messages.warning(request, f"Convite salvo, mas houve um erro ao enviar o email para {convite.email}.")