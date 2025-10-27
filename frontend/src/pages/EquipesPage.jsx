import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api'; // Nossa instância Axios

// (Opcional) Importar componentes UI se estiver usando (ex: Card, Button, List, Alert from MUI)

function EquipesPage() {
  const [teams, setTeams] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(null); // Para loading de botões Aceitar/Rejeitar
  const [actionError, setActionError] = useState(null); // Erros específicos das ações
  const navigate = useNavigate();

  // Função para buscar dados
  const fetchData = async () => {
    setLoading(true);
    setError(null);
    setActionError(null); // Limpa erros de ação ao recarregar
    try {
      const response = await api.get('/my-teams-invites/');
      setTeams(response.data.teams || []);
      setInvitations(response.data.invitations || []);
    } catch (err) {
      console.error('Erro ao buscar equipes e convites:', err);
      if (err.response && (err.response.status === 401 || err.response.status === 403)) {
        setError('Sessão expirada ou acesso negado. Faça login novamente.');
        // O Layout já deve redirecionar, mas podemos forçar aqui se necessário
        // navigate('/login');
      } else {
        setError('Não foi possível carregar os dados das equipes.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Buscar dados ao montar o componente
  useEffect(() => {
    fetchData();
  }, []); // Roda apenas uma vez

  // Função para lidar com Aceitar Convite
  const handleAcceptInvite = async (inviteId) => {
    setActionLoading(inviteId); // Define qual botão está carregando
    setActionError(null);
    try {
      await api.post(`/invites/${inviteId}/accept/`);
      // Se sucesso, remover o convite da lista e talvez atualizar a lista de equipes
      setInvitations(prev => prev.filter(inv => inv.id !== inviteId));
      // Opcional: Recarregar tudo para garantir consistência
      fetchData();
      // Ou navegar para o dashboard da nova equipe (precisaria do ID da equipe da resposta)
      // navigate(`/dashboard/${resposta.data.equipe_id}`);
    } catch (err) {
      console.error("Erro ao aceitar convite:", err);
      setActionError(`Erro ao aceitar convite ${inviteId}: ${err.response?.data?.detail || err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  // Função para lidar com Rejeitar Convite
  const handleRejectInvite = async (inviteId) => {
    setActionLoading(inviteId);
    setActionError(null);
    try {
      await api.post(`/invites/${inviteId}/reject/`);
      // Se sucesso, apenas remover o convite da lista
      setInvitations(prev => prev.filter(inv => inv.id !== inviteId));
    } catch (err) {
      console.error("Erro ao rejeitar convite:", err);
      setActionError(`Erro ao rejeitar convite ${inviteId}: ${err.response?.data?.detail || err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  // Função para definir a equipe ativa e navegar para o dashboard dela
  const handleSelectTeam = (teamId) => {
    sessionStorage.setItem('currentTeamId', teamId); // Armazena no sessionStorage por enquanto
    navigate(`/dashboard/${teamId}`); // Navega para a rota do dashboard da equipe (a ser criada)
  };

  // --- Renderização ---
  if (loading) {
    return <div style={{ padding: '20px' }}>Carregando equipes...</div>;
  }

  if (error) {
    return <div style={{ padding: '20px', color: 'red' }}>Erro: {error}</div>;
  }

  return (
    <div>
      {/* Cabeçalho da Página (pode virar um componente reutilizável) */}
      <div className="page-header">
        <div className="d-flex justify-content-between align-items-center flex-wrap gap-2">
          <div>
            <h1><i className="bi bi-people me-3"></i>Minhas Equipes</h1>
            <p className="mb-0 text-muted">Gerencie suas equipes e colaboradores</p>
          </div>
          <Link to="/equipes/criar" className="btn btn-success"> {/* Rota a ser criada */}
            <i className="bi bi-plus-circle me-2"></i>Nova Equipe
          </Link>
        </div>
      </div>

      {/* Seção de Convites Pendentes */}
      {invitations.length > 0 && (
        <div className="card mb-4 border-warning">
          <div className="card-header bg-warning text-dark">
            <h5 className="mb-0"><i className="bi bi-envelope-exclamation me-2"></i>Convites Pendentes ({invitations.length})</h5>
          </div>
          <div className="card-body" style={{ padding: '0.5rem 1rem' }}> {/* Padding menor */}
            {actionError && <div className="alert alert-danger p-2 small">{actionError}</div>}
            {invitations.map((invite) => (
              <div key={invite.id} className="d-flex justify-content-between align-items-center p-2 flex-wrap gap-2 border-bottom">
                <div>
                  Convidado por <strong>{invite.criado_por_info?.nome_completo || 'N/A'}</strong> para
                  <strong> "{invite.equipe_nome}"</strong> como <strong>{invite.papel}</strong>.
                  <small className="d-block text-muted">
                    Expira em: {new Date(invite.data_expiracao).toLocaleString('pt-BR')}
                  </small>
                </div>
                <div className="d-flex gap-2 flex-shrink-0">
                  <button
                    onClick={() => handleAcceptInvite(invite.id)}
                    className="btn btn-sm btn-success"
                    disabled={actionLoading === invite.id} // Desabilita botão durante a ação
                  >
                    {actionLoading === invite.id ? <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> : <><i className="bi bi-check-circle me-1"></i> Aceitar</>}
                  </button>
                  <button
                    onClick={() => handleRejectInvite(invite.id)}
                    className="btn btn-sm btn-danger"
                    disabled={actionLoading === invite.id}
                  >
                     {actionLoading === invite.id ? <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> : <><i className="bi bi-x-circle me-1"></i> Rejeitar</>}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Seção Minhas Equipes */}
      <div className="card mb-4">
        <div className="card-header">
          <h5 className="mb-0"><i className="bi bi-people-fill me-2"></i>Equipes que Participo ({teams.length})</h5>
        </div>
        <div className="card-body">
          {teams.length === 0 ? (
             <p className="text-muted text-center my-3">Você ainda não participa de nenhuma equipe.</p>
           ) : (
            <div className="row">
              {teams.map((team) => (
                <div key={team.id} className="col-md-6 col-lg-4 mb-3">
                  <div className="card h-100 border-0 shadow-sm">
                    <div className="card-body d-flex flex-column">
                      <div className="flex-grow-1">
                        <h6 className="card-title">
                          {team.nome}
                          {/* Badges de Papel */}
                          {team.sou_administrador_principal && <span className="badge bg-danger ms-1" title="Admin Principal"><i className="bi bi-shield-check"></i></span>}
                          {team.meu_papel === 'gerente' && !team.sou_administrador_principal && <span className="badge bg-warning text-dark ms-1" title="Gerente"><i className="bi bi-person-gear"></i></span>}
                          {team.meu_papel === 'administrador' && !team.sou_administrador_principal && <span className="badge bg-danger ms-1" title="Admin"><i className="bi bi-shield-check"></i></span>} {/* Papel Admin não-principal */}
                        </h6>
                        <p className="card-text text-muted small">
                          {team.descricao ? team.descricao.substring(0, 80) + (team.descricao.length > 80 ? '...' : '') : 'Sem descrição.'}
                        </p>
                      </div>
                      <div className="d-flex justify-content-between align-items-center mt-3 pt-2 border-top">
                        <small className="text-muted">
                          <i className="bi bi-people me-1"></i>{team.membros?.length || 0} membro(s)
                        </small>
                        <div className="d-flex gap-1">
                          {/* Botão para ir ao Dashboard da Equipe */}
                          <button
                            onClick={() => handleSelectTeam(team.id)}
                            className="btn btn-sm btn-primary"
                            title="Acessar Dashboard da Equipe"
                          >
                            <i className="bi bi-speedometer2"></i>
                          </button>
                          {/* Botão Gerenciar (se for admin ou gerente) */}
                          {(team.sou_administrador_principal || team.meu_papel === 'gerente' || team.meu_papel === 'administrador') && (
                            <Link
                              to={`/equipes/${team.id}/gerenciar`} // Rota a ser criada
                              className="btn btn-sm btn-warning"
                              title="Gerenciar Equipe"
                            >
                              <i className="bi bi-gear"></i>
                            </Link>
                          )}
                          {/* Botão Sair (se NÃO for admin principal) */}
                          {!team.sou_administrador_principal && (
                            <button
                               onClick={() => {/* Lógica para sair da equipe (chamar API) */}}
                               className="btn btn-sm btn-outline-danger"
                               title="Sair da Equipe"
                               disabled // Desabilitado por enquanto
                            >
                              <i className="bi bi-box-arrow-left"></i>
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

       {/* Mensagem se não houver equipes nem convites */}
      {teams.length === 0 && invitations.length === 0 && (
        <div className="alert alert-info">
          <i className="bi bi-info-circle me-2"></i>
          Você não faz parte de nenhuma equipe e não há convites pendentes.
          <Link to="/equipes/criar" className="alert-link ms-1">Crie uma nova equipe</Link> para começar.
        </div>
      )}
    </div>
  );
}

export default EquipesPage;