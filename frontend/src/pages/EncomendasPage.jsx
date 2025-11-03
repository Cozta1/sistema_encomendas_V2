import React, { useState, useEffect, useCallback } from 'react';
import { Link, Navigate, useSearchParams } from 'react-router-dom';
import api from '../services/api';

// Constante para opções de status
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

  // Estados para filtros
  const [searchParams, setSearchParams] = useSearchParams();
  const [filters, setFilters] = useState({
    status: searchParams.get('status') || '',
    clienteId: searchParams.get('cliente__id') || '',
    equipeId: searchParams.get('equipe__id') || '', // <-- Estado para filtro de equipe
    search: searchParams.get('search') || '',
  });

  // Estados para carregar opções dos filtros
  const [clientesOptions, setClientesOptions] = useState([]);
  const [loadingClientes, setLoadingClientes] = useState(false);
  const [equipesOptions, setEquipesOptions] = useState([]); // <-- NOVO ESTADO
  const [loadingEquipes, setLoadingEquipes] = useState(false); // <-- NOVO ESTADO

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
    if (filters.equipeId) params.append('equipe__id', filters.equipeId); // <-- Já estava sendo enviado
    if (filters.search) params.append('search', filters.search);
    params.append('ordering', '-numero_encomenda'); // Ordena pela mais recente

    // Atualiza a URL do navegador com os filtros atuais
    setSearchParams(params, { replace: true });

    try {
      const response = await api.get(`/encomendas/?${params.toString()}`);
      
      const results = response.data.results || (Array.isArray(response.data) ? response.data : []);
      const count = response.data.count || results.length;

      setEncomendas(results);
      setTotalCount(count);

      // Calcula total de páginas
      const pageSize = results.length > 0 ? results.length : 20;
      const effectivePageSize = (pageSize === 0 && count > 0) ? 20 : (pageSize || 20);
      setTotalPages(Math.ceil(count / effectivePageSize));
      setCurrentPage(page);

    } catch (err) {
      console.error('Erro ao buscar encomendas:', err);
      setError('Falha ao carregar encomendas.');
    } finally {
      setLoading(false);
    }
  }, [filters, setSearchParams]);

  // Buscar dados iniciais ou quando a página/filtros na URL mudam
  useEffect(() => {
    const pageFromUrl = parseInt(searchParams.get('page') || '1', 10);
    // Atualiza o estado dos filtros com base na URL
    setFilters({
        status: searchParams.get('status') || '',
        clienteId: searchParams.get('cliente__id') || '',
        equipeId: searchParams.get('equipe__id') || '',
        search: searchParams.get('search') || '',
    });
    fetchData(pageFromUrl);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]); // Re-busca quando os parâmetros da URL mudam

  // Função para buscar clientes para o filtro
  useEffect(() => {
    const fetchClientes = async () => {
        setLoadingClientes(true);
        try {
            // Busca clientes (idealmente filtrados pela(s) equipe(s) do usuário)
            const response = await api.get(`/clientes/?page_size=1000`); // Busca "todos"
            const options = (response.data.results || response.data || [])
                .map(c => ({ value: c.id, label: `${c.codigo} - ${c.nome} (${c.equipe_nome || 'N/A'})` }))
                .sort((a, b) => a.label.localeCompare(b.label));
            setClientesOptions([{ value: '', label: 'Todos os clientes' }, ...options]);
        } catch (error) {
            console.error("Erro ao buscar clientes para filtro:", error);
            setClientesOptions([{ value: '', label: 'Erro ao carregar' }]);
        } finally {
            setLoadingClientes(false);
        }
    };
    fetchClientes();
  }, []); // Roda só uma vez

  // --- NOVO: Função para buscar equipes para o filtro ---
  useEffect(() => {
    const fetchEquipes = async () => {
        setLoadingEquipes(true);
        try {
            // Reutiliza o endpoint que já busca as equipes do usuário
            const response = await api.get('/my-teams-invites/');
            const options = response.data.teams 
                ? response.data.teams.map(team => ({ value: team.id, label: team.nome })) 
                : [];
            setEquipesOptions([{ value: '', label: 'Todas as equipes' }, ...options]);
        } catch (error) {
            console.error("Erro ao buscar equipes para filtro:", error);
            setEquipesOptions([{ value: '', label: 'Erro ao carregar' }]);
        } finally {
            setLoadingEquipes(false);
        }
    };
    fetchEquipes();
  }, []); // Roda só uma vez

  // Handlers para mudança nos filtros
  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    // Atualiza o estado local dos filtros
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  // Handler para aplicar os filtros
  const handleFilterSubmit = (e) => {
    e.preventDefault();
    // A função fetchData agora usará os valores do estado 'filters'
    // e setará os searchParams, o que disparará o useEffect de busca
    const params = new URLSearchParams();
    params.append('page', '1'); // Reseta para página 1
    if (filters.status) params.append('status', filters.status);
    if (filters.clienteId) params.append('cliente__id', filters.clienteId);
    if (filters.equipeId) params.append('equipe__id', filters.equipeId);
    if (filters.search) params.append('search', filters.search);
    setSearchParams(params, { replace: true });
  };

  const handleClearFilters = () => {
    setFilters({ status: '', clienteId: '', equipeId: '', search: '' });
    setSearchParams({ page: '1' }, { replace: true }); // Limpa URL e reseta página
  };

  // Handlers para paginação
  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      // Atualiza o 'page' nos searchParams, o que dispara o useEffect de busca
      const params = new URLSearchParams(searchParams);
      params.set('page', newPage.toString());
      setSearchParams(params, { replace: true });
    }
  };

  // --- Renderização ---
  const token = localStorage.getItem('accessToken');
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  // Define equipeId ativa para o botão "Nova Encomenda"
  const activeTeamId = filters.equipeId || sessionStorage.getItem('currentTeamId');

  return (
    <div>
      {/* Cabeçalho */}
      <div className="page-header">
        <div className="d-flex justify-content-between align-items-center">
          <div>
            <h1><i className="bi bi-clipboard-data me-3"></i>Encomendas</h1>
            <p className="mb-0 text-muted">Gerencie todas as encomendas acessíveis</p>
          </div>
          <Link
            to={activeTeamId ? `/encomendas/nova/equipe/${activeTeamId}` : '/equipes'}
            className={`btn btn-primary ${!activeTeamId ? 'disabled' : ''}`}
            title={!activeTeamId ? 'Selecione uma equipe na lista de equipes ou nos filtros para criar encomenda' : 'Nova Encomenda'}
          >
            <i className="bi bi-plus-circle me-2"></i>Nova Encomenda
          </Link>
        </div>
      </div>

      {/* --- Card de Filtros ATUALIZADO --- */}
      <div className="card mb-4">
        <div className="card-body">
          <form onSubmit={handleFilterSubmit} className="row g-3 align-items-end">
            
            {/* Filtro Status (col-md-3) */}
            <div className="col-lg-3 col-md-6">
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
            
            {/* Filtro Cliente (col-md-3) */}
            <div className="col-lg-3 col-md-6">
              <label htmlFor="clienteFilter" className="form-label">Cliente</label>
              <select
                id="clienteFilter"
                name="clienteId" // Corresponde a filters.clienteId
                className="form-select"
                value={filters.clienteId}
                onChange={handleFilterChange}
                disabled={loadingClientes}
              >
                {loadingClientes ? (
                    <option>Carregando...</option>
                ) : (
                    clientesOptions.map(option => (
                        <option key={option.value} value={option.value}>{option.label}</option>
                    ))
                )}
              </select>
            </div>
            
            {/* --- NOVO FILTRO EQUIPE (col-md-2) --- */}
            <div className="col-lg-2 col-md-6">
              <label htmlFor="equipeFilter" className="form-label">Equipe</label>
              <select
                id="equipeFilter"
                name="equipeId" // Corresponde a filters.equipeId
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
            
            {/* Filtro Busca (col-md-2) */}
            <div className="col-lg-2 col-md-6">
              <label htmlFor="searchFilter" className="form-label">Buscar</label>
              <input
                type="text"
                id="searchFilter"
                name="search"
                className="form-control"
                placeholder="Número, cliente..."
                value={filters.search}
                onChange={handleFilterChange}
              />
            </div>
            
            {/* Botões (col-md-2) */}
            <div className="col-lg-2 col-md-12 d-flex align-items-end"> {/* Ocupa 100% no md */}
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
      {/* --- Fim do Card de Filtros --- */}

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
                          <Link to={`/encomendas/${encomenda.numero_encomenda}`}>
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
                              <Link to={`/encomendas/${encomenda.numero_encomenda}/editar`} className="btn btn-outline-secondary" title="Editar"><i className="bi bi-pencil"></i></Link>
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