# encomendas/views.py
from django.shortcuts import get_object_or_404
from django.http import Http404, JsonResponse, HttpResponse # Mantenha JsonResponse/HttpResponse para APIs
from django.contrib.auth.decorators import login_required # Mantenha se usar em APIs existentes
from django.views.decorators.http import require_http_methods # Mantenha se usar em APIs existentes
from django.utils import timezone
from django.db.models import Q, Sum, Value, Count, Subquery, OuterRef
from django.db.models.functions import Coalesce
from decimal import Decimal
from django.template.loader import get_template # Mantenha para PDF

# DRF Imports
from rest_framework import viewsets, permissions, status, serializers # Import serializers base
from rest_framework.response import Response
from rest_framework.decorators import action # Para ações customizadas se necessário

# (Opcional) Imports para filtros
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

# Models
from .models import (
    Encomenda, Cliente, Produto, Fornecedor, ItemEncomenda, Entrega,
    Equipe, MembroEquipe, Usuario # Mantenha todos os modelos
)
# Serializers (Importe os serializers criados no passo anterior)
from .serializers import (
    EncomendaSerializer, ClienteSerializer, ProdutoSerializer,
    FornecedorSerializer, EntregaSerializer # Adicione outros conforme necessário
)
# Mantenha forms se usados em APIs existentes ou lógicas complexas que não migraram para serializers
# from .forms import FiltroEncomendaForm, ...

# --- Helper function to get current team (MANTENHA ESTA FUNÇÃO) ---
def get_equipe_atual(request, equipe_id=None):
    """
    Determines the current team context for the logged-in user.
    Prioritizes equipe_id from URL.
    Raises Http404 if no team context can be found or user is not a member.
    Returns None if user has multiple teams but no specific ID was provided.
    """
    if not request.user.is_authenticated:
        raise Http404("Usuário não autenticado.")

    user_equipes = request.user.equipes.all()

    if equipe_id:
        try:
            equipe = user_equipes.get(id=equipe_id)
            return equipe
        except Equipe.DoesNotExist:
            raise Http404("Equipe não encontrada ou você não é membro.")

    if user_equipes.count() == 1:
        return user_equipes.first()
    elif user_equipes.count() > 1:
        # Em APIs, talvez seja melhor retornar um erro 400 Bad Request se a equipe for ambígua
        # raise serializers.ValidationError("ID da equipe é necessário pois você pertence a múltiplas equipes.")
        return None
    else:
        raise Http404("Você não pertence a nenhuma equipe.")

# --- DRF ViewSets ---

class EncomendaViewSet(viewsets.ModelViewSet):
    """
    API endpoint que permite visualizar, criar, editar e excluir Encomendas.
    Filtra automaticamente para mostrar apenas encomendas das equipes do usuário.
    """
    serializer_class = EncomendaSerializer
    permission_classes = [permissions.IsAuthenticated] # Garante autenticação

    # Configura filtros
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'cliente__id', 'equipe__id']
    search_fields = ['numero_encomenda', 'cliente__nome', 'cliente__codigo', 'itens__produto__nome', 'responsavel_criacao', 'equipe__nome']
    ordering_fields = ['numero_encomenda', 'data_criacao', 'data_encomenda', 'valor_total', 'status']
    ordering = ['-numero_encomenda']

    def get_queryset(self):
        """Filtra o queryset para retornar apenas encomendas das equipes do usuário."""
        user = self.request.user
        # O DRF já garante autenticação via permission_classes, mas checar aqui é seguro
        if user.is_authenticated:
            user_equipes_ids = user.equipes.values_list('id', flat=True)
            return Encomenda.objects.filter(equipe_id__in=user_equipes_ids).select_related(
                'cliente', 'equipe', 'entrega'
            ).prefetch_related(
                'itens__produto', 'itens__fornecedor'
            )
        return Encomenda.objects.none()

    def perform_create(self, serializer):
        """Associa a encomenda à equipe correta e ao usuário ao criar."""
        equipe_id_url = self.kwargs.get('equipe_pk')
        equipe_id_data = self.request.data.get('equipe_id')
        equipe = None
        user = self.request.user

        try:
            if equipe_id_url:
                equipe = get_object_or_404(Equipe, id=equipe_id_url, membros=user)
            elif equipe_id_data:
                 equipe = get_object_or_404(Equipe, id=equipe_id_data, membros=user)
            else:
                equipe = get_equipe_atual(self.request)
                if equipe is None:
                     raise serializers.ValidationError(
                         "Não foi possível determinar a equipe. Especifique 'equipe_id' na URL ou no corpo da requisição, ou pertença a apenas uma equipe."
                     )

            responsavel = user.nome_completo or user.username
            # Passa a equipe para o contexto do serializer
            context = self.get_serializer_context() # Obtem contexto base
            context['equipe'] = equipe # Adiciona equipe ao contexto
            # Salva passando a equipe e o responsável diretamente
            serializer.save(
                responsavel_criacao=responsavel,
                equipe=equipe
                # O serializer create/update agora acessará context['equipe']
            )
        except Http404 as e:
             raise serializers.ValidationError(str(e))
        except serializers.ValidationError as e:
            raise e
        except Exception as e:
            print(f"Erro inesperado em EncomendaViewSet perform_create: {e}")
            raise serializers.ValidationError("Ocorreu um erro inesperado ao criar a encomenda.")


    def get_serializer_context(self):
        """Adiciona a equipe ao contexto do serializer."""
        context = super().get_serializer_context()
        equipe = None
        user = self.request.user
        equipe_id_url = self.kwargs.get('equipe_pk')
        try:
            if equipe_id_url:
                equipe = get_object_or_404(Equipe, id=equipe_id_url, membros=user)
            else:
                # Usa self.get_object() que já lida com 404 se não encontrado
                instance = self.get_object() if self.detail else None
                if instance and hasattr(instance, 'equipe'):
                    equipe = instance.equipe
                    if not user.equipes.filter(id=equipe.id).exists():
                         # Segurança: Levanta erro se usuário não pertence à equipe da instância
                         raise Http404("Acesso negado à equipe desta encomenda.")
                elif self.action == 'create': # Ação de criação
                    equipe_id_data = self.request.data.get('equipe_id')
                    if equipe_id_data:
                         equipe = get_object_or_404(Equipe, id=equipe_id_data, membros=user)
                    else:
                         equipe_detectada = get_equipe_atual(self.request)
                         if equipe_detectada:
                             equipe = equipe_detectada
                         # Se ainda for None (ambíguo), perform_create levantará o erro

            if equipe:
                 context['equipe'] = equipe
        except Http404:
            # Se não encontrar a equipe ou acesso negado, deixa passar aqui.
            # get_queryset ou perform_create/update devem tratar a permissão.
             pass
        # Adiciona request ao contexto, útil para HyperlinkedSerializers ou validações
        context['request'] = self.request
        return context

# --- ViewSet Base para filtrar por equipe ---
class BaseEquipeFilteredViewSet(viewsets.ModelViewSet):
    """ViewSet base que filtra o queryset pela equipe e associa na criação."""
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filtra queryset para equipes do usuário ou equipe específica da URL."""
        user = self.request.user
        model = self.serializer_class.Meta.model
        queryset = model.objects.all()

        if user.is_authenticated:
            user_equipes_ids = user.equipes.values_list('id', flat=True)
            equipe_id_url = self.kwargs.get('equipe_pk')

            if equipe_id_url:
                try:
                    # Tenta pegar a equipe_id como UUID
                    equipe_uuid = uuid.UUID(equipe_id_url)
                    if equipe_uuid in user_equipes_ids:
                        queryset = queryset.filter(equipe_id=equipe_uuid)
                    else:
                        return model.objects.none() # Usuário não pertence
                except (ValueError, TypeError):
                     return model.objects.none() # ID inválido
            else:
                queryset = queryset.filter(equipe_id__in=user_equipes_ids)

            if not equipe_id_url:
                 queryset = queryset.select_related('equipe')

            ordering = getattr(self, 'ordering', getattr(model._meta, 'ordering', None))
            if ordering:
                queryset = queryset.order_by(*ordering)
            elif hasattr(model._meta, 'get_latest_by'):
                 queryset = queryset.order_by(f"-{model._meta.get_latest_by}")

            return queryset

        return model.objects.none()


    def perform_create(self, serializer):
        """Associa o objeto à equipe correta ao criar."""
        equipe_id_url = self.kwargs.get('equipe_pk')
        equipe_id_data = self.request.data.get('equipe_id')
        user = self.request.user
        model = self.serializer_class.Meta.model
        equipe = None

        try:
            if equipe_id_url:
                 equipe = get_object_or_404(Equipe, id=equipe_id_url, membros=user)
            elif equipe_id_data:
                 equipe = get_object_or_404(Equipe, id=equipe_id_data, membros=user)
            else:
                 equipe = get_equipe_atual(self.request)
                 if equipe is None:
                     raise serializers.ValidationError(
                         "Não foi possível determinar a equipe. Especifique 'equipe_id' na URL ou no corpo da requisição, ou pertença a apenas uma equipe."
                     )

            # Validação de código único DENTRO da equipe
            if hasattr(model, 'codigo'):
                 codigo = serializer.validated_data.get('codigo')
                 if codigo and model.objects.filter(equipe=equipe, codigo=codigo).exists():
                     # Verifica se não é o próprio objeto sendo atualizado (caso PATCH/PUT)
                     instance = serializer.instance
                     if instance is None or instance.codigo != codigo:
                          raise serializers.ValidationError(
                              f"Já existe um(a) {model._meta.verbose_name} com o código '{codigo}' na equipe '{equipe.nome}'."
                          )

            serializer.save(equipe=equipe)
        except Http404 as e:
            raise serializers.ValidationError(str(e))
        except serializers.ValidationError as e:
            raise e
        except Exception as e:
            print(f"Erro inesperado em {self.__class__.__name__} perform_create: {e}")
            raise serializers.ValidationError(f"Ocorreu um erro inesperado ao criar {model._meta.verbose_name}.")

    def get_serializer_context(self):
        """Adiciona a equipe ao contexto."""
        context = super().get_serializer_context()
        equipe = None
        user = self.request.user
        equipe_id_url = self.kwargs.get('equipe_pk')
        try:
            if equipe_id_url:
                equipe = get_object_or_404(Equipe, id=equipe_id_url, membros=user)
            else:
                 instance = self.get_object() if self.detail else None
                 if instance and hasattr(instance, 'equipe'):
                      equipe = instance.equipe
                      if not user.equipes.filter(id=equipe.id).exists():
                           raise Http404("Acesso negado à equipe deste objeto.")
                 elif self.action == 'create':
                      equipe_id_data = self.request.data.get('equipe_id')
                      if equipe_id_data:
                           equipe = get_object_or_404(Equipe, id=equipe_id_data, membros=user)
                      else:
                           equipe_detectada = get_equipe_atual(self.request)
                           if equipe_detectada:
                                equipe = equipe_detectada
            if equipe:
                 context['equipe'] = equipe
        except Http404:
            pass
        context['request'] = self.request
        return context


# --- ViewSets Específicos usando a Base ---
class ClienteViewSet(BaseEquipeFilteredViewSet):
    """API endpoint para Clientes, filtrado por equipes."""
    serializer_class = ClienteSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['bairro']
    search_fields = ['nome', 'codigo', 'endereco', 'telefone']
    ordering_fields = ['nome', 'codigo', 'bairro', 'updated_at']
    ordering = ['nome']


class ProdutoViewSet(BaseEquipeFilteredViewSet):
    """API endpoint para Produtos, filtrado por equipes."""
    serializer_class = ProdutoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['categoria']
    search_fields = ['nome', 'codigo', 'descricao']
    ordering_fields = ['nome', 'codigo', 'categoria', 'preco_base', 'updated_at']
    ordering = ['nome']


class FornecedorViewSet(BaseEquipeFilteredViewSet):
    """API endpoint para Fornecedores, filtrado por equipes."""
    serializer_class = FornecedorSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nome', 'codigo', 'contato', 'email', 'telefone']
    ordering_fields = ['nome', 'codigo', 'updated_at']
    ordering = ['nome']


# --- ViewSet para Entrega (ReadOnly) ---
class EntregaViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint para visualizar Entregas."""
    serializer_class = EntregaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filtra entregas baseadas nas encomendas das equipes do usuário."""
        user = self.request.user
        if user.is_authenticated:
            user_equipes_ids = user.equipes.values_list('id', flat=True)
            return Entrega.objects.filter(encomenda__equipe_id__in=user_equipes_ids).select_related(
                'encomenda', 'encomenda__cliente', 'encomenda__equipe'
            ).order_by('-encomenda__numero_encomenda')
        return Entrega.objects.none()

    @action(detail=True, methods=['post'], url_path='marcar-entregue')
    def marcar_entregue(self, request, pk=None):
        entrega = self.get_object()
        encomenda = entrega.encomenda

        if entrega.data_realizada:
            return Response({'detail': f'Entrega da encomenda #{encomenda.numero_encomenda} já está marcada como realizada.'},
                            status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        entrega.data_realizada = now
        entrega.data_entrega_realizada = now.date()
        entrega.hora_entrega = now.time()

        if not entrega.entregue_por:
            entrega.entregue_por = request.user.nome_completo or request.user.username

        entrega.save()

        if encomenda.status != 'entregue':
            encomenda.status = 'entregue'
            encomenda.save(update_fields=['status'])

        serializer = self.get_serializer(entrega)
        return Response(serializer.data)


# --- VIEWS DE API ANTIGAS/SEPARADAS (MANTIDAS) ---

@login_required # Ou use @api_view do DRF
@require_http_methods(["GET"])
def api_produto_info(request, produto_id):
    """Retorna informações do produto via AJAX. Verifica acesso da equipe."""
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({'error': 'Autenticação necessária'}, status=401)

    user_equipes_ids = user.equipes.values_list('id', flat=True)
    try:
        produto = Produto.objects.get(id=produto_id, equipe_id__in=user_equipes_ids)
        data = {
            'id': produto.id, # Inclui ID
            'nome': produto.nome,
            'codigo': produto.codigo,
            'preco_base': str(produto.preco_base), # Converte Decimal para string
            'categoria': produto.categoria,
            'descricao': produto.descricao,
            'equipe_id': str(produto.equipe_id) # Inclui ID da equipe
        }
        return JsonResponse(data)
    except Produto.DoesNotExist:
        return JsonResponse({'error': 'Produto não encontrado ou acesso não permitido'}, status=404)
    except Exception as e:
        print(f"Erro em api_produto_info: {e}") # Log de erro
        return JsonResponse({'error': 'Erro interno ao buscar produto'}, status=500)


@login_required # Ou use @api_view
@require_http_methods(["POST"])
def api_update_status(request, encomenda_pk):
    """Atualiza status da encomenda via AJAX. Verifica acesso da equipe."""
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({'error': 'Autenticação necessária'}, status=401)

    user_equipes_ids = user.equipes.values_list('id', flat=True)
    try:
        encomenda = get_object_or_404(Encomenda, pk=encomenda_pk, equipe_id__in=user_equipes_ids)

        new_status = request.POST.get('status')
        valid_statuses = [choice[0] for choice in Encomenda.STATUS_CHOICES]

        if not new_status or new_status not in valid_statuses:
            return JsonResponse({'error': 'Status inválido fornecido'}, status=400)

        old_status_display = encomenda.get_status_display()
        encomenda.status = new_status
        encomenda.save(update_fields=['status', 'updated_at']) # Inclui updated_at
        new_status_display = encomenda.get_status_display()

        return JsonResponse({
            'success': True,
            'status_code': new_status,
            'status_display': new_status_display,
            'message': f'Status alterado de "{old_status_display}" para "{new_status_display}"'
        })
    except Http404:
         return JsonResponse({'error': 'Encomenda não encontrada ou acesso negado'}, status=404)
    except Exception as e:
        print(f"Erro em api_update_status: {e}")
        return JsonResponse({'error': 'Erro interno ao atualizar status'}, status=500)


@login_required
@require_http_methods(["GET"])
def search_produtos(request):
    """API view for searching products (Select2) within user's teams."""
    search_term = request.GET.get('q', '').strip()
    equipe_id = request.GET.get('equipe_id')
    limit = int(request.GET.get('limit', 20))
    user = request.user
    if not user.is_authenticated: return JsonResponse({'error': 'Autenticação necessária'}, status=401)

    user_equipes = user.equipes.all()
    produtos = Produto.objects.filter(equipe__in=user_equipes)

    if equipe_id:
        try:
             equipe_uuid = uuid.UUID(equipe_id)
             if user_equipes.filter(id=equipe_uuid).exists():
                 produtos = produtos.filter(equipe_id=equipe_uuid)
             else:
                 return JsonResponse({'error': 'Acesso negado à equipe especificada'}, status=403)
        except (ValueError, TypeError):
             return JsonResponse({'error': 'ID de equipe inválido'}, status=400)

    if search_term:
        produtos = produtos.filter(
            Q(nome__icontains=search_term) | Q(codigo__icontains=search_term)
        )

    produtos = produtos.select_related('equipe').order_by('nome')[:limit]
    results = [{'id': p.id, 'text': f"{p.codigo} - {p.nome} ({p.equipe.nome})"} for p in produtos]
    return JsonResponse({'results': results})

# --- search_clientes ---
@login_required
@require_http_methods(["GET"])
def search_clientes(request):
    search_term = request.GET.get('q', '').strip()
    equipe_id = request.GET.get('equipe_id')
    limit = int(request.GET.get('limit', 20))
    user = request.user
    if not user.is_authenticated: return JsonResponse({'error': 'Autenticação necessária'}, status=401)

    user_equipes = user.equipes.all()
    clientes = Cliente.objects.filter(equipe__in=user_equipes)

    if equipe_id:
        try:
             equipe_uuid = uuid.UUID(equipe_id)
             if user_equipes.filter(id=equipe_uuid).exists():
                 clientes = clientes.filter(equipe_id=equipe_uuid)
             else:
                 return JsonResponse({'error': 'Acesso negado à equipe especificada'}, status=403)
        except (ValueError, TypeError):
              return JsonResponse({'error': 'ID de equipe inválido'}, status=400)

    if search_term:
        clientes = clientes.filter(
            Q(nome__icontains=search_term) | Q(codigo__icontains=search_term) | Q(telefone__icontains=search_term)
        )

    clientes = clientes.select_related('equipe').order_by('nome')[:limit]
    results = [{'id': c.id, 'text': f"{c.codigo} - {c.nome} ({c.equipe.nome})"} for c in clientes]
    return JsonResponse({'results': results})

# --- search_fornecedores ---
@login_required
@require_http_methods(["GET"])
def search_fornecedores(request):
    search_term = request.GET.get('q', '').strip()
    equipe_id = request.GET.get('equipe_id')
    limit = int(request.GET.get('limit', 20))
    user = request.user
    if not user.is_authenticated: return JsonResponse({'error': 'Autenticação necessária'}, status=401)

    user_equipes = user.equipes.all()
    fornecedores = Fornecedor.objects.filter(equipe__in=user_equipes)

    if equipe_id:
        try:
             equipe_uuid = uuid.UUID(equipe_id)
             if user_equipes.filter(id=equipe_uuid).exists():
                 fornecedores = fornecedores.filter(equipe_id=equipe_uuid)
             else:
                 return JsonResponse({'error': 'Acesso negado à equipe especificada'}, status=403)
        except (ValueError, TypeError):
             return JsonResponse({'error': 'ID de equipe inválido'}, status=400)

    if search_term:
        fornecedores = fornecedores.filter(
            Q(nome__icontains=search_term) | Q(codigo__icontains=search_term) | Q(contato__icontains=search_term)
        )

    fornecedores = fornecedores.select_related('equipe').order_by('nome')[:limit]
    results = [{'id': f.id, 'text': f"{f.codigo} - {f.nome} ({f.equipe.nome})"} for f in fornecedores]
    return JsonResponse({'results': results})


# --- Mantenha a view PDF ---
@login_required
def encomenda_pdf(request, pk):
    """Gera PDF para uma encomenda, verificando a associação à equipe."""
    user = request.user
    if not user.is_authenticated:
        # Embora @login_required já faça isso, é bom ter a checagem explícita
        # Em produção, você pode querer retornar um erro 401 ou redirecionar
        raise Http404("Autenticação necessária.")

    user_equipes_ids = user.equipes.values_list('id', flat=True)
    try:
        encomenda = get_object_or_404(
            Encomenda.objects.select_related('cliente', 'equipe'),
            pk=pk,
            equipe_id__in=user_equipes_ids
        )
        entrega = getattr(encomenda, 'entrega', None)
        # Filtra itens para garantir consistência da equipe
        itens = encomenda.itens.filter(
            produto__equipe=encomenda.equipe,
            fornecedor__equipe=encomenda.equipe
        ).select_related('produto', 'fornecedor').all()

        context = {'encomenda': encomenda, 'entrega': entrega, 'itens': itens}
        # Garante que o template PDF ainda exista no local correto (talvez mover para fora do app?)
        template = get_template('encomendas/encomenda_pdf.html')
        html = template.render(context)

        try:
            from weasyprint import HTML
            pdf = HTML(string=html).write_pdf()
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="encomenda_{encomenda.numero_encomenda}.pdf"'
            return response
        except ImportError:
            # Em vez de messages (que são para templates), retorna erro HTTP
            return HttpResponse("Erro: Biblioteca WeasyPrint não instalada. Instale com 'pip install weasyprint'.", status=500, content_type="text/plain")
        except Exception as e:
            print(f'Erro inesperado ao gerar PDF para encomenda {pk}: {e}')
            return HttpResponse("Erro inesperado ao gerar PDF.", status=500, content_type="text/plain")

    except Http404:
         return HttpResponse("Encomenda não encontrada ou acesso negado.", status=404, content_type="text/plain")
    except Exception as e:
        # Captura outros erros gerais
        print(f"Erro geral em encomenda_pdf para {pk}: {e}")
        return HttpResponse("Erro interno ao processar a solicitação do PDF.", status=500, content_type="text/plain")


# --- REMOVA ou COMENTE as views antigas que renderizavam HTML ---
# Ex: def encomenda_list(request): ... (substituída por EncomendaViewSet)
# Ex: def encomenda_detail(request, pk): ... (substituída por EncomendaViewSet)
# Ex: def cliente_list(request, equipe_id): ... (substituída por ClienteViewSet)
# Ex: def dashboard(request): ... (A lógica será do frontend)
# ... etc ...