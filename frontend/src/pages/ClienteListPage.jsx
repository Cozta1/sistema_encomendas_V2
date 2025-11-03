import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link, Navigate, useSearchParams } from 'react-router-dom';
import api from '../services/api';

// (Opcional) Importar componentes UI (Table, Button, Form, InputGroup, Pagination, Spinner etc.)

function ClienteListPage() {
  const { equipeId } = useParams(); // Pega o ID da equipe da URL
  const [searchParams, setSearchParams] = useSearchParams(); // Para filtros e paginação na URL
  const [clientes, setClientes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [equipeNome, setEquipeNome] = useState(''); // Para exibir o nome da equipe

  // Estados para paginação
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  // Estado para filtro de busca
  const [searchTerm, setSearchTerm] = useState(searchParams.get('search') || '');

  const token = localStorage.getItem('accessToken');

  // Função para buscar dados dos clientes
  const fetchData = useCallback(async (page = 1, currentSearch = searchTerm) => {
    if (!equipeId) {
        setError("ID da Equipe não encontrado na URL.");
        setLoading(false);
        return;
    }
    setLoading(true);
    setError(null);

    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('equipe__id', equipeId); // Filtra pela equipe da URL
    if (currentSearch) {
        params.append('search', currentSearch);
    }
    params.append('ordering', 'nome'); // Ordenar por nome

    // Atualiza a URL
    setSearchParams(params, { replace: true }); // replace: true para não poluir histórico do navegador

    try {
      // Busca os clientes filtrados pela equipe e busca
      const response = await api.get(`/clientes/?${params.toString()}`);
      
      // Lida com resposta paginada (com .results) ou não paginada (array direto)
      const results = response.data.results || (Array.isArray(response.data) ? response.data : []);
      const count = response.data.count || results.length;
      
      setClientes(results);
      setTotalCount(count);

      // Calcula total de páginas
      const pageSize = results.length > 0 ? results.length : 20; // Default page size
      // Garante que pageSize não seja 0 se a API retornar array vazio em página > 1
      const effectivePageSize = (pageSize === 0 && totalCount > 0) ? 20 : pageSize; 
      setTotalPages(Math.ceil(count / effectivePageSize));
      setCurrentPage(page);

      // Tenta buscar o nome da equipe
      if (results.length > 0 && results[0].equipe_nome) {
           setEquipeNome(results[0].equipe_nome);
      } else if (clientes.length === 0) { // Busca nome se a lista atual (do state) estiver vazia
           try {
               // Tenta buscar o nome da equipe (endpoint de EquipesPage)
               const teamData = await api.get('/my-teams-invites/');
               const foundTeam = teamData.data.teams.find(t => t.id === equipeId);
               if (foundTeam) {
                   setEquipeNome(foundTeam.nome);
               } else {
                   setEquipeNome(`Equipe ${equipeId.substring(0,8)}...`);
               }
           } catch (teamErr) { 
               console.error("Erro ao buscar nome da equipe:", teamErr); 
               setEquipeNome(`Equipe ${equipeId.substring(0,8)}...`); 
           }
      }

    } catch (err) {
      console.error(`Erro ao buscar clientes para equipe ${equipeId}:`, err);
      if (err.response && (err.response.status === 401 || err.response.status === 403 || err.response.status === 404)) {
        setError('Acesso negado ou equipe não encontrada.');
      } else {
        setError('Falha ao carregar lista de clientes.');
      }
    } finally {
      setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [equipeId, searchTerm, setSearchParams]); // Removido clientes.length para evitar loops

  // Busca inicial
  useEffect(() => {
    const pageFromUrl = parseInt(searchParams.get('page') || '1', 10);
    const searchFromUrl = searchParams.get('search') || '';
    // Atualiza o estado do termo de busca SE a URL mudar (ex: botão voltar)
    if (searchFromUrl !== searchTerm) {
        setSearchTerm(searchFromUrl);
    }
    fetchData(pageFromUrl, searchFromUrl);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [equipeId, searchParams]); // Depende apenas do equipeId e dos searchParams

  // Handlers para busca
  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchData(1, searchTerm); // Busca na página 1 com o novo termo
  };

  const handleClearSearch = () => {
    setSearchTerm('');
    fetchData(1, ''); // Busca na página 1 sem termo
  };

  // Handlers para paginação
  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      fetchData(newPage, searchTerm);
    }
  };

  // --- Renderização ---
  if (!token) return <Navigate to="/login" replace />;

  if (!equipeId) {
       return (
           <div style={{ padding: '20px' }} className="alert alert-danger">
               Erro: Nenhuma equipe selecionada. <br />
               <Link to="/equipes" className="alert-link">Selecione uma equipe primeiro.</Link>
           </div>
       );
  }
  
  return (
    <div>
      {/* Cabeçalho */}
      <div className="page-header">
        <div className="d-flex justify-content-between align-items-center">
          <div>
            <h1><i className="bi bi-people me-3"></i>Clientes {equipeNome ? `- ${equipeNome}` : ''}</h1>
            <p className="mb-0 text-muted">Gerencie os clientes da equipe</p>
          </div>
          <Link to={`/clientes/novo/equipe/${equipeId}`} className="btn btn-primary">
            <i className="bi bi-person-plus me-2"></i>Novo Cliente
          </Link>
        </div>
      </div>

       {/* Filtro de Busca */}
       <div className="card mb-4">
         <div className="card-body">
           <form onSubmit={handleSearchSubmit} className="row g-3 align-items-end">
             <div className="col-md-8">
               <label htmlFor="searchFilter" className="form-label">Buscar Cliente</label>
               <input
                 type="text"
                 id="searchFilter"
                 name="search"
                 className="form-control"
                 placeholder="Nome, código, telefone..."
                 value={searchTerm}
                 onChange={handleSearchChange}
               />
             </div>
             <div className="col-md-4 d-flex">
               <button type="submit" className="btn btn-primary me-2 flex-grow-1">
                 <i className="bi bi-search me-1"></i>Buscar
               </button>
               <button type="button" onClick={handleClearSearch} className="btn btn-outline-secondary" title="Limpar Busca">
                 <i className="bi bi-x-circle"></i>
               </button>
             </div>
           </form>
         </div>
       </div>

      {/* Loading / Erro */}
      {loading && <div className="text-center my-4"><span className="spinner-border" role="status"></span> Carregando...</div>}
      {error && !loading && (
         <div className="alert alert-danger">
             {error} <Link to="/equipes" className="alert-link ms-2">Voltar para equipes</Link>
         </div>
      )}

      {/* Tabela de Clientes */}
      {!loading && !error && (
        <div className="card">
          <div className="card-header d-flex justify-content-between align-items-center">
            <h5 className="mb-0">
              <i className="bi bi-list-ul me-2"></i>
              {totalCount} cliente(s) encontrado(s)
            </h5>
             {totalPages > 1 && (<small className="text-muted">Página {currentPage} de {totalPages}</small>)}
          </div>
          <div className="card-body p-0">
            {clientes.length === 0 ? (
              <div className="text-center p-5">
                <i className="bi bi-person-x text-muted" style={{ fontSize: '3rem' }}></i>
                <h5 className="text-muted mt-3">Nenhum cliente encontrado</h5>
                <p className="text-muted">
                  {searchTerm ? 'Tente ajustar a busca.' : 'Cadastre o primeiro cliente para esta equipe!'}
                </p>
                <Link to={`/clientes/novo/equipe/${equipeId}`} className="btn btn-primary mt-2">
                   <i className="bi bi-person-plus me-2"></i>Novo Cliente
                </Link>
              </div>
            ) : (
              <div className="table-responsive">
                <table className="table table-hover mb-0">
                  <thead>
                    <tr>
                      <th>Código</th>
                      <th>Nome</th>
                      <th>Bairro</th>
                      <th>Telefone</th>
                      {/* <th>Encomendas (Equipe)</th> */}
                      <th>Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {clientes.map(cliente => (
                      <tr key={cliente.id ?? cliente.pk}>
                        <td><strong>{cliente.codigo}</strong></td>
                        <td>
                          <div>
                            <strong>{cliente.nome}</strong><br />
                            <small className="text-muted">{cliente.endereco?.substring(0, 50) + (cliente.endereco?.length > 50 ? '...' : '')}</small>
                          </div>
                        </td>
                        <td>{cliente.bairro}</td>
                        <td>{cliente.telefone || '-'}</td>
                        {/* <td><span className="badge bg-primary">{cliente.encomendas_equipe_count ?? '?'}</span></td> */}
                        <td>
                          <div className="btn-group btn-group-sm">
                            <Link to={`/encomendas?cliente__id=${cliente.id ?? cliente.pk}&equipe__id=${equipeId}`} className="btn btn-outline-primary" title="Ver Encomendas">
                              <i className="bi bi-clipboard-data"></i>
                            </Link>
                            <Link to={`/encomendas/nova/equipe/${equipeId}?cliente_id=${cliente.id ?? cliente.pk}`} className="btn btn-outline-success" title="Nova Encomenda">
                              <i className="bi bi-plus-circle"></i>
                            </Link>
                            
                            {/* --- LINK DE EDIÇÃO ATUALIZADO --- */}
                            <Link 
                              to={`/clientes/${cliente.id ?? cliente.pk}/editar/equipe/${equipeId}`} 
                              className="btn btn-outline-secondary" 
                              title="Editar Cliente"
                            >
                              <i className="bi bi-pencil"></i>
                            </Link>

                            {/* Botão Excluir (implementar lógica depois) */}
                            <button onClick={() => {/* TODO: Implementar exclusão */}} className="btn btn-outline-danger" title="Excluir Cliente" disabled>
                              <i className="bi bi-trash"></i>
                            </button>
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
               <nav aria-label="Navegação de páginas de clientes">
                 <ul className="pagination mb-0">
                   <li className={`page-item ${currentPage === 1 ? 'disabled' : ''}`}>
                     <button className="page-link" onClick={() => handlePageChange(currentPage - 1)}>&laquo;</button>
                   </li>
                   {/* Lógica de números de página (simplificada) */}
                   {[...Array(totalPages).keys()].map(num => {
                       const pageNum = num + 1;
                       if (pageNum === 1 || pageNum === totalPages || (pageNum >= currentPage - 2 && pageNum <= currentPage + 2)) {
                           return ( <li key={pageNum} className={`page-item ${currentPage === pageNum ? 'active' : ''}`}> <button className="page-link" onClick={() => handlePageChange(pageNum)}>{pageNum}</button> </li> );
                       } else if (pageNum === currentPage - 3 || pageNum === currentPage + 3) {
                           return <li key={pageNum} className="page-item disabled"><span className="page-link">...</span></li>;
                       }
                       return null;
                   })}
                   <li className={`page-item ${currentPage === totalPages ? 'disabled' : ''}`}>
                     <button className="page-link" onClick={() => handlePageChange(currentPage + 1)}>&raquo;</button>
                   </li>
                 </ul>
               </nav>
             </div>
           )}
        </div>
      )}

      <div className="mt-4">
         <Link to={`/dashboard/${equipeId}`} className="btn btn-secondary">
             <i className="bi bi-arrow-left me-2"></i>Voltar ao Dashboard
         </Link>
      </div>
    </div>
  );
}

export default ClienteListPage;

