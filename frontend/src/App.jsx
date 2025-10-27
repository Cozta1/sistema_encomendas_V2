import React from 'react';
// Garantir que Link está importado aqui
import { BrowserRouter, Routes, Route, Navigate, Link } from 'react-router-dom';

// Layout e Páginas
import Layout from './components/Layout'; // Importar Layout
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import EncomendasPage from './pages/EncomendasPage';
// import EquipesPage from './pages/EquipesPage'; // Exemplo

// --- CORREÇÃO: Mover DashboardPlaceholder para FORA da função App ---
const DashboardPlaceholder = () => {
  const token = localStorage.getItem('accessToken');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  const handleLogout = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user_nome');
    localStorage.removeItem('user_email');
    sessionStorage.removeItem('currentTeamId');
    window.location.href = '/login';
  };
  return (
    <div style={{ padding: '20px' }}>
      <h1>Dashboard (Protegido)</h1>
      <p>Conteúdo do Dashboard virá aqui.</p>
       <nav>
        <ul>
          <li>
            <Link to="/encomendas">Ver Encomendas</Link>
          </li>
          {/* Adicione outros links aqui */}
        </ul>
      </nav>
      <button onClick={handleLogout} style={{ marginTop: '20px' }}>Logout</button>
    </div>
  );
};
// --- Fim Dashboard ---

// Componente App principal
function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Rotas Públicas */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Rotas Protegidas (dentro do Layout) */}
        <Route path="/" element={<Layout />}> {/* Rota pai com Layout */}
          {/* Rota Index (padrão dentro do layout) */}
          {/* Agora DashboardPlaceholder está definido corretamente */}
          <Route index element={<DashboardPlaceholder />} />
          <Route path="dashboard" element={<DashboardPlaceholder />} />
          <Route path="encomendas" element={<EncomendasPage />} />
          {/* Adicionar outras rotas protegidas aqui */}
          {/* <Route path="equipes" element={<EquipesPage />} /> */}

          {/* Rota Catch-all DENTRO do layout */}
          <Route path="*" element={<div>Página não encontrada (Layout)</div>}/>
        </Route>

        {/* Rota Catch-all FORA do layout (opcional) */}
        {/* <Route path="*" element={<div>Página não encontrada</div>} /> */}

      </Routes>
    </BrowserRouter>
  );
}

export default App;