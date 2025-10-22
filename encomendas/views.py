# encomendas/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
# Import necessary query tools
from django.db.models import Q, Sum, Value, Count, Subquery, OuterRef
from django.db.models.functions import Coalesce
from django.template.loader import get_template
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.forms import modelformset_factory # Keep if needed later

# Make sure all models are imported
from .models import (
    Encomenda, Cliente, Produto, Fornecedor, ItemEncomenda, Entrega,
    Equipe, MembroEquipe, Usuario
)
from .forms import (
    EncomendaForm, ItemEncomendaFormSet, EntregaForm, ClienteForm,
    ProdutoForm, FornecedorForm, FiltroEncomendaForm,
    # Import filter forms
    FiltroClienteForm, FiltroProdutoForm, FiltroFornecedorForm
)
from decimal import Decimal

# --- Helper function to get current team ---
def get_equipe_atual(request, equipe_id=None):
    """
    Determines the current team context for the logged-in user.
    Prioritizes equipe_id from URL.
    Raises Http404 if no team context can be found or user is not a member.
    Returns None if user has multiple teams but no specific ID was provided.
    """
    if not request.user.is_authenticated:
        raise Http404("Usuário não autenticado.")

    user_equipes = request.user.equipes.all() # Get all teams the user is part of

    if equipe_id:
        try:
            # Ensure the user is actually a member of the team they are accessing via URL
            equipe = user_equipes.get(id=equipe_id)
            # Optionally store in session for persistence across requests
            # request.session['equipe_id_atual'] = str(equipe.id)
            return equipe
        except Equipe.DoesNotExist:
            raise Http404("Equipe não encontrada ou você não é membro.")

    # Fallback: If no ID provided
    if user_equipes.count() == 1:
        # If user is only in one team, default to that team
        return user_equipes.first()
    elif user_equipes.count() > 1:
        # User in multiple teams, but no specific one selected via URL
        # Let the view decide how to handle this (e.g., redirect to team list)
        return None
    else:
        # User is authenticated but has no teams
        raise Http404("Você não pertence a nenhuma equipe.")

# --- Dashboard View ---
@login_required(login_url='login')
def dashboard(request):
    """
    Redirects authenticated users to their team list.
    If they have no teams, shows a specific page.
    """
    user_equipes = request.user.equipes.all().order_by('nome')
    if not user_equipes:
        # User is not in any team, show a specific template or message
        return render(request, 'encomendas/dashboard_sem_equipe.html')
    else:
        # Always redirect users with teams to the team list page
        return redirect('listar_equipes')

# --- Encomenda Views ---

@login_required(login_url='login')
def encomenda_list(request):
    """Lists encomendas based on user's teams, with filters for status, client, team, and search."""
    user_equipes = request.user.equipes.all()
    if not user_equipes:
        messages.info(request, "Você precisa fazer parte de uma equipe para ver encomendas.")
        # Pass an empty form, filtering choices won't matter here
        filtro_form = FiltroEncomendaForm(user=request.user)
        return render(request, 'encomendas/encomenda_list.html', {
            'page_obj': None, 'filtro_form': filtro_form,
            'equipes_usuario': None, 'current_equipe': None
        })

    # Base queryset: encomendas from teams the user is in
    encomendas_list = Encomenda.objects.filter(equipe__in=user_equipes).select_related('cliente', 'equipe').order_by('-numero_encomenda')

    # Initialize filter form, passing user to limit choices
    filtro_form = FiltroEncomendaForm(request.GET, user=request.user)

    current_status = request.GET.get('status')
    current_cliente_id = request.GET.get('cliente')
    current_search = request.GET.get('search')
    current_equipe_id = request.GET.get('equipe') # Allow filtering by specific team

    # Filter by selected team if provided
    current_equipe = None
    if current_equipe_id:
        try:
            # Ensure the selected team is one the user belongs to
            current_equipe = user_equipes.get(id=current_equipe_id)
            encomendas_list = encomendas_list.filter(equipe=current_equipe)
        except Equipe.DoesNotExist:
            messages.warning(request, "Equipe selecionada inválida.")
            encomendas_list = Encomenda.objects.none() # Show no results for invalid team

    # Apply other filters
    if current_status:
        encomendas_list = encomendas_list.filter(status=current_status)

    if current_cliente_id:
        # Ensure client belongs to one of user's teams before applying filter
        if Cliente.objects.filter(id=current_cliente_id, equipe__in=user_equipes).exists():
            encomendas_list = encomendas_list.filter(cliente_id=current_cliente_id)

    if current_search:
        encomendas_list = encomendas_list.filter(
            Q(numero_encomenda__icontains=current_search) |
            Q(cliente__nome__icontains=current_search) |
            Q(cliente__codigo__icontains=current_search) |
            # Ensure related items being searched also belong to user's teams' products/fornecedores
            Q(itens__produto__nome__icontains=current_search, itens__produto__equipe__in=user_equipes) |
            Q(itens__produto__codigo__icontains=current_search, itens__produto__equipe__in=user_equipes) |
            Q(responsavel_criacao__icontains=current_search) |
            Q(observacoes__icontains=current_search) |
            Q(equipe__nome__icontains=current_search)
        ).distinct()

    # Aggregation and Pagination (applied to the final filtered list)
    total_geral_filtrado = encomendas_list.count()
    total_pendentes_filtrado = encomendas_list.filter(status__in=['criada', 'cotacao', 'aprovada', 'em_andamento', 'pronta']).count()
    total_entregues_filtrado = encomendas_list.filter(status='entregue').count()
    valor_total_filtrado = encomendas_list.aggregate(
        total_valor=Coalesce(Sum('valor_total'), Value(Decimal('0.00')))
    )['total_valor']

    paginator = Paginator(encomendas_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get selected client object for display/logic if ID is present and valid
    selected_cliente_obj = None
    if current_cliente_id:
         try:
             selected_cliente_obj = Cliente.objects.get(id=current_cliente_id, equipe__in=user_equipes)
         except Cliente.DoesNotExist:
             pass # ID was invalid or client not accessible

    context = {
        'page_obj': page_obj,
        'filtro_form': filtro_form, # Pass the bound form
        'current_status': current_status,
        'current_cliente_id': current_cliente_id,
        'current_cliente': selected_cliente_obj, # Pass object if found
        'current_search': current_search,
        'current_equipe_id': current_equipe_id,
        'current_equipe': current_equipe, # Pass the selected team object
        'total_geral_filtrado': total_geral_filtrado,
        'total_pendentes_filtrado': total_pendentes_filtrado,
        'total_entregues_filtrado': total_entregues_filtrado,
        'valor_total_filtrado': valor_total_filtrado,
        'equipes_usuario': user_equipes.order_by('nome'), # For team filter dropdown
    }
    return render(request, 'encomendas/encomenda_list.html', context)


@login_required(login_url='login')
def encomenda_detail(request, pk):
    """Details of an order, ensuring the user is part of the team."""
    user_equipes_ids = request.user.equipes.values_list('id', flat=True)
    encomenda = get_object_or_404(
        Encomenda.objects.select_related('cliente', 'equipe'),
        pk=pk,
        equipe_id__in=user_equipes_ids # Check team membership
    )

    # Filter items ensuring related product/supplier belong to the order's team
    itens = encomenda.itens.filter(
        produto__equipe=encomenda.equipe,
        fornecedor__equipe=encomenda.equipe
    ).select_related('produto', 'fornecedor').all()

    entrega = getattr(encomenda, 'entrega', None) # Fetch delivery using related_name

    context = {
        'encomenda': encomenda,
        'itens': itens,
        'entrega': entrega,
        'equipe': encomenda.equipe # Pass team context
    }
    return render(request, 'encomendas/encomenda_detail.html', context)


@login_required(login_url='login')
def encomenda_create(request, equipe_id=None):
    """Create a new order associated with a specific team."""
    try:
        # Determine team context, redirecting if ambiguous or no access
        equipe_atual = get_equipe_atual(request, equipe_id)
        if equipe_atual is None:
            messages.warning(request, "Por favor, selecione uma equipe para criar a encomenda.")
            return redirect('listar_equipes')
    except Http404 as e:
        messages.error(request, str(e))
        return redirect('listar_equipes') # Redirect if user has no teams or invalid ID

    if request.method == 'POST':
        # Pass equipe_atual to forms to filter FK choices
        form = EncomendaForm(request.POST, equipe=equipe_atual)
        formset = ItemEncomendaFormSet(request.POST, prefix='itens', form_kwargs={'equipe': equipe_atual})

        if form.is_valid() and formset.is_valid():
            # Double-check client belongs to the correct team
            if form.cleaned_data['cliente'].equipe != equipe_atual:
                 messages.error(request, f"Cliente selecionado não pertence à equipe '{equipe_atual.nome}'.")
                 # Re-render form with error
                 context = {'form': form, 'formset': formset, 'title': f'Nova Encomenda (Equipe: {equipe_atual.nome})', 'equipe': equipe_atual}
                 return render(request, 'encomendas/encomenda_form.html', context)

            encomenda = form.save(commit=False)
            encomenda.equipe = equipe_atual
            encomenda.responsavel_criacao = request.user.nome_completo or request.user.username
            encomenda.save() # Save encomenda first to get PK

            instances = formset.save(commit=False)
            total_items_value = Decimal('0.00')
            items_to_save = []
            valid_items = True
            for instance in instances:
                instance.encomenda = encomenda
                # Ensure selected product/supplier belong to the team
                if instance.produto.equipe != equipe_atual or instance.fornecedor.equipe != equipe_atual:
                     messages.error(request, f"Item inválido: Produto '{instance.produto.nome}' ou Fornecedor '{instance.fornecedor.nome}' não pertence à equipe '{equipe_atual.nome}'.")
                     valid_items = False
                     break # Stop processing further items

                # Calculate item total
                if instance.quantidade is not None and instance.preco_cotado is not None:
                    instance.valor_total = instance.quantidade * instance.preco_cotado
                    total_items_value += instance.valor_total
                else:
                    instance.valor_total = Decimal('0.00')
                items_to_save.append(instance)

            if not valid_items:
                # If an item was invalid, delete the partially created encomenda and re-render form
                encomenda.delete() # Clean up the created Encomenda object
                context = {'form': form, 'formset': formset, 'title': f'Nova Encomenda (Equipe: {equipe_atual.nome})', 'equipe': equipe_atual}
                return render(request, 'encomendas/encomenda_form.html', context)

            # Bulk create items if all were valid
            if items_to_save:
                ItemEncomenda.objects.bulk_create(items_to_save)

            # Update encomenda total based on calculated item totals
            encomenda.valor_total = total_items_value
            encomenda.save(update_fields=['valor_total'])

            messages.success(request, f'Encomenda #{encomenda.numero_encomenda} criada com sucesso para a equipe {equipe_atual.nome}!')
            return redirect('encomenda_detail', pk=encomenda.pk)
        else:
            messages.error(request, 'Erro ao criar encomenda. Verifique os campos abaixo.')
            # Errors will be displayed by the template via form/formset rendering
    else:
        # GET request: Prepare forms with initial data and team context
        initial_encomenda_data = {'responsavel_criacao': request.user.nome_completo or request.user.username}
        form = EncomendaForm(initial=initial_encomenda_data, equipe=equipe_atual)
        formset = ItemEncomendaFormSet(prefix='itens', form_kwargs={'equipe': equipe_atual})

    context = {
        'form': form,
        'formset': formset,
        'title': f'Nova Encomenda (Equipe: {equipe_atual.nome})',
        'equipe': equipe_atual, # Pass team context
    }
    return render(request, 'encomendas/encomenda_form.html', context)


@login_required(login_url='login')
def encomenda_edit(request, pk):
    """Edit an existing order, checking team membership and team consistency."""
    user_equipes_ids = request.user.equipes.values_list('id', flat=True)
    # Ensure user is part of the team the order belongs to
    encomenda = get_object_or_404(Encomenda.objects.select_related('equipe', 'cliente'), pk=pk, equipe_id__in=user_equipes_ids)
    equipe_atual = encomenda.equipe # Team context is fixed for editing

    if request.method == 'POST':
        # Pass instance and team context to forms
        form = EncomendaForm(request.POST, instance=encomenda, equipe=equipe_atual)
        formset = ItemEncomendaFormSet(request.POST, instance=encomenda, prefix='itens', form_kwargs={'equipe': equipe_atual})

        if form.is_valid() and formset.is_valid():
            # Ensure the client wasn't changed to one outside the team
            if form.cleaned_data['cliente'].equipe != equipe_atual:
                 messages.error(request, f"Cliente '{form.cleaned_data['cliente'].nome}' não pertence à equipe '{equipe_atual.nome}'.")
                 # Re-render form with error
                 context = {'form': form, 'formset': formset, 'encomenda': encomenda, 'title': f'Editar Encomenda #{encomenda.numero_encomenda} (Equipe: {equipe_atual.nome})', 'equipe': equipe_atual}
                 return render(request, 'encomendas/encomenda_form.html', context)

            encomenda = form.save() # Save encomenda changes first

            instances = formset.save(commit=False)
            total_items_value = Decimal('0.00')
            items_to_update = []
            items_to_create = []
            valid_items = True

            for instance in instances:
                 # Ensure selected product/supplier belong to the team
                if instance.produto.equipe != equipe_atual or instance.fornecedor.equipe != equipe_atual:
                     messages.error(request, f"Item inválido: Produto '{instance.produto.nome}' ou Fornecedor '{instance.fornecedor.nome}' não pertence à equipe '{equipe_atual.nome}'.")
                     valid_items = False
                     break # Stop processing items

                # Calculate value before saving
                if instance.quantidade is not None and instance.preco_cotado is not None:
                     instance.valor_total = instance.quantidade * instance.preco_cotado
                     total_items_value += instance.valor_total
                else:
                     instance.valor_total = Decimal('0.00')

                if instance.pk: # Existing item
                     items_to_update.append(instance)
                else: # New item added during edit
                     instance.encomenda = encomenda # Associate with parent
                     items_to_create.append(instance)

            if not valid_items:
                # Re-render form if an item was invalid
                context = {'form': form, 'formset': formset, 'encomenda': encomenda, 'title': f'Editar Encomenda #{encomenda.numero_encomenda} (Equipe: {equipe_atual.nome})', 'equipe': equipe_atual}
                return render(request, 'encomendas/encomenda_form.html', context)

            # Handle deletions marked by the formset
            for form_in_formset in formset.deleted_forms:
                if form_in_formset.instance.pk:
                     form_in_formset.instance.delete()

            # Save updated items
            if items_to_update:
                ItemEncomenda.objects.bulk_update(items_to_update, ['produto', 'fornecedor', 'quantidade', 'preco_cotado', 'valor_total', 'observacoes'])
            # Save newly created items
            if items_to_create:
                ItemEncomenda.objects.bulk_create(items_to_create)

            # Final update of encomenda total
            encomenda.valor_total = total_items_value
            encomenda.save(update_fields=['valor_total'])

            messages.success(request, f'Encomenda #{encomenda.numero_encomenda} atualizada com sucesso!')
            return redirect('encomenda_detail', pk=encomenda.pk)
        else:
            messages.error(request, 'Erro ao atualizar encomenda. Verifique os campos abaixo.')
    else:
        # GET request: Pass instance and team context to forms
        form = EncomendaForm(instance=encomenda, equipe=equipe_atual)
        formset = ItemEncomendaFormSet(instance=encomenda, prefix='itens', form_kwargs={'equipe': equipe_atual})

    context = {
        'form': form,
        'formset': formset,
        'encomenda': encomenda,
        'title': f'Editar Encomenda #{encomenda.numero_encomenda} (Equipe: {equipe_atual.nome})',
        'equipe': equipe_atual, # Pass team context
    }
    return render(request, 'encomendas/encomenda_form.html', context)


@login_required(login_url='login')
def encomenda_delete(request, pk):
    """Delete an order, checking team membership."""
    user_equipes_ids = request.user.equipes.values_list('id', flat=True)
    encomenda = get_object_or_404(Encomenda.objects.select_related('equipe'), pk=pk, equipe_id__in=user_equipes_ids)
    equipe_id_redirect = encomenda.equipe.id if encomenda.equipe else None

    if request.method == 'POST':
        numero = encomenda.numero_encomenda
        encomenda.delete()
        messages.success(request, f'Encomenda #{numero} excluída com sucesso!')
        # Redirect back to the general encomenda list, optionally filtering by the team
        redirect_url = reverse('encomenda_list')
        if equipe_id_redirect:
            redirect_url += f'?equipe={equipe_id_redirect}'
        return redirect(redirect_url)

    # GET request: Show confirmation page
    context = {
        'encomenda': encomenda,
        'equipe': encomenda.equipe,
        'title': f'Excluir Encomenda #{encomenda.numero_encomenda}'
        }
    return render(request, 'encomendas/encomenda_confirm_delete.html', context)


# --- Entrega Views (No significant changes needed, rely on Encomenda's team check) ---
@login_required(login_url='login')
def entrega_create(request, encomenda_pk):
    """Create delivery info for an order, checking team membership via the order."""
    user_equipes_ids = request.user.equipes.values_list('id', flat=True)
    encomenda = get_object_or_404(Encomenda.objects.select_related('equipe'), pk=encomenda_pk, equipe_id__in=user_equipes_ids)

    # Check if delivery already exists
    if hasattr(encomenda, 'entrega') and encomenda.entrega is not None:
         messages.warning(request, f"Encomenda #{encomenda.numero_encomenda} já possui informações de entrega.")
         return redirect('entrega_edit', pk=encomenda.entrega.pk) # Redirect to edit existing

    if request.method == 'POST':
        form = EntregaForm(request.POST)
        if form.is_valid():
            entrega = form.save(commit=False)
            entrega.encomenda = encomenda
            # Link form's delivery date to internal planning date
            entrega.data_prevista = form.cleaned_data.get('data_entrega')
            entrega.save()
            messages.success(request, f'Informações de entrega para encomenda #{encomenda.numero_encomenda} criadas!')
            return redirect('encomenda_detail', pk=encomenda.pk)
        else:
             messages.error(request, "Erro ao salvar informações de entrega. Verifique os campos.")
    else:
        # Pre-fill responsible field and default date
        initial_data = {
            'responsavel_entrega': request.user.nome_completo or request.user.username,
            'data_entrega': timezone.now().date()
            }
        form = EntregaForm(initial=initial_data)

    context = {
        'form': form,
        'encomenda': encomenda,
        'equipe': encomenda.equipe, # Pass team context
        'title': f'Programar Entrega - Encomenda #{encomenda.numero_encomenda}',
    }
    return render(request, 'encomendas/entrega_form.html', context)


@login_required(login_url='login')
def entrega_edit(request, pk):
    """Edit delivery info, checking team membership via the order."""
    entrega = get_object_or_404(Entrega.objects.select_related('encomenda__equipe'), pk=pk)
    encomenda = entrega.encomenda

    # Check if user belongs to the encomenda's team
    if not request.user.equipes.filter(id=encomenda.equipe_id).exists():
         messages.error(request, "Você não tem permissão para editar esta entrega.")
         return redirect('listar_equipes') # Or appropriate redirect

    if request.method == 'POST':
        form = EntregaForm(request.POST, instance=entrega)
        if form.is_valid():
            entrega = form.save(commit=False)
            # Link form fields back to potentially different model fields
            entrega.data_prevista = form.cleaned_data.get('data_entrega')
            # Handle combining Date and Time fields into DateTimeField
            data_realizada_form = form.cleaned_data.get('data_entrega_realizada')
            hora_realizada_form = form.cleaned_data.get('hora_entrega')
            if data_realizada_form and hora_realizada_form:
                 entrega.data_realizada = timezone.make_aware(
                     timezone.datetime.combine(data_realizada_form, hora_realizada_form)
                 )
            elif data_realizada_form: # Only date provided
                 entrega.data_realizada = timezone.make_aware(
                     timezone.datetime.combine(data_realizada_form, timezone.datetime.min.time()) # Use midnight
                 )
            else: # Date/Time cleared in form
                 entrega.data_realizada = None
                 # Ensure individual date/time fields are also cleared if combined field is None
                 entrega.data_entrega_realizada = None
                 entrega.hora_entrega = None

            entrega.save()

            # Update encomenda status if delivery date/time was SET
            if entrega.data_realizada and encomenda.status != 'entregue':
                encomenda.status = 'entregue'
                encomenda.save(update_fields=['status'])
                messages.info(request, f'Status da Encomenda #{encomenda.numero_encomenda} atualizado para Entregue.')
            # Optional: Revert status if date/time was CLEARED
            elif not entrega.data_realizada and encomenda.status == 'entregue':
                 # Determine previous status? Simplest is to require manual change.
                 pass

            messages.success(request, 'Informações de entrega atualizadas com sucesso!')
            return redirect('encomenda_detail', pk=encomenda.pk)
        else:
             messages.error(request, "Erro ao atualizar informações de entrega. Verifique os campos.")
    else:
        # GET request: Prepare initial data for form based on model instance
        initial_data = {
            'data_entrega': entrega.data_entrega, # Use model field directly
            'data_entrega_realizada': entrega.data_realizada.date() if entrega.data_realizada else None,
            'hora_entrega': entrega.data_realizada.time() if entrega.data_realizada else None,
        }
        form = EntregaForm(instance=entrega, initial=initial_data)

    context = {
        'form': form,
        'entrega': entrega,
        'encomenda': encomenda,
        'equipe': encomenda.equipe, # Pass team context
        'title': f'Editar Entrega - Encomenda #{encomenda.numero_encomenda}',
    }
    return render(request, 'encomendas/entrega_form.html', context)


# --- Cliente, Produto, Fornecedor Views (UPDATED with team context & annotations) ---

@login_required(login_url='login')
def cliente_list(request, equipe_id):
    """Lists clients for a specific team, including encomenda count."""
    try:
        equipe_atual = get_equipe_atual(request, equipe_id)
        if equipe_atual is None:
            messages.error(request, "ID da equipe não especificado ou acesso negado.")
            return redirect('listar_equipes')
    except Http404 as e:
        messages.error(request, str(e))
        return redirect('listar_equipes')

    # Subquery to count encomendas within this team for each client
    encomendas_count_subquery = Encomenda.objects.filter(
        cliente=OuterRef('pk'),
        equipe=equipe_atual # Filter by the current team
    ).values('cliente').annotate(count=Count('pk')).values('count')

    # Base queryset for clients in the current team, annotated with the count
    clientes_list = Cliente.objects.filter(
        equipe=equipe_atual
    ).annotate(
        encomendas_equipe_count=Coalesce(Subquery(encomendas_count_subquery), 0)
    ).order_by('nome')

    # Apply search filter
    filtro_form = FiltroClienteForm(request.GET)
    search = request.GET.get('search')
    if search:
        clientes_list = clientes_list.filter(
            Q(nome__icontains=search) | Q(codigo__icontains=search) |
            Q(endereco__icontains=search) | Q(bairro__icontains=search) |
            Q(telefone__icontains=search)
        ).distinct()

    # Paginate results
    paginator = Paginator(clientes_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'filtro_form': filtro_form,
        'current_search': search,
        'equipe': equipe_atual, # Pass team context
        'title': f'Clientes - {equipe_atual.nome}'
        }
    return render(request, 'encomendas/cliente_list.html', context)

@login_required(login_url='login')
def cliente_create(request, equipe_id):
    """Creates a new client associated with a specific team."""
    try:
        equipe_atual = get_equipe_atual(request, equipe_id)
        if equipe_atual is None:
             messages.error(request, "ID da equipe não especificado ou acesso negado.")
             return redirect('listar_equipes')
    except Http404 as e:
        messages.error(request, str(e))
        return redirect('listar_equipes')

    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.equipe = equipe_atual # Associate with the current team
            try:
                # Check for unique code within the team before saving
                if Cliente.objects.filter(equipe=equipe_atual, codigo=cliente.codigo).exists():
                     messages.error(request, f"Erro: Já existe um cliente com o código '{cliente.codigo}' na equipe '{equipe_atual.nome}'.")
                else:
                    cliente.save()
                    messages.success(request, f'Cliente {cliente.nome} criado com sucesso na equipe {equipe_atual.nome}!')
                    return redirect('cliente_list', equipe_id=equipe_atual.id)
            except Exception as e: # Catch other potential DB errors
                 messages.error(request, f"Erro ao salvar cliente: {e}")
        else:
             messages.error(request, "Erro ao criar cliente. Verifique os campos.")
    else:
        form = ClienteForm() # Excludes 'equipe' field by default

    context = {
        'form': form,
        'equipe': equipe_atual, # Pass team context
        'title': f'Novo Cliente - {equipe_atual.nome}'
        }
    return render(request, 'encomendas/cliente_form.html', context)


@login_required(login_url='login')
def produto_list(request, equipe_id):
    """Lists products for a specific team, including usage count."""
    try:
        equipe_atual = get_equipe_atual(request, equipe_id)
        if equipe_atual is None:
             messages.error(request, "ID da equipe não especificado ou acesso negado.")
             return redirect('listar_equipes')
    except Http404 as e:
        messages.error(request, str(e))
        return redirect('listar_equipes')

    # Subquery to count usage in ItemEncomenda within this team
    item_usage_subquery = ItemEncomenda.objects.filter(
        produto=OuterRef('pk'),
        encomenda__equipe=equipe_atual # Filter by the current team via related encomenda
    ).values('produto').annotate(count=Count('pk')).values('count')

    # Base queryset for products in the current team, annotated with usage count
    produtos_list = Produto.objects.filter(
        equipe=equipe_atual
    ).annotate(
        uso_equipe_count=Coalesce(Subquery(item_usage_subquery), 0)
    ).order_by('nome')

    # Apply search filter
    filtro_form = FiltroProdutoForm(request.GET)
    search = request.GET.get('search')
    if search:
        produtos_list = produtos_list.filter(
            Q(nome__icontains=search) | Q(codigo__icontains=search) |
            Q(categoria__icontains=search) | Q(descricao__icontains=search)
        ).distinct()

    # Paginate results
    paginator = Paginator(produtos_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'filtro_form': filtro_form,
        'current_search': search,
        'equipe': equipe_atual, # Pass team context
        'title': f'Produtos - {equipe_atual.nome}'
        }
    return render(request, 'encomendas/produto_list.html', context)

@login_required(login_url='login')
def produto_create(request, equipe_id):
    """Creates a new product associated with a specific team."""
    try:
        equipe_atual = get_equipe_atual(request, equipe_id)
        if equipe_atual is None:
             messages.error(request, "ID da equipe não especificado ou acesso negado.")
             return redirect('listar_equipes')
    except Http404 as e:
        messages.error(request, str(e))
        return redirect('listar_equipes')

    if request.method == 'POST':
        form = ProdutoForm(request.POST)
        if form.is_valid():
            produto = form.save(commit=False)
            produto.equipe = equipe_atual
            try:
                # Check for unique code within the team
                if Produto.objects.filter(equipe=equipe_atual, codigo=produto.codigo).exists():
                     messages.error(request, f"Erro: Já existe um produto com o código '{produto.codigo}' na equipe '{equipe_atual.nome}'.")
                else:
                    produto.save()
                    messages.success(request, f'Produto {produto.nome} criado com sucesso na equipe {equipe_atual.nome}!')
                    return redirect('produto_list', equipe_id=equipe_atual.id)
            except Exception as e:
                 messages.error(request, f"Erro ao salvar produto: {e}")
        else:
            messages.error(request, "Erro ao criar produto. Verifique os campos.")
    else:
        form = ProdutoForm() # Excludes 'equipe' field by default

    context = {
        'form': form,
        'equipe': equipe_atual, # Pass team context
        'title': f'Novo Produto - {equipe_atual.nome}'
        }
    return render(request, 'encomendas/produto_form.html', context)


@login_required(login_url='login')
def fornecedor_list(request, equipe_id):
    """Lists suppliers for a specific team, including usage count."""
    try:
        equipe_atual = get_equipe_atual(request, equipe_id)
        if equipe_atual is None:
             messages.error(request, "ID da equipe não especificado ou acesso negado.")
             return redirect('listar_equipes')
    except Http404 as e:
        messages.error(request, str(e))
        return redirect('listar_equipes')

    # Subquery to count usage in ItemEncomenda within this team
    item_usage_subquery = ItemEncomenda.objects.filter(
        fornecedor=OuterRef('pk'),
        encomenda__equipe=equipe_atual # Filter by the current team via related encomenda
    ).values('fornecedor').annotate(count=Count('pk')).values('count')

    # Base queryset for suppliers in the current team, annotated with usage count
    fornecedores_list = Fornecedor.objects.filter(
        equipe=equipe_atual
    ).annotate(
        uso_equipe_count=Coalesce(Subquery(item_usage_subquery), 0)
    ).order_by('nome')

    # Apply search filter
    filtro_form = FiltroFornecedorForm(request.GET)
    search = request.GET.get('search')
    if search:
        fornecedores_list = fornecedores_list.filter(
            Q(nome__icontains=search) | Q(codigo__icontains=search) |
            Q(contato__icontains=search) | Q(email__icontains=search) |
            Q(telefone__icontains=search)
        ).distinct()

    # Paginate results
    paginator = Paginator(fornecedores_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'filtro_form': filtro_form,
        'current_search': search,
        'equipe': equipe_atual, # Pass team context
        'title': f'Fornecedores - {equipe_atual.nome}'
        }
    return render(request, 'encomendas/fornecedor_list.html', context)

@login_required(login_url='login')
def fornecedor_create(request, equipe_id):
    """Creates a new supplier associated with a specific team."""
    try:
        equipe_atual = get_equipe_atual(request, equipe_id)
        if equipe_atual is None:
             messages.error(request, "ID da equipe não especificado ou acesso negado.")
             return redirect('listar_equipes')
    except Http404 as e:
        messages.error(request, str(e))
        return redirect('listar_equipes')

    if request.method == 'POST':
        form = FornecedorForm(request.POST)
        if form.is_valid():
            fornecedor = form.save(commit=False)
            fornecedor.equipe = equipe_atual
            try:
                # Check for unique code within the team
                if Fornecedor.objects.filter(equipe=equipe_atual, codigo=fornecedor.codigo).exists():
                     messages.error(request, f"Erro: Já existe um fornecedor com o código '{fornecedor.codigo}' na equipe '{equipe_atual.nome}'.")
                else:
                    fornecedor.save()
                    messages.success(request, f'Fornecedor {fornecedor.nome} criado com sucesso na equipe {equipe_atual.nome}!')
                    return redirect('fornecedor_list', equipe_id=equipe_atual.id)
            except Exception as e:
                messages.error(request, f"Erro ao salvar fornecedor: {e}")
        else:
             messages.error(request, "Erro ao criar fornecedor. Verifique os campos.")
    else:
        form = FornecedorForm() # Excludes 'equipe' field by default

    context = {
        'form': form,
        'equipe': equipe_atual, # Pass team context
        'title': f'Novo Fornecedor - {equipe_atual.nome}'
        }
    return render(request, 'encomendas/fornecedor_form.html', context)


# --- API Views (Ensure team context is handled) ---

@login_required(login_url='login')
@require_http_methods(["GET"])
def api_produto_info(request, produto_id):
    """Returns product info via AJAX. Checks team access."""
    user_equipes_ids = request.user.equipes.values_list('id', flat=True)
    try:
        # Ensure the product belongs to one of the user's teams
        produto = Produto.objects.get(id=produto_id, equipe_id__in=user_equipes_ids)
        data = {
            'nome': produto.nome,
            'codigo': produto.codigo,
            'preco_base': str(produto.preco_base),
            # 'equipe_id': str(produto.equipe_id) # Optionally include team ID
        }
        return JsonResponse(data)
    except Produto.DoesNotExist:
        return JsonResponse({'error': 'Produto não encontrado ou acesso não permitido'}, status=404)


@login_required(login_url='login')
@require_http_methods(["POST"])
def api_update_status(request, encomenda_pk):
    """Updates order status via AJAX, checking team membership."""
    user_equipes_ids = request.user.equipes.values_list('id', flat=True)
    encomenda = get_object_or_404(Encomenda, pk=encomenda_pk, equipe_id__in=user_equipes_ids)

    new_status = request.POST.get('status')
    valid_statuses = [choice[0] for choice in Encomenda.STATUS_CHOICES]
    if new_status in valid_statuses:
        old_status_display = encomenda.get_status_display()
        encomenda.status = new_status
        encomenda.save(update_fields=['status'])
        new_status_display = encomenda.get_status_display() # Get display name after save
        return JsonResponse({
            'success': True,
            'status_code': new_status,        # Return the code (e.g., 'entregue')
            'status_display': new_status_display, # Return the display name (e.g., 'Entregue')
            'message': f'Status alterado de "{old_status_display}" para "{new_status_display}"'
        })
    else:
        return JsonResponse({'error': 'Status inválido'}, status=400)


@login_required(login_url='login')
def encomenda_pdf(request, pk):
    """Generates PDF for an order, checking team membership."""
    user_equipes_ids = request.user.equipes.values_list('id', flat=True)
    encomenda = get_object_or_404(Encomenda.objects.select_related('cliente', 'equipe'), pk=pk, equipe_id__in=user_equipes_ids)
    entrega = getattr(encomenda, 'entrega', None)
    # Ensure items shown also belong to the team
    itens = encomenda.itens.filter(
        produto__equipe=encomenda.equipe,
        fornecedor__equipe=encomenda.equipe
    ).select_related('produto', 'fornecedor').all()

    context = {'encomenda': encomenda, 'entrega': entrega, 'itens': itens}
    template = get_template('encomendas/encomenda_pdf.html')
    html = template.render(context)

    try:
        from weasyprint import HTML # Consider optional import
        pdf = HTML(string=html).write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        # Use inline for viewing in browser, attachment for download prompt
        response['Content-Disposition'] = f'inline; filename="encomenda_{encomenda.numero_encomenda}.pdf"'
        return response
    except ImportError:
        messages.error(request, 'Erro ao gerar PDF: Biblioteca WeasyPrint não encontrada. Instale com "pip install weasyprint".')
        return redirect('encomenda_detail', pk=pk)
    except Exception as e:
        # Log the error in production
        print(f'Erro inesperado ao gerar PDF: {e}')
        messages.error(request, f'Erro inesperado ao gerar PDF.')
        return redirect('encomenda_detail', pk=pk)


@login_required(login_url='login')
@require_http_methods(["POST"])
def marcar_entrega_realizada(request, pk):
    """Marks a delivery as completed, checking team membership via the order."""
    user_equipes_ids = request.user.equipes.values_list('id', flat=True)
    # Ensure user has access to the encomenda linked to this entrega
    entrega = get_object_or_404(Entrega.objects.select_related('encomenda__equipe'), pk=pk, encomenda__equipe_id__in=user_equipes_ids)
    encomenda = entrega.encomenda

    if entrega.data_realizada:
        messages.warning(request, f'Entrega da encomenda #{encomenda.numero_encomenda} já está marcada como realizada.')
        return redirect('encomenda_detail', pk=encomenda.pk)

    now = timezone.now()
    entrega.data_realizada = now # Set combined DateTimeField
    entrega.data_entrega_realizada = now.date() # Set DateField for consistency
    entrega.hora_entrega = now.time() # Set TimeField for consistency

    # Optionally pre-fill 'entregue_por' if empty
    if not entrega.entregue_por:
        entrega.entregue_por = request.user.nome_completo or request.user.username
    # Optionally mark signature based on request data if needed
    # entrega.assinatura_cliente = True # Or based on a form field

    entrega.save()

    # Update encomenda status
    if encomenda.status != 'entregue':
        encomenda.status = 'entregue'
        encomenda.save(update_fields=['status'])

    messages.success(request, f'Entrega da encomenda #{encomenda.numero_encomenda} marcada como realizada!')
    return redirect('encomenda_detail', pk=encomenda.pk)


# --- Search APIs (Updated to filter by user's teams) ---

@login_required(login_url='login')
def search_produtos(request):
    """API view for searching products (Select2) within user's teams."""
    search_term = request.GET.get('q', '')
    equipe_id = request.GET.get('equipe_id') # Optional: specific team context
    user_equipes = request.user.equipes.all()

    produtos = Produto.objects.filter(equipe__in=user_equipes) # Start with user's accessible products

    # Further filter by specific team if requested AND user belongs to it
    if equipe_id:
         if user_equipes.filter(id=equipe_id).exists():
             produtos = produtos.filter(equipe_id=equipe_id)
         else:
             produtos = Produto.objects.none() # Invalid team for user

    # Apply search term
    if search_term:
        produtos = produtos.filter(
            Q(nome__icontains=search_term) | Q(codigo__icontains=search_term)
        )

    produtos = produtos.select_related('equipe').order_by('nome')[:20] # Limit results, include team for display

    results = [{'id': p.id, 'text': f"{p.codigo} - {p.nome} ({p.equipe.nome})"} for p in produtos]
    return JsonResponse({'results': results})


@login_required(login_url='login')
def search_clientes(request):
    """API view for searching clients (Select2) within user's teams."""
    search_term = request.GET.get('q', '')
    equipe_id = request.GET.get('equipe_id')
    user_equipes = request.user.equipes.all()

    clientes = Cliente.objects.filter(equipe__in=user_equipes)

    if equipe_id:
        if user_equipes.filter(id=equipe_id).exists():
             clientes = clientes.filter(equipe_id=equipe_id)
        else:
             clientes = Cliente.objects.none()

    if search_term:
        clientes = clientes.filter(
            Q(nome__icontains=search_term) | Q(codigo__icontains=search_term) | Q(telefone__icontains=search)
        )

    clientes = clientes.select_related('equipe').order_by('nome')[:20]
    results = [{'id': c.id, 'text': f"{c.codigo} - {c.nome} ({c.equipe.nome})"} for c in clientes]
    return JsonResponse({'results': results})


@login_required(login_url='login')
def search_fornecedores(request):
    """API view for searching suppliers (Select2) within user's teams."""
    search_term = request.GET.get('q', '')
    equipe_id = request.GET.get('equipe_id')
    user_equipes = request.user.equipes.all()

    fornecedores = Fornecedor.objects.filter(equipe__in=user_equipes)

    if equipe_id:
        if user_equipes.filter(id=equipe_id).exists():
            fornecedores = fornecedores.filter(equipe_id=equipe_id)
        else:
            fornecedores = Fornecedor.objects.none()

    if search_term:
        fornecedores = fornecedores.filter(
            Q(nome__icontains=search_term) | Q(codigo__icontains=search_term) | Q(contato__icontains=search)
        )

    fornecedores = fornecedores.select_related('equipe').order_by('nome')[:20]
    results = [{'id': f.id, 'text': f"{f.codigo} - {f.nome} ({f.equipe.nome})"} for f in fornecedores]
    return JsonResponse({'results': results})