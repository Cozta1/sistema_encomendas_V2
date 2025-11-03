import React, { useState, useEffect } from 'react';
import { Outlet, Navigate, useLocation } from 'react-router-dom';
import NavbarComponent from './NavbarComponent';
import SidebarComponent from './SidebarComponent';

const Layout = () => {
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  // ATUALIZADO: Gerencia 'activeTeamId' como estado para re-renderizar componentes filhos
  const [activeTeamId, setActiveTeamId] = useState(sessionStorage.getItem('currentTeamId'));
  
  const location = useLocation(); // Hook para detectar mudanças de rota

  // Efeito para:
  // 1. Fechar a sidebar ao navegar (em mobile).
  // 2. Atualizar o estado 'activeTeamId' se ele mudar no sessionStorage (ex: ao clicar em EquipesPage).
  useEffect(() => {
    if (isSidebarOpen) {
        setSidebarOpen(false);
    }
    // Sincroniza o estado com o sessionStorage em cada mudança de rota
    setActiveTeamId(sessionStorage.getItem('currentTeamId'));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]); // Depende da mudança de rota

  const toggleSidebar = () => {
    setSidebarOpen(!isSidebarOpen);
  };

  // Proteção de Rota
  const token = localStorage.getItem('accessToken');
  if (!token) {
    // ATUALIZADO: Passa a localização atual para redirecionar de volta após o login
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return (
    <div>
      {/* Passa a função de toggle para a Navbar */}
      <NavbarComponent toggleSidebar={toggleSidebar} />
      
      <div className="container-fluid">
        <div className="row">
          {/* Passa o estado de abertura e o ID da equipe ativa para a Sidebar */}
          <SidebarComponent isOpen={isSidebarOpen} activeTeamId={activeTeamId} />
          
          {/* Conteúdo principal da página */}
          <main className="col-lg-10 ms-lg-auto main-content" style={{ paddingTop: '20px' }}>
             
             {/* Overlay escuro para fechar a sidebar em modo mobile */}
             {isSidebarOpen && (
                <div 
                    onClick={toggleSidebar} 
                    style={{ 
                        position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, 
                        backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 999 
                    }} 
                    className="d-lg-none" // Mostra apenas em telas menores que lg
                />
             )}
             
             {/* ATUALIZADO: Passa 'setActiveTeamId' para as rotas filhas via 'context' */}
            <Outlet context={{ setActiveTeamId }} /> 
          </main>
        </div>
      </div>
    </div>
  );
};

export default Layout;

