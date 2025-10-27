import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';

// (Opcional) Importe api se precisar chamar um endpoint de logout no futuro
// import api from '../services/api';

const NavbarComponent = ({ toggleSidebar }) => {
  // Removido useNavigate não utilizado por enquanto
  const [user, setUser] = useState(null);

  // Efeito para buscar dados do usuário (exemplo simulado)
  useEffect(() => {
    // TODO: Implementar busca real de dados do usuário logado (ex: /api/users/me/)
    // Por enquanto, usamos dados simulados ou salvos no localStorage
    const simulatedUser = {
      nome_completo: localStorage.getItem('user_nome') || 'Usuário', // Tente buscar, senão use 'Usuário'
      username: localStorage.getItem('user_email') || '' // Tente buscar email
    };
    setUser(simulatedUser);
  }, []); // Roda apenas uma vez ao montar

  const handleLogout = () => {
    // Limpa tokens e dados simulados do localStorage
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user_nome');
    localStorage.removeItem('user_email');
    sessionStorage.removeItem('currentTeamId'); // Limpa equipe ativa da sessão

    // TODO: Chamar API de logout no backend (/api/logout/ ou similar), se existir

    // Redireciona para login (força recarregamento para limpar estado global)
    window.location.href = '/login';
  };

  // --- Lógica do Theme Toggle (Dark Mode como Padrão) ---
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const savedTheme = localStorage.getItem('theme');
    // Se não houver tema salvo, o padrão é escuro (true). Se salvo como 'light', é claro (false).
    return savedTheme ? savedTheme === 'dark' : true;
  });

  useEffect(() => {
    // Se NÃO for dark mode (ou seja, é light), ADICIONA a classe 'light-mode'
    if (!isDarkMode) {
      document.body.classList.add('light-mode');
    } else {
    // Se FOR dark mode, REMOVE a classe 'light-mode' (voltando ao padrão :root que é escuro)
      document.body.classList.remove('light-mode');
    }
    // Salva a preferência atual no localStorage
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
  }, [isDarkMode]); // Roda sempre que isDarkMode mudar

  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode); // Alterna o estado
  };
  // --- Fim Lógica do Theme Toggle ---

  return (
    <nav className="navbar navbar-expand-lg sticky-top" style={{ /* Estilos do base/index.css */
        background: 'var(--navbar-bg)',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        borderBottom: '1px solid var(--border-color)',
        minHeight: '58px'
    }}>
      <div className="container-fluid">
        {/* Botão para mostrar Sidebar em telas menores (d-lg-none) */}
        <button
          className="btn btn-outline-primary d-lg-none me-3" // Usa cor primária do tema atual
          type="button"
          onClick={toggleSidebar} // Função passada como prop pelo Layout
          aria-label="Toggle sidebar"
        >
          <i className="bi bi-list"></i>
        </button>

        {/* Brand/Logo */}
        <Link className="navbar-brand" to="/dashboard"> {/* Link para dashboard */}
          <i className="bi bi-clipboard-check me-2"></i>
          Sistema de Encomendas
        </Link>

         {/* Itens à direita */}
        <div className="navbar-nav ms-auto d-flex flex-row align-items-center">
          {user && (
            <span className="navbar-text me-3 d-none d-sm-inline">
              Olá, {user.nome_completo || user.username || 'Usuário'} {/* Fallback se nome/username não existirem */}
            </span>
          )}

          {/* Theme Toggle Button */}
          <div
            className="theme-toggle me-3"
            title="Alterar tema"
            onClick={toggleTheme}
            style={{ cursor: 'pointer', fontSize: '1.25rem', color: 'var(--text-muted-color)' }}
          >
            {/* Mostra sol se estiver escuro, lua se estiver claro */}
            {isDarkMode ? <i className="bi bi-sun-fill"></i> : <i className="bi bi-moon-fill"></i>}
          </div>

          {/* Links de Perfil/Equipes (Exemplo) */}
           <Link className="nav-link me-2" to="/perfil" title="Meu Perfil"> {/* Criar rota /perfil depois */}
             <i className="bi bi-person-circle"></i>
           </Link>
           <Link className="nav-link me-2" to="/equipes" title="Minhas Equipes"> {/* Criar rota /equipes depois */}
             <i className="bi bi-people"></i>
           </Link>

          {/* Botão de Logout */}
          <button
            type="button"
            className="btn btn-outline-danger btn-sm"
            title="Sair"
            onClick={handleLogout}
          >
            <i className="bi bi-box-arrow-right"></i> <span className="d-none d-sm-inline">Sair</span>
          </button>
        </div>
      </div>
    </nav>
  );
};

export default NavbarComponent;