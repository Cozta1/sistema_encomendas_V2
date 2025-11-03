import React, { useEffect } from 'react';
import { Link, useOutletContext } from 'react-router-dom';

function DashboardPage() {
  // Tenta pegar a função 'setActiveTeamId' do 'Layout' (via Outlet)
  // O '?' é para evitar erro se o contexto não for passado
  const { setActiveTeamId } = useOutletContext() || {};

  // Efeito para limpar a equipe ativa (no sessionStorage e no estado do Layout)
  // ao visitar o dashboard principal.
  useEffect(() => {
    // Limpa do sessionStorage para persistir
    sessionStorage.removeItem('currentTeamId');
    // Limpa o estado do Layout (para a Sidebar atualizar)
    if (setActiveTeamId) {
      setActiveTeamId(null);
    }
  }, [setActiveTeamId]); // Roda quando o componente é carregado
  
  // Pega o nome do usuário (simulado do localStorage)
  const userName = localStorage.getItem('user_nome') || 'Usuário';

  return (
    <div>
      {/* Cabeçalho */}
      <div className="page-header">
        <h1><i className="bi bi-house-door-fill me-3"></i>Página Inicial</h1>
        <p className="mb-0 text-muted">Bem-vindo(a), {userName}. Selecione uma ação abaixo.</p>
      </div>

      {/* Cartões de Acesso Rápido */}
      <div className="row">
        {/* Card 1: Gerenciar Equipes */}
        <div className="col-md-6 col-lg-4 mb-3">
          <div className="card h-100">
            <div className="card-body text-center d-flex flex-column justify-content-center align-items-center">
              <i className="bi bi-people-fill" style={{ fontSize: '3rem', color: 'var(--link-color)' }}></i>
              <h5 className="card-title mt-3">Gerenciar Equipes</h5>
              <p className="card-text text-muted small">
                Crie equipes, convide membros ou selecione uma equipe para trabalhar.
              </p>
              <Link to="/equipes" className="btn btn-primary mt-auto">
                <i className="bi bi-arrow-right me-1"></i> Ver Minhas Equipes
              </Link>
            </div>
          </div>
        </div>

        {/* Card 2: Ver Todas Encomendas */}
        <div className="col-md-6 col-lg-4 mb-3">
          <div className="card h-100">
            <div className="card-body text-center d-flex flex-column justify-content-center align-items-center">
              <i className="bi bi-clipboard-data-fill text-success" style={{ fontSize: '3rem', color: 'var(--success-color)' }}></i>
              <h5 className="card-title mt-3">Todas as Encomendas</h5>
              <p className="card-text text-muted small">
                Veja e filtre todas as encomendas de todas as suas equipes em um só lugar.
              </p>
              <Link to="/encomendas" className="btn btn-success mt-auto">
                <i className="bi bi-search me-1"></i> Ver Encomendas
              </Link>
            </div>
          </div>
        </div>
        
        {/* Card 3: Nova Encomenda (Linka para Equipes) */}
        <div className="col-md-6 col-lg-4 mb-3">
          <div className="card h-100">
            <div className="card-body text-center d-flex flex-column justify-content-center align-items-center">
              <i className="bi bi-plus-circle-dotted text-warning" style={{ fontSize: '3rem', color: 'var(--warning-color)' }}></i>
              <h5 className="card-title mt-3">Nova Encomenda</h5>
              <p className="card-text text-muted small">
                Para criar uma nova encomenda, você precisa primeiro selecionar uma equipe.
              </p>
              <Link to="/equipes" className="btn btn-warning mt-auto">
                <i className="bi bi-people me-1"></i> Escolher Equipe
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DashboardPage;

