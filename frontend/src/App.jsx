import React from 'react';
// Importa componentes necessários do React Router
import { BrowserRouter, Routes, Route, Navigate, Link, useParams } from 'react-router-dom';

// Layout e Páginas Implementadas
import Layout from './components/Layout'; // Componente de Layout (Navbar + Sidebar)
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import EquipesPage from './pages/EquipesPage'; // Página para listar equipes
import TeamDashboardPage from './pages/TeamDashboardPage'; // Página de dashboard da equipe
import EncomendasPage from './pages/EncomendasPage'; // Página de lista de encomendas
import EncomendaDetailPage from './pages/EncomendaDetailPage'; // Página de detalhes da encomenda
import EncomendaFormPage from './pages/EncomendaFormPage'; // Página de formulário de encomenda

// --- Componente App principal ---
function App() {
  return (
    <BrowserRouter> {/* Habilita o roteamento */}
      <Routes> {/* Define o container das rotas */}

        {/* --- Rotas Públicas (sem Layout) --- */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* --- Rotas Protegidas (renderizadas dentro do <Layout>) --- */}
        <Route path="/" element={<Layout />}> {/* Rota pai que renderiza o Layout */}

          {/* Rota Index: Página padrão exibida em "/" dentro do Layout */}
          {/* Aponta para a lista de equipes como página inicial */}
          <Route index element={<EquipesPage />} />

          {/* Rota explícita para a lista de equipes */}
          <Route path="equipes" element={<EquipesPage />} />

          {/* Rota para o Dashboard ESPECÍFICO da equipe */}
          <Route path="dashboard/:equipeId" element={<TeamDashboardPage />} />

          {/* Rotas de Encomendas */}
          <Route path="encomendas" element={<EncomendasPage />} />
          <Route path="encomendas/:encomendaId" element={<EncomendaDetailPage />} />
          <Route path="encomendas/:encomendaId/editar" element={<EncomendaFormPage />} />
          <Route path="encomendas/nova/equipe/:equipeId" element={<EncomendaFormPage />} />

          {/* --- Rotas para CRUDs futuros (Clientes, Produtos, etc.) serão adicionadas aqui --- */}
          {/* Ex: <Route path="clientes/equipe/:equipeId" element={<ClienteListPage />} /> */}

          {/* Rota Catch-all (404) DENTRO do layout */}
          <Route path="*" element={
            <div style={{ padding: '20px' }}>
                <h2>Página Não Encontrada (404)</h2>
                <p>O recurso que você procura não foi encontrado dentro da aplicação.</p>
                <Link to="/equipes">Voltar para a página inicial</Link>
            </div>
          }/>
        </Route> {/* Fim das rotas protegidas dentro do Layout */}

      </Routes>
    </BrowserRouter>
  );
}

export default App;

