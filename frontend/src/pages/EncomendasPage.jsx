import React, { useState, useEffect, useCallback } from 'react';
import { Link, Navigate, useSearchParams } from 'react-router-dom';
import api from '../services/api';

// (Opcional) Importar componentes UI (Table, Button, Form, InputGroup, Pagination from react-bootstrap or MUI)

// Constante para opções de status (pode vir da API ou ser definida aqui)
const STATUS_CHOICES = [
    { value: '', label: 'Todos os status' },
    { value: 'criada', label: 'Criada' },
    { value: 'cotacao', label: 'Em Cotação' },
    { value: 'aprovada', label: 'Aprovada' },
    { value: 'em_andamento', label: 'Em Andamento' },
    { value: 'pronta', label: 'Pronta para Entrega' },
    { value: 'entregue', label: 'Entregue' },
    { value: 'cancelada', label: 'Cancelada' },
];

function EncomendasPage() {
  const [encomendas, setEncomendas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Estados para paginação
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  // Estados para filtros - inicializados pelos query params da URL
  const [searchParams, setSearchParams] = useSearchParams();
  const [filters, setFilters] = useState({
    status: searchParams.get('status') || '',
    clienteId: searchParams.get('cliente__id') || '', // Nome do parâmetro como na API
    equipeId: searchParams.get('equipe__id') || '',   // Nome do parâmetro como na API
    search: searchParams.get('search') || '',
  });

  // Estado para carregar clientes (para o dropdown de filtro)
  const [clientesOptions, setClientesOptions] = useState([]);
  const [loadingClientes, setLoadingClientes] = useState(false);


  const [equipesOptions, setEquipesOptions] = useState([]);
  const [loadingEquipes, setLoadingEquipes] = useState(false);

  // --- Funções ---

  // Função para buscar dados com filtros e paginação
  const fetchData = useCallback(async (page = 1) => {
    setLoading(true);
    setError(null);

    // Constrói os query parameters
    const params = new URLSearchParams();
    params.append('page', page.toString());
    if (filters.status) params.append('status', filters.status);
    if (filters.clienteId) params.append('cliente__id', filters.clienteId);
    if (filters.equipeId) params.append('equipe__id', filters.equipeId);
    if (filters.search) params.append('search', filters.search);
    // Adicionar ordenação se necessário: params.append('ordering', '-numero_encomenda');

    // Atualiza a URL do navegador com os filtros atuais
    setSearchParams(params);

    try {
      const response = await api.get(`/encomendas/?${params.toString()}`);
      setEncomendas(response.data.results || []);
      setTotalCount(response.data.count || 0);
      // Calcula total de páginas (assumindo que a API não retorna 'total_pages')
      const pageSize = response.data.results?.length > 0 ? response.data.results.length : 20; // Ou pegue PAGE_SIZE do settings
      setTotalPages(Math.ceil((response.data.count || 0) / pageSize));
      setCurrentPage(page);

    } catch (err) {
      console.error('Erro ao buscar encomendas:', err);
      setError('Falha ao carregar encomendas.');
      // Tratar erros 401/403 se necessário
    } finally {
      setLoading(false);
    }
  }, [filters, setSearchParams]); // Depende dos filtros e da função de atualizar URL

  // Buscar dados iniciais ou quando a página muda (vinda da URL)
  useEffect(() => {
    const pageFromUrl = parseInt(searchParams.get('page') || '1', 10);
    fetchData(pageFromUrl);
  }, [fetchData, searchParams]); // Re-busca se fetchData mudar ou searchParams (ex: back button)

  // Função para buscar clientes para o filtro (apenas uma vez ou quando equipe mudar)
  // ** MELHORIA FUTURA: Usar um Select2/Autocomplete que busca dinamicamente **
  useEffect(() => {
    const fetchClientes = async () => {
        setLoadingClientes(true);
        try {
            // Busca TODOS os clientes acessíveis (pode ser muitos!)
            // Idealmente, usar um componente de busca/autocomplete aqui
            const params = new URLSearchParams();
            if (filters.equipeId) { // Filtra clientes se uma equipe estiver selecionada
                params.append('equipe__id', filters.equipeId);
            }
             // Adicionar `page_size=all` ou um limite alto se a API suportar
            const response = await api.get(`/clientes/?${params.toString()}`); // Endpoint de clientes
            const options = response.data.results ? response.data.results.map(c => ({ value: c.id, label: `${c.codigo} - ${c.nome} (${c.equipe_nome})` })) : (Array.isArray(response.data) ? response.data.map(c => ({ value: c.id, label: `${c.codigo} - ${c.nome}` })) : []);
            setClientesOptions([{ value: '', label: 'Todos os clientes' }, ...options]);
        } catch (error) {
            console.error("Erro ao buscar clientes para filtro:", error);
            setClientesOptions([{ value: '', label: 'Erro ao carregar' }]);
        } finally {
            setLoadingClientes(false);
        }
    };
    fetchClientes();
  }, [filters.equipeId]); // Re-busca clientes se a equipe selecionada mudar


   
  // Busca as equipes do usuário para o dropdown de filtro
  useEffect(() => {
    const fetchUserTeams = async () => {
        setLoadingEquipes(true);
        try {
            // Reutiliza o endpoint que busca equipes e convites, pegando só as equipes
            const response = await api.get('/my-teams-invites/');
            // Formata para o dropdown: { value: id, label: nome }
            const options = response.data.teams
                ? response.data.teams.map(team => ({ value: team.id, label: team.nome }))
                : [];
            // Adiciona a opção "Todas" no início
            setEquipesOptions([{ value: '', label: 'Todas as minhas equipes' }, ...options]);
        } catch (error) {
            console.error("Erro ao buscar equipes para filtro:", error);
            setEquipesOptions([{ value: '', label: 'Erro ao carregar equipes' }]);
        } finally {
            setLoadingEquipes(false);
        }
    };
    fetchUserTeams();
}, []); // Roda apenas uma vez ao montar


  // Handlers para mudança nos filtros
  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  const handleFilterSubmit = (e) => {
    e.preventDefault();
    fetchData(1); // Volta para a primeira página ao aplicar novos filtros
  };

  const handleClearFilters = () => {
    setFilters({ status: '', clienteId: '', equipeId: '', search: '' });
    // Limpa searchParams E inicia busca na página 1 (será pego pelo useEffect)
    setSearchParams({ page: '1' });
  };

  // Handlers para paginação
  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      fetchData(newPage);
    }
  };

  // --- Renderização ---
  const token = localStorage.getItem('accessToken');
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  // Define equipeId ativa para o botão "Nova Encomenda"
  const activeTeamIdForNew = filters.equipeId || sessionStorage.getItem('currentTeamId');

  return (
    <div>
      {/* Cabeçalho */}
      <div className="page-header">
        <div className="d-flex justify-content-between align-items-center">
          <div>
            <h1><i className="bi bi-clipboard-data me-3"></i>Encomendas</h1>
            <p className="mb-0 text-muted">Gerencie todas as encomendas acessíveis</p>
          </div>
          {/* Botão Nova Encomenda - Tenta usar a equipe do filtro ou a da sessão */}
          <Link
          to={activeTeamIdForNew ? `/encomendas/nova/equipe/${activeTeamIdForNew}` : '/equipes'}
          className={`btn btn-primary ${!activeTeamIdForNew ? 'disabled' : ''}`}
          title={!activeTeamIdForNew ? 'Selecione uma equipe nos filtros ou na lista de equipes para criar encomenda' : 'Nova Encomenda'}>
          <i className="bi bi-plus-circle me-2"></i>Nova Encomenda
          </Link>
        </div>
      </div>

      {/* Card de Filtros */}
      <div className="card mb-4">
        <div className="card-body">
          <form onSubmit={handleFilterSubmit} className="row g-3 align-items-end">
            {/* NOVO: Filtro Equipe */}
            <div className="col-md-2"> {/* Ou ajuste o tamanho das colunas */}
              <label htmlFor="equipeFilter" className="form-label">Equipe</label>
              <select
                id="equipeFilter"
                name="equipeId" // Nome do estado
                className="form-select"
                value={filters.equipeId}
                onChange={handleFilterChange}
                disabled={loadingEquipes}
              >
                {loadingEquipes ? (
                    <option>Carregando...</option>
                ) : (
                    equipesOptions.map(option => (
                        <option key={option.value} value={option.value}>{option.label}</option>
                    ))
                )}
              </select>
            </div>


            {/* Filtro Status */}
            <div className="col-md-3">
              <label htmlFor="statusFilter" className="form-label">Status</label>
              <select
                id="statusFilter"
                name="status"
                className="form-select"
                value={filters.status}
                onChange={handleFilterChange}
              >
                {STATUS_CHOICES.map(option => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </div>
            {/* Filtro Cliente */}
            <div className="col-md-3">
              <label htmlFor="clienteFilter" className="form-label">Cliente</label>
              <select
                id="clienteFilter"
                name="clienteId"
                className="form-select"
                value={filters.clienteId}
                onChange={handleFilterChange}
                disabled={loadingClientes} // Desabilita enquanto carrega
              >
                {loadingClientes ? (
                    <option>Carregando clientes...</option>
                ) : (
                    clientesOptions.map(option => (
                        <option key={option.value} value={option.value}>{option.label}</option>
                    ))
                )}
              </select>
            </div>
             {/* Filtro Equipe (Opcional, se quiser filtrar aqui também) */}
             {/* <div className="col-md-2"> ... dropdown de equipes ... </div> */}

            {/* Filtro Busca */}
            <div className="col-md-4">
              <label htmlFor="searchFilter" className="form-label">Buscar</label>
              <input
                type="text"
                id="searchFilter"
                name="search"
                className="form-control"
                placeholder="Número, cliente, produto..."
                value={filters.search}
                onChange={handleFilterChange}
              />
            </div>
            {/* Botões */}
            <div className="col-md-2 d-flex">
              <button type="submit" className="btn btn-primary me-2 flex-grow-1">
                <i className="bi bi-search me-1"></i>Filtrar
              </button>
              <button type="button" onClick={handleClearFilters} className="btn btn-outline-secondary" title="Limpar Filtros">
                <i className="bi bi-x-circle"></i>
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Indicador de Loading e Erro */}
      {loading && <div className="text-center my-3"><span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Carregando...</div>}
      {error && <div className="alert alert-danger">{error}</div>}

      {/* Tabela de Encomendas */}
      {!loading && !error && (
        <div className="card">
          <div className="card-header d-flex justify-content-between align-items-center">
            <h5 className="mb-0">
              <i className="bi bi-list-ul me-2"></i>
              {totalCount} encomenda(s) encontrada(s)
            </h5>
            {totalPages > 1 && (
              <small className="text-muted">Página {currentPage} de {totalPages}</small>
            )}
          </div>
          <div className="card-body p-0">
            {encomendas.length === 0 ? (
              <div className="text-center p-5">
                 <i className="bi bi-inbox text-muted" style={{ fontSize: '3rem' }}></i>
                 <h5 className="text-muted mt-3">Nenhuma encomenda encontrada</h5>
                 <p className="text-muted">Tente ajustar os filtros ou crie uma nova encomenda.</p>
              </div>
            ) : (
              <div className="table-responsive">
                <table className="table table-hover mb-0">
                  <thead>
                    <tr>
                      <th>Número</th>
                      <th>Cliente</th>
                      <th>Equipe</th>
                      <th>Status</th>
                      <th>Data Criação</th>
                      <th>Responsável</th>
                      <th>Valor Total</th>
                      <th>Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {encomendas.map((encomenda) => (
                      <tr key={encomenda.numero_encomenda}>
                        <td>
                          <Link to={`/encomendas/${encomenda.numero_encomenda}`}> {/* Rota de detalhe a ser criada */}
                            <strong>#{encomenda.numero_encomenda}</strong>
                          </Link>
                        </td>
                        <td>{encomenda.cliente_nome}</td>
                        <td>{encomenda.equipe_nome}</td>
                        <td><span className={`status-badge status-${encomenda.status}`}>{encomenda.status_display}</span></td>
                        <td>{new Date(encomenda.data_criacao).toLocaleDateString('pt-BR')}</td>
                        <td>{encomenda.responsavel_criacao}</td>
                        <td><strong>R$ {parseFloat(encomenda.valor_total).toFixed(2)}</strong></td>
                        <td>
                           <div className="btn-group btn-group-sm">
                              <Link to={`/encomendas/${encomenda.numero_encomenda}`} className="btn btn-outline-primary" title="Ver Detalhes"><i className="bi bi-eye"></i></Link>
                              <Link to={`/encomendas/${encomenda.numero_encomenda}/editar`} className="btn btn-outline-secondary" title="Editar"><i className="bi bi-pencil"></i></Link> {/* Rota a ser criada */}
                               {/* Adicionar botão Excluir com confirmação */}
                               <button onClick={() => {/* Lógica de exclusão */}} className="btn btn-outline-danger" title="Excluir" disabled><i className="bi bi-trash"></i></button>
                           </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Paginação */}
          {totalPages > 1 && (
            <div className="card-footer d-flex justify-content-center">
              <nav aria-label="Navegação de páginas">
                <ul className="pagination mb-0">
                  <li className={`page-item ${currentPage === 1 ? 'disabled' : ''}`}>
                    <button className="page-link" onClick={() => handlePageChange(currentPage - 1)} aria-label="Anterior">
                      <span aria-hidden="true">&laquo;</span>
                    </button>
                  </li>
                  {/* Gerar números de página (simplificado) */}
                   {[...Array(totalPages).keys()].map(num => {
                       const pageNum = num + 1;
                       // Lógica para mostrar apenas algumas páginas (ex: atual, +-2, primeira, última)
                       if (pageNum === 1 || pageNum === totalPages || (pageNum >= currentPage - 2 && pageNum <= currentPage + 2)) {
                           return (
                               <li key={pageNum} className={`page-item ${currentPage === pageNum ? 'active' : ''}`}>
                                   <button className="page-link" onClick={() => handlePageChange(pageNum)}>{pageNum}</button>
                               </li>
                           );
                       } else if (pageNum === currentPage - 3 || pageNum === currentPage + 3) {
                           return <li key={pageNum} className="page-item disabled"><span className="page-link">...</span></li>;
                       }
                       return null;
                   })}

                  <li className={`page-item ${currentPage === totalPages ? 'disabled' : ''}`}>
                    <button className="page-link" onClick={() => handlePageChange(currentPage + 1)} aria-label="Próxima">
                      <span aria-hidden="true">&raquo;</span>
                    </button>
                  </li>
                </ul>
              </nav>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default EncomendasPage;
