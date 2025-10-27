import React from 'react';
import { NavLink } from 'react-router-dom';

const SidebarComponent = ({ isOpen, activeTeamId }) => {
  const teamLinksDisabled = !activeTeamId;

  const getNavLinkClass = ({ isActive }) => `nav-link ${isActive ? 'active' : ''}`;
  const getTeamNavLinkClass = ({ isActive }) => {
       let classes = 'nav-link';
       if (teamLinksDisabled) classes += ' disabled';
       else if (isActive) classes += ' active';
       return classes;
   };


  return (
    <nav
      id="sidebar"
      className={`col-lg-2 sidebar d-lg-block ${isOpen ? 'show' : ''}`}
      style={{ /* Estilos...*/ background: 'var(--sidebar-bg)', minHeight: 'calc(100vh - 58px)', borderRight: '1px solid var(--border-color)', paddingTop: '1rem', position: 'fixed', top: '58px', left: isOpen ? '0' : '-250px', width: '250px', zIndex: 1000, transition: 'left 0.3s ease' }}
    >
      <div className="position-sticky pt-3">
        <ul className="nav flex-column">
          <li className="nav-item">
             <NavLink to="/equipes" className={getNavLinkClass} end>
               <i className="bi bi-house-door me-2"></i> Início / Equipes
             </NavLink>
           </li>
           <li className="nav-item">
            <NavLink to="/encomendas" className={getNavLinkClass}>
              <i className="bi bi-clipboard-data me-2"></i> Encomendas
            </NavLink>
          </li>
          <li className="nav-item">
             <NavLink
               to={activeTeamId ? `/clientes/equipe/${activeTeamId}` : '#'}
               className={getTeamNavLinkClass}
               aria-disabled={teamLinksDisabled}
               title={teamLinksDisabled ? "Selecione equipe" : ""}
             > <i className="bi bi-people me-2"></i> Clientes </NavLink>
           </li>
          <li className="nav-item">
             <NavLink
               to={activeTeamId ? `/produtos/equipe/${activeTeamId}` : '#'}
               className={getTeamNavLinkClass}
               aria-disabled={teamLinksDisabled}
               title={teamLinksDisabled ? "Selecione equipe" : ""}
             > <i className="bi bi-box me-2"></i> Produtos </NavLink>
          </li>
          <li className="nav-item">
             <NavLink
               to={activeTeamId ? `/fornecedores/equipe/${activeTeamId}` : '#'}
               className={getTeamNavLinkClass}
               aria-disabled={teamLinksDisabled}
               title={teamLinksDisabled ? "Selecione equipe" : ""}
             > <i className="bi bi-truck me-2"></i> Fornecedores </NavLink>
          </li>
        </ul>
      </div>
    </nav>
  );
};

export default SidebarComponent;