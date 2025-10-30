import React, { useState, useEffect } from 'react';
import { Outlet, Navigate, useLocation } from 'react-router-dom';
import NavbarComponent from './NavbarComponent';
import SidebarComponent from './SidebarComponent';

const Layout = () => {
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  // Estado para armazenar o ID da equipe ativa.
  // Usamos sessionStorage para persistir entre reloads, mas useState para re-renderizar.
  const [activeTeamId, setActiveTeamId] = useState(sessionStorage.getItem('currentTeamId'));
  
  const location = useLocation(); // Hook para detectar mudanças de rota

  // Efeito para atualizar o activeTeamId se ele mudar no sessionStorage
  // (Isso será útil quando a EquipesPage o definir)
  // Também é útil para fechar a sidebar em navegação mobile.
  useEffect(() => {
    setActiveTeamId(sessionStorage.getItem('currentTeamId'));
    
    // Fecha a sidebar em telas menores ao navegar
    if (isSidebarOpen) {
        setSidebarOpen(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]); // Depende da mudança de rota

  const toggleSidebar = () => {
    setSidebarOpen(!isSidebarOpen);
  };

  // Proteção de Rota
  const token = localStorage.getItem('accessToken');
  if (!token) {
    // Se não houver token, redireciona para a página de login
    // Preserva a rota que o usuário tentou acessar (para redirecionar de volta após login)
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
             
             {/* Outlet renderiza o componente da rota filha (ex: DashboardPage, EncomendasPage) */}
            <Outlet context={{ setActiveTeamId }} /> {/* Passa a função de definir equipe para as rotas filhas */}
          </main>
        </div>
      </div>
    </div>
  );
};

export default Layout;
