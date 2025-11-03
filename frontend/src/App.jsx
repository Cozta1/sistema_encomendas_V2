import React from 'react';
// Importa componentes necessários do React Router
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';

// Layout e Páginas Implementadas
import Layout from './components/Layout'; // Componente de Layout (Navbar + Sidebar)
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';

// --- Novas Páginas ---
import HomePage from './pages/HomePage'; // Importa o novo dispatcher de rota
import EquipesPage from './pages/EquipesPage'; // Página para listar equipes
import TeamDashboardPage from './pages/TeamDashboardPage'; // Página de dashboard da equipe

// Encomendas
import EncomendasPage from './pages/EncomendasPage'; // Página de lista de encomendas
import EncomendaDetailPage from './pages/EncomendaDetailPage'; // Página de detalhes da encomenda
import EncomendaFormPage from './pages/EncomendaFormPage'; // Página de formulário de encomenda

// Clientes (Assumindo que foram criados)
import ClienteListPage from './pages/ClienteListPage'; 
import ClienteFormPage from './pages/ClienteFormPage'; 

// Produtos (Novos)
import ProdutoListPage from './pages/ProdutoListPage'; 
import ProdutoFormPage from './pages/ProdutoFormPage'; 

// Fornecedores (Novos)
import FornecedorListPage from './pages/FornecedorListPage'; 
import FornecedorFormPage from './pages/FornecedorFormPage'; 

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

          {/* Rota Index: Aponta para o HomePage que decide para onde redirecionar */}
          <Route index element={<HomePage />} />

          {/* Rota explícita para a lista de equipes */}
          <Route path="equipes" element={<EquipesPage />} />

          {/* Rota para o Dashboard ESPECÍFICO da equipe */}
          <Route path="dashboard/:equipeId" element={<TeamDashboardPage />} />

          {/* Rotas de Encomendas */}
          <Route path="encomendas" element={<EncomendasPage />} />
          <Route path="encomendas/:encomendaId" element={<EncomendaDetailPage />} />
          <Route path="encomendas/:encomendaId/editar" element={<EncomendaFormPage />} />
          <Route path="encomendas/nova/equipe/:equipeId" element={<EncomendaFormPage />} />

          {/* --- Rotas para CRUDs --- */}
          
          {/* Clientes */}
          <Route path="clientes/equipe/:equipeId" element={<ClienteListPage />} />
          <Route path="clientes/novo/equipe/:equipeId" element={<ClienteFormPage />} />
          <Route path="clientes/:clienteId/editar/equipe/:equipeId" element={<ClienteFormPage />} />

          {/* Produtos (Novas) */}
          <Route path="produtos/equipe/:equipeId" element={<ProdutoListPage />} />
          <Route path="produtos/novo/equipe/:equipeId" element={<ProdutoFormPage />} />
          <Route path="produtos/:produtoId/editar/equipe/:equipeId" element={<ProdutoFormPage />} />

          {/* Fornecedores (Novas) */}
          <Route path="fornecedores/equipe/:equipeId" element={<FornecedorListPage />} />
          <Route path="fornecedores/novo/equipe/:equipeId" element={<FornecedorFormPage />} />
          <Route path="fornecedores/:fornecedorId/editar/equipe/:equipeId" element={<FornecedorFormPage />} />


          {/* Rota Catch-all (404) DENTRO do layout */}
          <Route path="*" element={
            <div style={{ padding: '20px' }}>
                <h2>Página Não Encontrada (404)</h2>
                <p>O recurso que você procura não foi encontrado dentro da aplicação.</p>
                <Link to="/equipes">Voltar para a seleção de equipes</Link>
            </div>
          }/>
        </Route> {/* Fim das rotas protegidas dentro do Layout */}

      </Routes>
    </BrowserRouter>
  );
}

export default App;