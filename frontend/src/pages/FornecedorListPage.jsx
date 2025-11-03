import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link, Navigate, useSearchParams } from 'react-router-dom';
import api from '../services/api';

function FornecedorListPage() {
  const { equipeId } = useParams(); // Pega o ID da equipe da URL
  const [searchParams, setSearchParams] = useSearchParams(); // Para filtros e paginação na URL
  const [fornecedores, setFornecedores] = useState([]);
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

  // Função para buscar dados
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

    setSearchParams(params, { replace: true });

    try {
      // Busca os fornecedores
      const response = await api.get(`/fornecedores/?${params.toString()}`);
      
      const results = response.data.results || (Array.isArray(response.data) ? response.data : []);
      const count = response.data.count || results.length;
      
      setFornecedores(results);
      setTotalCount(count);

      const pageSize = results.length > 0 ? results.length : 20; 
      setTotalPages(Math.ceil(count / pageSize));
      setCurrentPage(page);

      // Tenta buscar o nome da equipe
      if (results.length > 0 && results[0].equipe_nome) {
           setEquipeNome(results[0].equipe_nome);
      } else if (fornecedores.length === 0 && totalCount === 0) { 
           try {
               const teamData = await api.get('/my-teams-invites/');
               const foundTeam = teamData.data.teams.find(t => t.id === equipeId);
               setEquipeNome(foundTeam ? foundTeam.nome : `Equipe ${equipeId.substring(0,8)}...`);
           // eslint-disable-next-line no-unused-vars
           } catch (teamErr) { setEquipeNome(`Equipe ${equipeId.substring(0,8)}...`); }
      }

    } catch (err) {
      console.error(`Erro ao buscar fornecedores para equipe ${equipeId}:`, err);
      if (err.response && (err.response.status === 401 || err.response.status === 403 || err.response.status === 404)) {
        setError('Acesso negado ou equipe não encontrada.');
      } else {
        setError('Falha ao carregar lista de fornecedores.');
      }
    } finally {
      setLoading(false);
    }
  }, [equipeId, searchTerm, setSearchParams, fornecedores.length, totalCount]);

  // Busca inicial
  useEffect(() => {
    const pageFromUrl = parseInt(searchParams.get('page') || '1', 10);
    const searchFromUrl = searchParams.get('search') || '';
    if (searchFromUrl !== searchTerm) setSearchTerm(searchFromUrl);
    fetchData(pageFromUrl, searchFromUrl);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [equipeId, searchParams]); 

  // Handlers para busca
  const handleSearchChange = (e) => setSearchTerm(e.target.value);
  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchData(1, searchTerm); 
  };
  const handleClearSearch = () => {
    setSearchTerm('');
    fetchData(1, ''); 
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
            <h1><i className="bi bi-truck me-3"></i>Fornecedores {equipeNome ? `- ${equipeNome}` : ''}</h1>
            <p className="mb-0 text-muted">Gerencie os fornecedores da equipe</p>
          </div>
          <Link to={`/fornecedores/novo/equipe/${equipeId}`} className="btn btn-primary">
            <i className="bi bi-plus-circle me-2"></i>Novo Fornecedor
          </Link>
        </div>
      </div>

      {/* Filtro de Busca */}
      <div className="card mb-4">
        <div className="card-body">
          <form onSubmit={handleSearchSubmit} className="row g-3 align-items-end">
            <div className="col-md-8">
              <label htmlFor="searchFilter" className="form-label">Buscar Fornecedor</label>
              <input
                type="text"
                id="searchFilter"
                name="search"
                className="form-control"
                placeholder="Nome, código, contato, e-mail..."
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

      {/* Tabela de Fornecedores */}
      {!loading && !error && (
        <div className="card">
          <div className="card-header d-flex justify-content-between align-items-center">
            <h5 className="mb-0">
              <i className="bi bi-list-ul me-2"></i>
              {totalCount} fornecedor(es) encontrado(s)
            </h5>
             {totalPages > 1 && (<small className="text-muted">Página {currentPage} de {totalPages}</small>)}
          </div>
          <div className="card-body p-0">
            {fornecedores.length === 0 ? (
              <div className="text-center p-5">
                <i className="bi bi-truck text-muted" style={{ fontSize: '3rem' }}></i>
                <h5 className="text-muted mt-3">Nenhum fornecedor encontrado</h5>
                <p className="text-muted">{searchTerm ? 'Tente ajustar a busca.' : 'Cadastre o primeiro fornecedor para esta equipe!'}</p>
                <Link to={`/fornecedores/novo/equipe/${equipeId}`} className="btn btn-primary mt-2">
                   <i className="bi bi-plus-circle me-2"></i>Novo Fornecedor
                </Link>
              </div>
            ) : (
              <div className="table-responsive">
                <table className="table table-hover mb-0">
                  <thead>
                    <tr>
                      <th>Código</th>
                      <th>Nome</th>
                      <th>Contato</th>
                      <th>Telefone</th>
                      <th>E-mail</th>
                      {/* <th>Uso (Encomendas)</th> */}
                      <th>Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {fornecedores.map(fornecedor => (
                      <tr key={fornecedor.id ?? fornecedor.pk}>
                        <td><strong>{fornecedor.codigo}</strong></td>
                        <td><strong>{fornecedor.nome}</strong></td>
                        <td>{fornecedor.contato || '-'}</td>
                        <td>{fornecedor.telefone || '-'}</td>
                        <td>{fornecedor.email ? <a href={`mailto:${fornecedor.email}`}>{fornecedor.email}</a> : '-'}</td>
                        {/* <td><span className="badge bg-primary">?</span></td> */}
                        <td>
                          <div className="btn-group btn-group-sm">
                            <Link to={`/encomendas/nova/equipe/${equipeId}?fornecedor_id=${fornecedor.id ?? fornecedor.pk}`} className="btn btn-outline-success" title="Nova Encomenda com este Fornecedor">
                              <i className="bi bi-plus-circle"></i>
                            </Link>
                            <Link to={`/fornecedores/${fornecedor.id ?? fornecedor.pk}/editar/equipe/${equipeId}`} className="btn btn-outline-secondary" title="Editar Fornecedor">
                              <i className="bi bi-pencil"></i>
                            </Link>
                            <button onClick={() => {/* TODO: Lógica de exclusão */}} className="btn btn-outline-danger" title="Excluir Fornecedor" disabled>
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
               <nav aria-label="Navegação de páginas de fornecedores">
                 <ul className="pagination mb-0">
                   <li className={`page-item ${currentPage === 1 ? 'disabled' : ''}`}>
                     <button className="page-link" onClick={() => handlePageChange(currentPage - 1)}>&laquo;</button>
                   </li>
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

export default FornecedorListPage;