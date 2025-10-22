# encomendas/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404 # Added Http404
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Value
from django.db.models.functions import Coalesce
from django.template.loader import get_template
from django.utils import timezone
from django.contrib.auth.decorators import login_required # Import login_required
from django.urls import reverse # Import reverse

# Make sure all models are imported, including team-related ones if needed indirectly
from .models import (
    Encomenda, Cliente, Produto, Fornecedor, ItemEncomenda, Entrega,
    Equipe, MembroEquipe # Import team models
)
from .forms import (
    EncomendaForm, ItemEncomendaFormSet, EntregaForm, ClienteForm,
    ProdutoForm, FornecedorForm, FiltroEncomendaForm
)
from decimal import Decimal

# Helper function to get the current team (you might improve this logic)
def get_equipe_atual(request, equipe_id=None):
    """
    Determines the current team context.
    Prioritizes equipe_id from URL, then maybe session, then user's first team.
    Raises Http404 if no team context can be found or user is not a member.
    """
    if not request.user.is_authenticated:
        # Redirect anonymous users to login (or handle as appropriate)
        # This shouldn't typically be hit if views are decorated with @login_required
        raise Http404("Usuário não autenticado.")

    if equipe_id:
        try:
            # Ensure the user is actually a member of the team they are accessing
            equipe = request.user.equipes.get(id=equipe_id)
            # Optionally store in session for persistence across requests
            # request.session['equipe_id_atual'] = str(equipe.id)
            return equipe
        except Equipe.DoesNotExist:
            raise Http404("Equipe não encontrada ou você não é membro.")

    # Optional: Check session for a previously selected team
    # session_equipe_id = request.session.get('equipe_id_atual')
    # if session_equipe_id:
    #     try:
    #         equipe = request.user.equipes.get(id=session_equipe_id)
    #         return equipe
    #     except Equipe.DoesNotExist:
    #         del request.session['equipe_id_atual'] # Clean up invalid session data

    # Fallback: If no ID provided and nothing in session, maybe default?
    # Or raise error / redirect to team selection
    user_equipes = request.user.equipes.all()
    if user_equipes.exists():
         # Maybe default to the first one if only one exists? Or always require selection?
         # For now, return None to indicate no specific context was determined here
         return None
    else:
        # User is authenticated but has no teams
        raise Http404("Você não pertence a nenhuma equipe.")


@login_required(login_url='login')
def dashboard(request):
    """
    Main entry point after login. Redirects to team selection or first team dashboard.
    """
    user_equipes = request.user.equipes.all().order_by('nome') # Order for consistency
    if not user_equipes:
        # User is not in any team, show a specific template or message
        return render(request, 'encomendas/dashboard_sem_equipe.html')
    # elif user_equipes.count() == 1:
        # If only one team, go directly to its dashboard
        # primeira_equipe = user_equipes.first()
        # return redirect('dashboard_equipe', equipe_id=primeira_equipe.id)
    else:
        # If multiple teams, maybe redirect to team list to choose?
        # For now, redirecting to the first team's dashboard.
        primeira_equipe = user_equipes.first()
        return redirect('dashboard_equipe', equipe_id=primeira_equipe.id)


@login_required(login_url='login')
def encomenda_list(request):
    """Lista encomendas based on user's teams, with filters"""
    user_equipes = request.user.equipes.all()
    if not user_equipes:
         messages.info(request, "Você precisa fazer parte de uma equipe para ver encomendas.")
         filtro_form = FiltroEncomendaForm() # Pass empty form
         # Adjust queryset for Cliente in the form if needed
         # filtro_form.fields['cliente'].queryset = Cliente.objects.none() # Or filter by teams if clients are team-specific
         return render(request, 'encomendas/encomenda_list.html', {'page_obj': None, 'filtro_form': filtro_form, 'equipes_usuario': None})

    # Base queryset: encomendas from teams the user is in
    encomendas_list = Encomenda.objects.filter(equipe__in=user_equipes).select_related('cliente', 'equipe').order_by('-numero_encomenda')

    # Initialize form - Pass request.GET to populate filters
    filtro_form = FiltroEncomendaForm(request.GET)
    # If clients/products/etc. become team-specific, adjust form querysets here
    # filtro_form.fields['cliente'].queryset = Cliente.objects.filter(equipe__in=user_equipes) # Example

    current_status = request.GET.get('status')
    current_cliente_id = request.GET.get('cliente')
    current_search = request.GET.get('search')
    current_equipe_id = request.GET.get('equipe') # Allow filtering by specific team

    # Apply filters
    if current_status:
        encomendas_list = encomendas_list.filter(status=current_status)

    if current_cliente_id:
        encomendas_list = encomendas_list.filter(cliente_id=current_cliente_id)

    if current_equipe_id:
         # Ensure the selected team is one the user belongs to
         if user_equipes.filter(id=current_equipe_id).exists():
             encomendas_list = encomendas_list.filter(equipe_id=current_equipe_id)
         else:
             # Handle invalid team selection (e.g., show error or ignore filter)
             messages.warning(request, "Equipe selecionada inválida.")
             encomendas_list = Encomenda.objects.none() # Show no results for invalid team


    if current_search:
        encomendas_list = encomendas_list.filter(
            Q(numero_encomenda__icontains=current_search) |
            Q(cliente__nome__icontains=current_search) |
            Q(cliente__codigo__icontains=current_search) |
            Q(itens__produto__nome__icontains=current_search) |
            Q(itens__produto__codigo__icontains=current_search) |
            Q(responsavel_criacao__icontains=current_search) |
            Q(observacoes__icontains=current_search) |
            Q(equipe__nome__icontains=current_search) # Search by team name
        ).distinct()

    # --- Aggregation and Pagination ---
    total_geral_filtrado = encomendas_list.count()
    total_pendentes_filtrado = encomendas_list.filter(status__in=['criada', 'cotacao', 'aprovada', 'em_andamento', 'pronta']).count()
    total_entregues_filtrado = encomendas_list.filter(status='entregue').count()
    valor_total_filtrado = encomendas_list.aggregate(
        total_valor=Coalesce(Sum('valor_total'), Value(Decimal('0.00')))
    )['total_valor']

    paginator = Paginator(encomendas_list, 20) # Items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # --- Prepare context ---
    clientes = Cliente.objects.all().order_by('nome') # Assuming global clients for filter dropdown
    status_choices = Encomenda.STATUS_CHOICES
    equipes_usuario = user_equipes.order_by('nome') # For team filter dropdown

    # Get selected client object for display/logic if ID is present
    current_cliente = None
    if current_cliente_id:
         try:
             current_cliente = Cliente.objects.get(id=current_cliente_id)
         except Cliente.DoesNotExist:
             pass # ID was invalid

    context = {
        'page_obj': page_obj,
        'filtro_form': filtro_form, # Pass the bound form
        'clientes': clientes, # For dropdown
        'status_choices': status_choices, # For dropdown
        'current_status': current_status,
        'current_cliente_id': current_cliente_id, # Keep ID for comparison in template
        'current_cliente': current_cliente, # Pass object if found
        'current_search': current_search,
        'current_equipe_id': current_equipe_id, # Pass selected team ID
        'total_geral_filtrado': total_geral_filtrado,
        'total_pendentes_filtrado': total_pendentes_filtrado,
        'total_entregues_filtrado': total_entregues_filtrado,
        'valor_total_filtrado': valor_total_filtrado,
        'equipes_usuario': equipes_usuario, # For team filter dropdown
    }
    return render(request, 'encomendas/encomenda_list.html', context)


@login_required(login_url='login')
def encomenda_detail(request, pk):
    """Detalhes de uma encomenda, ensuring user is part of the team"""
    user_equipes_ids = request.user.equipes.values_list('id', flat=True)
    # Fetch related objects efficiently
    encomenda = get_object_or_404(
        Encomenda.objects.select_related('cliente', 'equipe'),
        pk=pk,
        equipe_id__in=user_equipes_ids
    )

    itens = encomenda.itens.select_related('produto', 'fornecedor').all()

    # Fetch delivery using related_name (avoids try/except)
    entrega = getattr(encomenda, 'entrega', None)

    context = {
        'encomenda': encomenda,
        'itens': itens,
        'entrega': entrega,
        'equipe': encomenda.equipe # Pass team context
    }
    return render(request, 'encomendas/encomenda_detail.html', context)


@login_required(login_url='login')
def encomenda_create(request, equipe_id=None): # Allow optional team ID from URL
    """Criar nova encomenda associada a uma equipe"""
    user_equipes = request.user.equipes.all()
    if not user_equipes:
        messages.error(request, "Você precisa pertencer a pelo menos uma equipe para criar encomendas.")
        return redirect('listar_equipes')

    # Determine the team for the new encomenda
    equipe_atual = None
    if equipe_id: # Prioritize URL parameter
        equipe_atual = get_object_or_404(user_equipes, id=equipe_id)
    elif user_equipes.count() == 1: # Default if user is in only one team
         equipe_atual = user_equipes.first()
    # Else: If multiple teams and no ID, redirect to a selection page or show selector in form

    if not equipe_atual:
         messages.warning(request, "Por favor, selecione uma equipe para criar a encomenda.")
         # Ideally redirect to a page where they can choose, or modify this form
         return redirect('listar_equipes')


    if request.method == 'POST':
        form = EncomendaForm(request.POST)
        # Ensure correct prefix and pass initial data if needed
        formset = ItemEncomendaFormSet(request.POST, prefix='itens')

        if form.is_valid() and formset.is_valid():
            encomenda = form.save(commit=False)
            encomenda.equipe = equipe_atual # Associate with the selected team
            # Set creator automatically based on logged-in user
            encomenda.responsavel_criacao = request.user.nome_completo or request.user.username
            encomenda.save() # Save encomenda first to get PK

            # Save items associated with the saved encomenda
            instances = formset.save(commit=False)
            total_items_value = Decimal('0.00')
            items_to_save = []
            for instance in instances:
                instance.encomenda = encomenda
                # Calculate item total before potential save
                if instance.quantidade is not None and instance.preco_cotado is not None:
                    instance.valor_total = instance.quantidade * instance.preco_cotado
                    total_items_value += instance.valor_total
                else:
                    instance.valor_total = Decimal('0.00')
                items_to_save.append(instance)

            # Bulk create items for efficiency if many items
            if items_to_save:
                ItemEncomenda.objects.bulk_create(items_to_save)
            # formset.save_m2m() # Only needed if formset has M2M fields

            # Update encomenda total based on calculated item totals
            encomenda.valor_total = total_items_value
            encomenda.save(update_fields=['valor_total'])

            messages.success(request, f'Encomenda #{encomenda.numero_encomenda} criada com sucesso para a equipe {equipe_atual.nome}!')
            return redirect('encomenda_detail', pk=encomenda.pk)
        else:
            messages.error(request, 'Erro ao criar encomenda. Verifique os campos abaixo.')
            # Errors will be displayed by the template
    else:
        # Pre-fill responsible field
        initial_encomenda_data = {'responsavel_criacao': request.user.nome_completo or request.user.username}
        form = EncomendaForm(initial=initial_encomenda_data)
        formset = ItemEncomendaFormSet(prefix='itens')

    context = {
        'form': form,
        'formset': formset,
        'title': f'Nova Encomenda (Equipe: {equipe_atual.nome})',
        'equipe': equipe_atual, # Pass team context
    }
    return render(request, 'encomendas/encomenda_form.html', context)


@login_required(login_url='login')
def encomenda_edit(request, pk):
    """Editar encomenda existente, checking team membership"""
    user_equipes_ids = request.user.equipes.values_list('id', flat=True)
    encomenda = get_object_or_404(Encomenda, pk=pk, equipe_id__in=user_equipes_ids)

    if request.method == 'POST':
        form = EncomendaForm(request.POST, instance=encomenda)
        formset = ItemEncomendaFormSet(request.POST, instance=encomenda, prefix='itens')

        if form.is_valid() and formset.is_valid():
            encomenda = form.save() # Save encomenda changes

            # Save changes to items (handles creates, updates, deletes)
            instances = formset.save(commit=False)
            total_items_value = Decimal('0.00')
            items_to_update = []
            items_to_create = []

            for instance in instances:
                # Calculate value before saving
                if instance.quantidade is not None and instance.preco_cotado is not None:
                     instance.valor_total = instance.quantidade * instance.preco_cotado
                     total_items_value += instance.valor_total
                else:
                     instance.valor_total = Decimal('0.00')

                if instance.pk:
                     items_to_update.append(instance)
                else: # New item added during edit
                     instance.encomenda = encomenda # Associate with parent
                     items_to_create.append(instance)

            # Handle deletions marked by the formset
            for form_in_formset in formset.deleted_forms:
                if form_in_formset.instance.pk:
                     form_in_formset.instance.delete()
                     # Value already excluded as it wasn't in `instances`

            # Save updated items
            if items_to_update:
                ItemEncomenda.objects.bulk_update(items_to_update, ['produto', 'fornecedor', 'quantidade', 'preco_cotado', 'valor_total', 'observacoes'])
            # Save newly created items
            if items_to_create:
                ItemEncomenda.objects.bulk_create(items_to_create)

            # formset.save_m2m() # Only if formset uses M2M

            # Final update of encomenda total
            encomenda.valor_total = total_items_value
            encomenda.save(update_fields=['valor_total'])

            messages.success(request, f'Encomenda #{encomenda.numero_encomenda} atualizada com sucesso!')
            return redirect('encomenda_detail', pk=encomenda.pk)
        else:
            messages.error(request, 'Erro ao atualizar encomenda. Verifique os campos abaixo.')
    else:
        form = EncomendaForm(instance=encomenda)
        formset = ItemEncomendaFormSet(instance=encomenda, prefix='itens')

    context = {
        'form': form,
        'formset': formset,
        'encomenda': encomenda,
        'title': f'Editar Encomenda #{encomenda.numero_encomenda} (Equipe: {encomenda.equipe.nome})',
        'equipe': encomenda.equipe,
    }
    return render(request, 'encomendas/encomenda_form.html', context)


@login_required(login_url='login')
def encomenda_delete(request, pk):
    """Excluir encomenda, checking team membership"""
    user_equipes_ids = request.user.equipes.values_list('id', flat=True)
    encomenda = get_object_or_404(Encomenda, pk=pk, equipe_id__in=user_equipes_ids)
    equipe_id_redirect = encomenda.equipe.id if encomenda.equipe else None

    if request.method == 'POST':
        numero = encomenda.numero_encomenda
        encomenda.delete()
        messages.success(request, f'Encomenda #{numero} excluída com sucesso!')
        # Redirect to the team dashboard or list after deletion
        if equipe_id_redirect:
            return redirect('dashboard_equipe', equipe_id=equipe_id_redirect)
        else:
            return redirect('encomenda_list') # Fallback if team was somehow null

    context = {
        'encomenda': encomenda,
        'equipe': encomenda.equipe, # Pass team for context in template
        'title': f'Excluir Encomenda #{encomenda.numero_encomenda}' # Add title
        }
    return render(request, 'encomendas/encomenda_confirm_delete.html', context)


# --- Entrega Views (ensure encomenda access check) ---
@login_required(login_url='login')
def entrega_create(request, encomenda_pk):
    """Criar entrega, checking team membership for the encomenda"""
    user_equipes_ids = request.user.equipes.values_list('id', flat=True)
    encomenda = get_object_or_404(Encomenda, pk=encomenda_pk, equipe_id__in=user_equipes_ids)

    # Check if delivery already exists using related_name
    if hasattr(encomenda, 'entrega') and encomenda.entrega is not None:
         messages.warning(request, f"Encomenda #{encomenda.numero_encomenda} já possui informações de entrega.")
         return redirect('entrega_edit', pk=encomenda.entrega.pk)

    if request.method == 'POST':
        form = EntregaForm(request.POST)
        if form.is_valid():
            entrega = form.save(commit=False)
            entrega.encomenda = encomenda
            # Ensure data_prevista is set if data_entrega is provided (form field mapping)
            entrega.data_prevista = form.cleaned_data.get('data_entrega') # Link form field to model field
            entrega.save()
            messages.success(request, f'Informações de entrega para encomenda #{encomenda.numero_encomenda} criadas!')
            return redirect('encomenda_detail', pk=encomenda.pk)
        else:
             messages.error(request, "Erro ao salvar informações de entrega. Verifique os campos.")
    else:
        # Pre-fill responsible field and maybe default date
        initial_data = {
            'responsavel_entrega': request.user.nome_completo or request.user.username,
            'data_entrega': timezone.now().date() # Default to today
            }
        form = EntregaForm(initial=initial_data)

    context = {
        'form': form,
        'encomenda': encomenda,
        'equipe': encomenda.equipe,
        'title': f'Programar Entrega - Encomenda #{encomenda.numero_encomenda}',
    }
    return render(request, 'encomendas/entrega_form.html', context)

@login_required(login_url='login')
def entrega_edit(request, pk):
    """Editar entrega, checking team membership via the encomenda"""
    # Select related encomenda and equipe for efficiency and permission check
    entrega = get_object_or_404(Entrega.objects.select_related('encomenda__equipe'), pk=pk)
    encomenda = entrega.encomenda

    # Check if user belongs to the encomenda's team
    if not request.user.equipes.filter(id=encomenda.equipe_id).exists():
         messages.error(request, "Você não tem permissão para editar esta entrega.")
         return redirect('listar_equipes') # Redirect to team list

    if request.method == 'POST':
        form = EntregaForm(request.POST, instance=entrega)
        if form.is_valid():
            entrega = form.save(commit=False)
            # Link form fields back to model fields if names differ
            entrega.data_prevista = form.cleaned_data.get('data_entrega')
            # Handle DateTime for data_realizada based on form's Date and Time fields
            data_realizada_form = form.cleaned_data.get('data_entrega_realizada')
            hora_realizada_form = form.cleaned_data.get('hora_entrega')
            if data_realizada_form and hora_realizada_form:
                 entrega.data_realizada = timezone.make_aware(
                     timezone.datetime.combine(data_realizada_form, hora_realizada_form)
                 )
            elif data_realizada_form: # If only date is provided, set time to midnight (or null?)
                 entrega.data_realizada = timezone.make_aware(
                     timezone.datetime.combine(data_realizada_form, timezone.datetime.min.time())
                 )
            else:
                 entrega.data_realizada = None # Clear if date is cleared

            entrega.save()

            # Update encomenda status if marked as delivered
            if entrega.data_realizada and encomenda.status != 'entregue':
                encomenda.status = 'entregue'
                encomenda.save(update_fields=['status'])
                messages.info(request, f'Status da Encomenda #{encomenda.numero_encomenda} atualizado para Entregue.')
            # Optional: Revert status if date is cleared?
            elif not entrega.data_realizada and encomenda.status == 'entregue':
                 # Revert logic might be complex (what was the previous status?)
                 # Maybe just leave it as delivered or require manual change.
                 pass


            messages.success(request, 'Informações de entrega atualizadas com sucesso!')
            return redirect('encomenda_detail', pk=encomenda.pk)
        else:
             messages.error(request, "Erro ao atualizar informações de entrega. Verifique os campos.")

    else:
        # Prepare initial data for form based on model instance
        initial_data = {
            'data_entrega': entrega.data_prevista or entrega.data_entrega, # Use data_prevista if available
            'data_entrega_realizada': entrega.data_realizada.date() if entrega.data_realizada else entrega.data_entrega_realizada, # Use date part
            'hora_entrega': entrega.data_realizada.time() if entrega.data_realizada else entrega.hora_entrega # Use time part
        }
        form = EntregaForm(instance=entrega, initial=initial_data)

    context = {
        'form': form,
        'entrega': entrega,
        'encomenda': encomenda,
        'equipe': encomenda.equipe,
        'title': f'Editar Entrega - Encomenda #{encomenda.numero_encomenda}',
    }
    return render(request, 'encomendas/entrega_form.html', context)


# --- Cliente, Produto, Fornecedor Views (Assuming Global) ---
# Add @login_required to protect these views

@login_required(login_url='login')
def cliente_list(request):
    """Lista de clientes (Global)"""
    clientes = Cliente.objects.all().order_by('nome')
    search = request.GET.get('search')
    if search:
        clientes = clientes.filter(
            Q(nome__icontains=search) | Q(codigo__icontains=search) |
            Q(endereco__icontains=search) | Q(bairro__icontains=search) |
            Q(telefone__icontains=search)
        ).distinct()

    paginator = Paginator(clientes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj, 'current_search': search}
    return render(request, 'encomendas/cliente_list.html', context)

@login_required(login_url='login')
def cliente_create(request):
    """Criar novo cliente (Global)"""
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f'Cliente {cliente.nome} criado com sucesso!')
            return redirect('cliente_list')
        else:
             messages.error(request, "Erro ao criar cliente. Verifique os campos.")
    else:
        form = ClienteForm()
    context = {'form': form, 'title': 'Novo Cliente'}
    return render(request, 'encomendas/cliente_form.html', context)

@login_required(login_url='login')
def produto_list(request):
    """Lista de produtos (Global)"""
    produtos = Produto.objects.all().order_by('nome')
    search = request.GET.get('search')
    if search:
        produtos = produtos.filter(
            Q(nome__icontains=search) | Q(codigo__icontains=search) |
            Q(categoria__icontains=search) | Q(descricao__icontains=search)
        ).distinct()

    paginator = Paginator(produtos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj, 'current_search': search}
    return render(request, 'encomendas/produto_list.html', context)

@login_required(login_url='login')
def produto_create(request):
    """Criar novo produto (Global)"""
    if request.method == 'POST':
        form = ProdutoForm(request.POST)
        if form.is_valid():
            produto = form.save()
            messages.success(request, f'Produto {produto.nome} criado com sucesso!')
            return redirect('produto_list')
        else:
            messages.error(request, "Erro ao criar produto. Verifique os campos.")
    else:
        form = ProdutoForm()
    context = {'form': form, 'title': 'Novo Produto'}
    return render(request, 'encomendas/produto_form.html', context)

@login_required(login_url='login')
def fornecedor_list(request):
    """Lista de fornecedores (Global)"""
    fornecedores = Fornecedor.objects.all().order_by('nome')
    search = request.GET.get('search')
    if search:
        fornecedores = fornecedores.filter(
            Q(nome__icontains=search) | Q(codigo__icontains=search) |
            Q(contato__icontains=search) | Q(email__icontains=search) |
            Q(telefone__icontains=search)
        ).distinct()

    paginator = Paginator(fornecedores, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj, 'current_search': search}
    return render(request, 'encomendas/fornecedor_list.html', context)

@login_required(login_url='login')
def fornecedor_create(request):
    """Criar novo fornecedor (Global)"""
    if request.method == 'POST':
        form = FornecedorForm(request.POST)
        if form.is_valid():
            fornecedor = form.save()
            messages.success(request, f'Fornecedor {fornecedor.nome} criado com sucesso!')
            return redirect('fornecedor_list')
        else:
             messages.error(request, "Erro ao criar fornecedor. Verifique os campos.")
    else:
        form = FornecedorForm()
    context = {'form': form, 'title': 'Novo Fornecedor'}
    return render(request, 'encomendas/fornecedor_form.html', context)


# --- API Views ---
@login_required(login_url='login') # Protect API endpoint
@require_http_methods(["GET"])
def api_produto_info(request, produto_id):
    """Retorna informações do produto via AJAX (Global product assumed)"""
    # No team check needed if products are global
    try:
        produto = Produto.objects.get(id=produto_id)
        data = {
            'nome': produto.nome,
            'codigo': produto.codigo,
            'preco_base': str(produto.preco_base), # Ensure string conversion
        }
        return JsonResponse(data)
    except Produto.DoesNotExist:
        return JsonResponse({'error': 'Produto não encontrado'}, status=404)

@login_required(login_url='login') # Protect API endpoint
@require_http_methods(["POST"])
def api_update_status(request, encomenda_pk):
    """Atualiza status da encomenda via AJAX, checking team membership"""
    user_equipes_ids = request.user.equipes.values_list('id', flat=True)
    encomenda = get_object_or_404(Encomenda, pk=encomenda_pk, equipe_id__in=user_equipes_ids)

    new_status = request.POST.get('status')

    # Validate status choice
    valid_statuses = [choice[0] for choice in Encomenda.STATUS_CHOICES]
    if new_status in valid_statuses:
        old_status_display = encomenda.get_status_display()
        encomenda.status = new_status
        encomenda.save(update_fields=['status'])
        new_status_display = encomenda.get_status_display() # Get display name after save
        return JsonResponse({
            'success': True,
            'status_code': new_status,
            'status_display': new_status_display,
            'message': f'Status alterado de "{old_status_display}" para "{new_status_display}"'
        })
    else:
        return JsonResponse({'error': 'Status inválido'}, status=400)


@login_required(login_url='login') # Protect API endpoint
def encomenda_pdf(request, pk):
    """Gerar PDF da encomenda, checking team membership"""
    user_equipes_ids = request.user.equipes.values_list('id', flat=True)
    encomenda = get_object_or_404(Encomenda.objects.select_related('cliente', 'equipe'), pk=pk, equipe_id__in=user_equipes_ids)

    entrega = getattr(encomenda, 'entrega', None) # Use related_name
    itens = encomenda.itens.select_related('produto', 'fornecedor').all() # Fetch items for PDF

    context = {'encomenda': encomenda, 'entrega': entrega, 'itens': itens}
    template = get_template('encomendas/encomenda_pdf.html')
    html = template.render(context)

    try:
        from weasyprint import HTML
        pdf = HTML(string=html).write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="encomenda_{encomenda.numero_encomenda}.pdf"'
        return response
    except ImportError:
        messages.error(request, 'Erro ao gerar PDF: Biblioteca WeasyPrint não encontrada.')
        return redirect('encomenda_detail', pk=pk)
    except Exception as e:
        messages.error(request, f'Erro inesperado ao gerar PDF: {e}')
        return redirect('encomenda_detail', pk=pk)


@login_required(login_url='login') # Protect action
@require_http_methods(["POST"]) # Make sure this is POST only
def marcar_entrega_realizada(request, pk):
    """Marcar entrega como realizada, checking team membership"""
    # Fetch entrega ensuring user has access via encomenda's team
    user_equipes_ids = request.user.equipes.values_list('id', flat=True)
    entrega = get_object_or_404(Entrega.objects.select_related('encomenda'), pk=pk, encomenda__equipe_id__in=user_equipes_ids)
    encomenda = entrega.encomenda

    # Check if already marked
    if entrega.data_realizada:
        messages.warning(request, f'Entrega da encomenda #{encomenda.numero_encomenda} já está marcada como realizada.')
        return redirect('encomenda_detail', pk=encomenda.pk)

    now = timezone.now()
    entrega.data_realizada = now # Set DateTimeField
    entrega.data_entrega_realizada = now.date() # Set DateField for consistency
    entrega.hora_entrega = now.time() # Set TimeField for consistency

    # Optionally pre-fill 'entregue_por' if empty
    if not entrega.entregue_por:
        entrega.entregue_por = request.user.nome_completo or request.user.username
    entrega.save()

    # Update encomenda status
    if encomenda.status != 'entregue':
        encomenda.status = 'entregue'
        encomenda.save(update_fields=['status'])

    messages.success(request, f'Entrega da encomenda #{encomenda.numero_encomenda} marcada como realizada!')
    return redirect('encomenda_detail', pk=encomenda.pk)


@login_required(login_url='login') # Protect API endpoint
def search_produtos(request):
    """API view for searching products (Global) for Select2."""
    search_term = request.GET.get('q', '')
    # Assuming products are global
    produtos = Produto.objects.filter(
        Q(nome__icontains=search_term) | Q(codigo__icontains=search_term)
    ).order_by('nome')[:20] # Limit results

    results = [{'id': p.id, 'text': f"{p.codigo} - {p.nome}"} for p in produtos]
    return JsonResponse({'results': results})