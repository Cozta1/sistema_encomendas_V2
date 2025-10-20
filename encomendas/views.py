from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Value
from django.db.models.functions import Coalesce 
from django.template.loader import get_template
from django.utils import timezone
from .models import Encomenda, Cliente, Produto, Fornecedor, ItemEncomenda, Entrega
from .forms import EncomendaForm, ItemEncomendaFormSet, EntregaForm, ClienteForm, ProdutoForm, FornecedorForm, FiltroEncomendaForm
from decimal import Decimal


def dashboard(request):
    """Dashboard principal com estatísticas"""
    total_encomendas = Encomenda.objects.count()
    encomendas_pendentes = Encomenda.objects.filter(status__in=['criada', 'cotacao', 'aprovada', 'em_andamento', 'pronta']).count()
    encomendas_entregues = Encomenda.objects.filter(status='entregue').count()

    ultimas_encomendas = Encomenda.objects.select_related('cliente').order_by('-data_criacao')[:5]

    context = {
        'total_encomendas': total_encomendas,
        'encomendas_pendentes': encomendas_pendentes,
        'encomendas_entregues': encomendas_entregues,
        'ultimas_encomendas': ultimas_encomendas,
    }
    return render(request, 'encomendas/dashboard.html', context)


def encomenda_list(request):
    """Lista todas as encomendas com filtros"""
    encomendas_list = Encomenda.objects.select_related('cliente').order_by('-numero_encomenda')

    filtro_form = FiltroEncomendaForm(request.GET)
    current_status = None
    current_cliente = None
    current_search = None

    if filtro_form.is_valid():
        current_status = filtro_form.cleaned_data.get('status')
        current_cliente = filtro_form.cleaned_data.get('cliente')
        current_search = filtro_form.cleaned_data.get('search')

        if current_status:
            encomendas_list = encomendas_list.filter(status=current_status)

        if current_cliente:
            encomendas_list = encomendas_list.filter(cliente=current_cliente)

        if current_search:
            encomendas_list = encomendas_list.filter(
                Q(numero_encomenda__icontains=current_search) |
                Q(cliente__nome__icontains=current_search) |
                Q(cliente__codigo__icontains=current_search) |
                Q(itens__produto__nome__icontains=current_search) |
                Q(itens__produto__codigo__icontains=current_search) |
                Q(responsavel_criacao__icontains=current_search) |
                Q(observacoes__icontains=current_search)
            ).distinct()

    total_geral_filtrado = encomendas_list.count()
    total_pendentes_filtrado = encomendas_list.filter(status__in=['criada', 'cotacao', 'aprovada', 'em_andamento', 'pronta']).count()
    total_entregues_filtrado = encomendas_list.filter(status='entregue').count()
    valor_total_filtrado = encomendas_list.aggregate(
        total_valor=Coalesce(Sum('valor_total'), Value(Decimal('0.00')))
    )['total_valor']

    paginator = Paginator(encomendas_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    clientes = Cliente.objects.all().order_by('nome')
    status_choices = Encomenda.STATUS_CHOICES

    context = {
        'page_obj': page_obj,
        'filtro_form': filtro_form,
        'clientes': clientes,
        'status_choices': status_choices,
        'current_status': current_status,
        'current_cliente_id': current_cliente.id if current_cliente else None,
        'current_search': current_search,
        'total_geral_filtrado': total_geral_filtrado,
        'total_pendentes_filtrado': total_pendentes_filtrado,
        'total_entregues_filtrado': total_entregues_filtrado,
        'valor_total_filtrado': valor_total_filtrado,
    }
    return render(request, 'encomendas/encomenda_list.html', context)


# --- Rest of your views.py ---
# encomenda_detail, encomenda_create, etc. remain the same
# ... (Keep all other functions as they were) ...

def cliente_list(request):
    """Lista de clientes"""
    clientes = Cliente.objects.all().order_by('nome')

    search = request.GET.get('search')
    if search:
        clientes = clientes.filter(
            Q(nome__icontains=search) |
            Q(codigo__icontains=search) |
            Q(endereco__icontains=search)
        )

    paginator = Paginator(clientes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'current_search': search,
    }
    return render(request, 'encomendas/cliente_list.html', context)


def cliente_create(request):
    """Criar novo cliente"""
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f'Cliente {cliente.nome} criado com sucesso!')
            return redirect('cliente_list')
    else:
        form = ClienteForm()

    context = {
        'form': form,
        'title': 'Novo Cliente',
    }
    return render(request, 'encomendas/cliente_form.html', context)


def produto_list(request):
    """Lista de produtos"""
    produtos = Produto.objects.all().order_by('nome')

    search = request.GET.get('search')
    if search:
        produtos = produtos.filter(
            Q(nome__icontains=search) |
            Q(codigo__icontains=search) |
            Q(categoria__icontains=search)
        )

    paginator = Paginator(produtos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'current_search': search,
    }
    return render(request, 'encomendas/produto_list.html', context)


def produto_create(request):
    """Criar novo produto"""
    if request.method == 'POST':
        form = ProdutoForm(request.POST)
        if form.is_valid():
            produto = form.save()
            messages.success(request, f'Produto {produto.nome} criado com sucesso!')
            return redirect('produto_list')
    else:
        form = ProdutoForm()

    context = {
        'form': form,
        'title': 'Novo Produto',
    }
    return render(request, 'encomendas/produto_form.html', context)


def fornecedor_list(request):
    """Lista de fornecedores"""
    fornecedores = Fornecedor.objects.all().order_by('nome')

    search = request.GET.get('search')
    if search:
        fornecedores = fornecedores.filter(
            Q(nome__icontains=search) |
            Q(codigo__icontains=search) |
            Q(contato__icontains=search)
        )

    paginator = Paginator(fornecedores, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'current_search': search,
    }
    return render(request, 'encomendas/fornecedor_list.html', context)


def fornecedor_create(request):
    """Criar novo fornecedor"""
    if request.method == 'POST':
        form = FornecedorForm(request.POST)
        if form.is_valid():
            fornecedor = form.save()
            messages.success(request, f'Fornecedor {fornecedor.nome} criado com sucesso!')
            return redirect('fornecedor_list')
    else:
        form = FornecedorForm()

    context = {
        'form': form,
        'title': 'Novo Fornecedor',
    }
    return render(request, 'encomendas/fornecedor_form.html', context)


# API Views para AJAX

@require_http_methods(["GET"])
def api_produto_info(request, produto_id):
    """Retorna informações do produto via AJAX"""
    try:
        produto = Produto.objects.get(id=produto_id)
        data = {
            'nome': produto.nome,
            'codigo': produto.codigo,
            'preco_base': str(produto.preco_base),
        }
        return JsonResponse(data)
    except Produto.DoesNotExist:
        return JsonResponse({'error': 'Produto não encontrado'}, status=404)


@require_http_methods(["POST"])
def api_update_status(request, encomenda_pk):
    """Atualiza status da encomenda via AJAX"""
    encomenda = get_object_or_404(Encomenda, pk=encomenda_pk)
    new_status = request.POST.get('status')

    if new_status in dict(Encomenda.STATUS_CHOICES):
        old_status = encomenda.get_status_display()
        encomenda.status = new_status
        encomenda.save()
        return JsonResponse({
            'success': True,
            'status': encomenda.get_status_display(),
            'message': f'Status alterado de "{old_status}" para "{encomenda.get_status_display()}"'
        })

    return JsonResponse({'error': 'Status inválido'}, status=400)


def encomenda_pdf(request, pk):
    """Gerar PDF da encomenda no formato do formulário físico"""
    encomenda = get_object_or_404(Encomenda, pk=pk)

    # Buscar entrega se existir
    entrega = None
    try:
        entrega = Entrega.objects.get(encomenda=encomenda)
    except Entrega.DoesNotExist:
        pass

    context = {
        'encomenda': encomenda,
        'entrega': entrega,
    }

    template = get_template('encomendas/encomenda_pdf.html')
    html = template.render(context)

    # Usar weasyprint para gerar PDF
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration

        font_config = FontConfiguration()

        pdf = HTML(string=html).write_pdf()

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="encomenda_{encomenda.numero_encomenda}.pdf"'

        return response

    except ImportError:
        messages.error(request, 'Erro ao gerar PDF. WeasyPrint não está instalado.')
        return redirect('encomenda_detail', pk=pk)


def marcar_entrega_realizada(request, pk):
    """Marcar entrega como realizada"""
    entrega = get_object_or_404(Entrega, pk=pk)

    # Use POST method check for safety
    if request.method == 'POST':
        entrega.data_realizada = timezone.now() # Use data_realizada (DateTimeField)
        # Optionally set data_entrega_realizada if needed for display consistency
        entrega.data_entrega_realizada = timezone.now().date()
        entrega.save()

        # Atualizar status da encomenda
        entrega.encomenda.status = 'entregue'
        entrega.encomenda.save()

        messages.success(request, f'Entrega da encomenda #{entrega.encomenda.numero_encomenda} marcada como realizada!')
        return redirect('encomenda_detail', pk=entrega.encomenda.pk)
    else:
        # Redirect GET requests or show a confirmation page
        messages.warning(request, 'Use o botão apropriado para marcar a entrega como realizada.')
        return redirect('encomenda_detail', pk=entrega.encomenda.pk)

# Keep other detail/create/edit/delete views below if they exist
# encomenda_detail, encomenda_create, encomenda_edit, encomenda_delete
# entrega_create, entrega_edit

# Make sure all required functions are present

def encomenda_detail(request, pk):
    """Detalhes de uma encomenda específica"""
    encomenda = get_object_or_404(Encomenda, pk=pk)
    itens = encomenda.itens.select_related('produto', 'fornecedor').all()

    try:
        entrega = encomenda.entrega
    except Entrega.DoesNotExist:
        entrega = None

    context = {
        'encomenda': encomenda,
        'itens': itens,
        'entrega': entrega,
    }
    return render(request, 'encomendas/encomenda_detail.html', context)


def encomenda_create(request):
    """Criar nova encomenda"""
    if request.method == 'POST':
        form = EncomendaForm(request.POST)
        formset = ItemEncomendaFormSet(request.POST, prefix='itens') # Added prefix

        if form.is_valid() and formset.is_valid():
            encomenda = form.save()

            # Salvar itens
            instances = formset.save(commit=False)
            for instance in instances:
                instance.encomenda = encomenda
                instance.save()
            formset.save_m2m() # Important for some formset types, though maybe not inline

            # Recalcular valor total (save method on ItemEncomenda should handle this)
            # encomenda.calcular_valor_total() # Calling save on item should trigger this

            messages.success(request, f'Encomenda #{encomenda.numero_encomenda} criada com sucesso!')
            return redirect('encomenda_detail', pk=encomenda.pk)
        else:
            print("Form errors:", form.errors)
            print("Formset errors:", formset.errors)
            messages.error(request, 'Erro ao criar encomenda. Verifique os campos.')
    else:
        form = EncomendaForm()
        formset = ItemEncomendaFormSet(prefix='itens') # Added prefix

    context = {
        'form': form,
        'formset': formset,
        'title': 'Nova Encomenda',
    }
    return render(request, 'encomendas/encomenda_form.html', context)


def encomenda_edit(request, pk):
    """Editar encomenda existente"""
    encomenda = get_object_or_404(Encomenda, pk=pk)

    if request.method == 'POST':
        form = EncomendaForm(request.POST, instance=encomenda)
        formset = ItemEncomendaFormSet(request.POST, instance=encomenda, prefix='itens') # Added prefix

        if form.is_valid() and formset.is_valid():
            encomenda = form.save()
            formset.save() # This should handle deletes and updates

            # Recalcular valor total (save method on ItemEncomenda should handle this)
            # encomenda.calcular_valor_total() # Calling save/delete on items should trigger this

            messages.success(request, f'Encomenda #{encomenda.numero_encomenda} atualizada com sucesso!')
            return redirect('encomenda_detail', pk=encomenda.pk)
        else:
            print("Form errors:", form.errors)
            print("Formset errors:", formset.errors)
            messages.error(request, 'Erro ao atualizar encomenda. Verifique os campos.')

    else:
        form = EncomendaForm(instance=encomenda)
        formset = ItemEncomendaFormSet(instance=encomenda, prefix='itens') # Added prefix

    context = {
        'form': form,
        'formset': formset,
        'encomenda': encomenda,
        'title': f'Editar Encomenda #{encomenda.numero_encomenda}',
    }
    return render(request, 'encomendas/encomenda_form.html', context)


def encomenda_delete(request, pk):
    """Excluir encomenda"""
    encomenda = get_object_or_404(Encomenda, pk=pk)

    if request.method == 'POST':
        numero = encomenda.numero_encomenda
        encomenda.delete()
        messages.success(request, f'Encomenda #{numero} excluída com sucesso!')
        return redirect('encomenda_list')

    context = {'encomenda': encomenda}
    return render(request, 'encomendas/encomenda_confirm_delete.html', context)


def entrega_create(request, encomenda_pk):
    """Criar informações de entrega para uma encomenda"""
    encomenda = get_object_or_404(Encomenda, pk=encomenda_pk)

    # Verificar se já existe entrega
    try:
        entrega = encomenda.entrega
        return redirect('entrega_edit', pk=entrega.pk)
    except Entrega.DoesNotExist:
        pass

    if request.method == 'POST':
        form = EntregaForm(request.POST)
        if form.is_valid():
            entrega = form.save(commit=False)
            entrega.encomenda = encomenda
            entrega.save()

            messages.success(request, 'Informações de entrega criadas com sucesso!')
            return redirect('encomenda_detail', pk=encomenda.pk)
    else:
        # Pre-fill responsible field if possible
        initial_data = {'responsavel_entrega': request.user.nome_completo if request.user.is_authenticated else ''}
        form = EntregaForm(initial=initial_data)


    context = {
        'form': form,
        'encomenda': encomenda,
        'title': f'Programar Entrega - Encomenda #{encomenda.numero_encomenda}',
    }
    return render(request, 'encomendas/entrega_form.html', context)


def entrega_edit(request, pk):
    """Editar informações de entrega"""
    entrega = get_object_or_404(Entrega, pk=pk)
    encomenda = entrega.encomenda # Get related encomenda

    if request.method == 'POST':
        form = EntregaForm(request.POST, instance=entrega)
        if form.is_valid():
            entrega = form.save()

            # Atualizar status da encomenda se foi entregue
            if entrega.data_realizada: # Check if the delivery date/time is set
                entrega.encomenda.status = 'entregue'
                entrega.encomenda.save()
                messages.info(request, f'Status da Encomenda #{entrega.encomenda.numero_encomenda} atualizado para Entregue.')


            messages.success(request, 'Informações de entrega atualizadas com sucesso!')
            return redirect('encomenda_detail', pk=entrega.encomenda.pk)
    else:
        form = EntregaForm(instance=entrega)

    context = {
        'form': form,
        'entrega': entrega,
        'encomenda': encomenda, # Pass encomenda to context
        'title': f'Editar Entrega - Encomenda #{entrega.encomenda.numero_encomenda}',
    }
    return render(request, 'encomendas/entrega_form.html', context)


# NOVA VIEW PARA PESQUISA DE PRODUTOS
def search_produtos(request):
    """API view for searching products for Select2."""
    search_term = request.GET.get('q', '')
    produtos = Produto.objects.filter(
        Q(nome__icontains=search_term) | Q(codigo__icontains=search_term)
    ).order_by('nome')[:20] # Limita a 20 resultados

    results = []
    for produto in produtos:
        results.append({
            'id': produto.id,
            'text': f"{produto.codigo} - {produto.nome}"
        })
        
    return JsonResponse({'results': results})