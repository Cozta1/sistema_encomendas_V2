import React, { useState, useEffect } from 'react';
import { useParams, Link, Navigate } from 'react-router-dom';
import api from '../services/api';

// (Opcional) Importar componentes UI (Card, Row, Col, Button, Table, Badge from react-bootstrap or MUI)

function TeamDashboardPage() {
  const { equipeId } = useParams(); // Pega o ID da equipe da URL
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const token = localStorage.getItem('accessToken'); // Verifica autenticação

  useEffect(() => {
    // Define a equipe ativa no sessionStorage sempre que entrar nesta página
    // (Redundante se já feito ao clicar no link, mas garante consistência)
    if (equipeId) {
        sessionStorage.setItem('currentTeamId', equipeId);
    }

    const fetchDashboardData = async () => {
      if (!equipeId) {
        setError("ID da equipe não encontrado na URL.");
        setLoading(false);
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const response = await api.get(`/equipes/${equipeId}/dashboard-data/`);
        setDashboardData(response.data);
      } catch (err) {
        console.error(`Erro ao buscar dados do dashboard para equipe ${equipeId}:`, err);
        if (err.response) {
             if (err.response.status === 401 || err.response.status === 403 || err.response.status === 404) {
                setError('Acesso negado ou equipe não encontrada.');
                // Idealmente, redirecionar para lista de equipes ou login
             } else {
                setError('Erro ao carregar dados do dashboard.');
             }
        } else {
             setError('Erro de conexão.');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [equipeId]); // Re-executa se o equipeId na URL mudar

  // --- Renderização ---

  // Redireciona se não estiver logado
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (loading) {
    return <div style={{ padding: '20px' }}>Carregando dashboard da equipe...</div>;
  }

  if (error) {
    return (
        <div style={{ padding: '20px', color: 'red' }}>
            Erro: {error} <br />
            <Link to="/equipes">Voltar para a lista de equipes</Link>
        </div>
    );
  }

  if (!dashboardData) {
    return (
        <div style={{ padding: '20px' }}>
            Não foi possível carregar os dados do dashboard. <br/>
            <Link to="/equipes">Voltar para a lista de equipes</Link>
        </div>
    );
  }

  const { team_info, stats, recent_orders } = dashboardData;

  return (
    <div>
      {/* Cabeçalho */}
      <div className="page-header">
        <h1><i className="bi bi-speedometer2 me-3"></i>Dashboard - {team_info?.nome || 'Equipe'}</h1>
        <p className="mb-0 text-muted">{team_info?.descricao || `Visão geral da equipe ${equipeId}`}</p>
      </div>

      {/* Estatísticas */}
      <div className="row mb-4">
        {/* Card Total */}
        <div className="col-md-4 mb-3">
          <div className="card stats-card h-100">
            <div className="card-body text-center">
              <div className="d-flex align-items-center justify-content-between">
                <div>
                  <h3 className="text-primary mb-1">{stats?.total ?? '?'}</h3>
                  <p className="text-muted mb-0">Total Encomendas</p>
                </div>
                <div className="text-primary"><i className="bi bi-clipboard-data"></i></div>
              </div>
            </div>
          </div>
        </div>
        {/* Card Pendentes */}
        <div className="col-md-4 mb-3">
          <div className="card stats-card h-100">
            <div className="card-body text-center">
              <div className="d-flex align-items-center justify-content-between">
                <div>
                  <h3 className="text-warning mb-1">{stats?.pending ?? '?'}</h3>
                  <p className="text-muted mb-0">Pendentes</p>
                </div>
                 <div className="text-warning"><i className="bi bi-clock-history"></i></div>
              </div>
            </div>
          </div>
        </div>
        {/* Card Entregues */}
        <div className="col-md-4 mb-3">
          <div className="card stats-card h-100">
            <div className="card-body text-center">
              <div className="d-flex align-items-center justify-content-between">
                <div>
                  <h3 className="text-success mb-1">{stats?.delivered ?? '?'}</h3>
                  <p className="text-muted mb-0">Entregues</p>
                </div>
                <div className="text-success"><i className="bi bi-check-circle"></i></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Ações Rápidas */}
      <div className="card mb-4">
        <div className="card-header"><h5 className="mb-0"><i className="bi bi-lightning me-2"></i>Ações Rápidas</h5></div>
        <div className="card-body">
          <div className="d-flex flex-wrap gap-2 justify-content-start">
            <Link to={`/encomendas/`} className="btn btn-outline-secondary"> {/* Rota a ser criada */}
              <i className="bi bi-plus-circle me-2"></i> Ver Encomendas
            </Link>
            <Link to={`/encomendas/nova/equipe/${equipeId}`} className="btn btn-primary"> {/* Rota a ser criada */}
              <i className="bi bi-plus-circle me-2"></i> Nova Encomenda
            </Link>
            <Link to={`/clientes/equipe/${equipeId}`} className="btn btn-outline-secondary">
              <i className="bi bi-people me-2"></i> Ver Clientes
            </Link>
            <Link to={`/clientes/novo/equipe/${equipeId}`} className="btn btn-success"> {/* Rota a ser criada */}
              <i className="bi bi-person-plus me-2"></i> Novo Cliente
            </Link>
            {/* Adicionar botões para Produtos e Fornecedores similarmente */}
             <Link to={`/produtos/equipe/${equipeId}`} className="btn btn-outline-secondary">
                <i className="bi bi-box me-2"></i> Ver Produtos
            </Link>
            <Link to={`/produtos/novo/equipe/${equipeId}`} className="btn btn-info"> {/* Rota a ser criada */}
                <i className="bi bi-box me-2"></i> Novo Produto
            </Link>
            <Link to={`/fornecedores/equipe/${equipeId}`} className="btn btn-outline-secondary">
                <i className="bi bi-truck me-2"></i> Ver Fornecedores
            </Link>
            <Link to={`/fornecedores/novo/equipe/${equipeId}`} className="btn btn-warning"> {/* Rota a ser criada */}
                <i className="bi bi-truck me-2"></i> Novo Fornecedor
            </Link>
          </div>
        </div>
      </div>

      {/* Últimas Encomendas */}
      <div className="card">
        <div className="card-header d-flex justify-content-between align-items-center">
          <h5 className="mb-0"><i className="bi bi-clock-history me-2"></i>Últimas Encomendas</h5>
          <Link to={`/encomendas?equipe_id=${equipeId}`} className="btn btn-outline-light btn-sm">
            Ver Todas <i className="bi bi-arrow-right ms-1"></i>
          </Link>
        </div>
        <div className="card-body p-0">
          {recent_orders && recent_orders.length > 0 ? (
            <div className="table-responsive">
              <table className="table table-hover mb-0">
                <thead>
                  <tr>
                    <th>Número</th>
                    <th>Cliente</th>
                    <th>Status</th>
                    <th>Data</th>
                    <th>Valor</th>
                    <th>Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {recent_orders.map((encomenda) => (
                    <tr key={encomenda.numero_encomenda}>
                      <td><Link to={`/encomendas/${encomenda.numero_encomenda}`}><strong>#{encomenda.numero_encomenda}</strong></Link></td>
                      <td>{encomenda.cliente_nome}</td>
                      <td><span className={`status-badge status-${encomenda.status}`}>{encomenda.status_display}</span></td>
                      <td><small>{new Date(encomenda.data_criacao).toLocaleString('pt-BR')}</small></td>
                      <td><strong>R$ {parseFloat(encomenda.valor_total).toFixed(2)}</strong></td>
                      <td>
                        <div className="btn-group btn-group-sm">
                          <Link to={`/encomendas/${encomenda.numero_encomenda}`} className="btn btn-outline-primary" title="Ver Detalhes"><i className="bi bi-eye"></i></Link>
                          <Link to={`/encomendas/${encomenda.numero_encomenda}/editar`} className="btn btn-outline-secondary" title="Editar"><i className="bi bi-pencil"></i></Link> {/* Rota a ser criada */}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center p-5">
              <i className="bi bi-inbox text-muted" style={{ fontSize: '3rem' }}></i>
              <h5 className="text-muted mt-3">Nenhuma encomenda recente encontrada para esta equipe.</h5>
               <Link to={`/encomendas/nova/equipe/${equipeId}`} className="btn btn-primary mt-3">
                    <i className="bi bi-plus-circle me-2"></i>Criar Primeira Encomenda
                </Link>
            </div>
          )}
        </div>
      </div>

      {/* Botão Voltar */}
      <div className="mt-4">
         <Link to="/equipes" className="btn btn-secondary">
              <i className="bi bi-arrow-left me-2"></i>Voltar para Lista de Equipes
          </Link>
      </div>

    </div>
  );
}

export default TeamDashboardPage;