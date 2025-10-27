import React, { useState } from 'react';
import { Outlet, Navigate } from 'react-router-dom';
import NavbarComponent from './NavbarComponent';
import SidebarComponent from './SidebarComponent';

const Layout = () => {
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const activeTeamId = sessionStorage.getItem('currentTeamId'); // Solução temporária

  const toggleSidebar = () => {
    setSidebarOpen(!isSidebarOpen);
  };

  // Proteção de Rota
  const token = localStorage.getItem('accessToken');
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div>
      <NavbarComponent toggleSidebar={toggleSidebar} />
      <div className="container-fluid">
        <div className="row">
          <SidebarComponent isOpen={isSidebarOpen} activeTeamId={activeTeamId} />
          <main className="col-lg-10 ms-lg-auto main-content" style={{ paddingTop: '20px' }}>
             {isSidebarOpen && <div onClick={toggleSidebar} style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 999 }} className="d-lg-none" />}
            <Outlet /> {/* Onde as páginas serão renderizadas */}
          </main>
        </div>
      </div>
    </div>
  );
};

export default Layout;