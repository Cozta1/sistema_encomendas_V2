import React from 'react';
// Importa componentes necessários do React Router
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';

// --- Layout e Páginas Públicas ---
import Layout from './components/Layout'; 
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
// Fluxo de senha
import SolicitarResetSenhaPage from './pages/SolicitarResetSenhaPage'; 
import RedefinirSenhaPage from './pages/RedefinirSenhaPage';       

// --- Páginas Protegidas (Core) ---
import HomePage from './pages/HomePage'; // Redirecionador (/)
import EquipesPage from './pages/EquipesPage'; // Lista de equipes
import TeamDashboardPage from './pages/TeamDashboardPage'; // Dashboard da equipe

// --- Páginas de Equipe ---
import EquipeCreatePage from './pages/EquipeCreatePage';     
import EquipeManagePage from './pages/EquipeManagePage';     
import ConvidarMembroPage from './pages/ConvidarMembroPage'; 
import AceitarConvitePage from './pages/AceitarConvitePage'; 

// --- Páginas de Usuário ---
import PerfilPage from './pages/PerfilPage';           
import AlterarSenhaPage from './pages/AlterarSenhaPage'; 

// --- Encomendas ---
import EncomendasPage from './pages/EncomendasPage'; 
import EncomendaDetailPage from './pages/EncomendaDetailPage'; 
import EncomendaFormPage from './pages/EncomendaFormPage'; 
// Entregas
import EntregaFormPage from './pages/EntregaFormPage'; 

// --- CRUDs ---
import ClienteListPage from './pages/ClienteListPage'; 
import ClienteFormPage from './pages/ClienteFormPage'; 
import ProdutoListPage from './pages/ProdutoListPage'; 
import ProdutoFormPage from './pages/ProdutoFormPage'; 
import FornecedorListPage from './pages/FornecedorListPage'; 
import FornecedorFormPage from './pages/FornecedorFormPage'; 

// --- Componente App principal ---
function App() {
  return (
    <BrowserRouter>
      <Routes> 

        {/* --- Rotas Públicas (sem Layout) --- */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        
        {/* Fluxo de Reset de Senha (Público) */}
        <Route path="/solicitar-reset-senha" element={<SolicitarResetSenhaPage />} />
        <Route path="/redefinir-senha/:token" element={<RedefinirSenhaPage />} />

        {/* --- Rotas Protegidas (renderizadas dentro do <Layout>) --- */}
        <Route path="/" element={<Layout />}>

          {/* Core */}
          <Route index element={<HomePage />} />
          <Route path="perfil" element={<PerfilPage />} />
          <Route path="alterar-senha" element={<AlterarSenhaPage />} />

          {/* Equipes */}
          <Route path="equipes" element={<EquipesPage />} />
          <Route path="equipes/criar" element={<EquipeCreatePage />} />
          <Route path="dashboard/:equipeId" element={<TeamDashboardPage />} />
          <Route path="equipes/:equipeId/gerenciar" element={<EquipeManagePage />} />
          <Route path="equipes/:equipeId/convidar" element={<ConvidarMembroPage />} />
          
          {/* Convites */}
          <Route path="convites/:conviteId/aceitar" element={<AceitarConvitePage />} />

          {/* Encomendas */}
          <Route path="encomendas" element={<EncomendasPage />} />
          {/* Rota para criar sem equipe definida (App pode escolher a primeira) */}
          <Route path="encomendas/nova" element={<EncomendaFormPage />} /> 
          {/* Rota para criar dentro de uma equipe específica */}
          <Route path="encomendas/nova/equipe/:equipeId" element={<EncomendaFormPage />} />
          <Route path="encomendas/:encomendaId" element={<EncomendaDetailPage />} />
          <Route path="encomendas/:encomendaId/editar" element={<EncomendaFormPage />} />

          {/* Entregas (associadas a encomendas) */}
          <Route path="encomendas/:encomendaId/entrega/nova" element={<EntregaFormPage />} />
          <Route path="entregas/:entregaId/editar" element={<EntregaFormPage />} />

          {/* Clientes */}
          <Route path="clientes/equipe/:equipeId" element={<ClienteListPage />} />
          <Route path="clientes/novo/equipe/:equipeId" element={<ClienteFormPage />} />
          <Route path="clientes/:clienteId/editar/equipe/:equipeId" element={<ClienteFormPage />} />

          {/* Produtos */}
          <Route path="produtos/equipe/:equipeId" element={<ProdutoListPage />} />
          <Route path="produtos/novo/equipe/:equipeId" element={<ProdutoFormPage />} />
          <Route path="produtos/:produtoId/editar/equipe/:equipeId" element={<ProdutoFormPage />} />

          {/* Fornecedores */}
          <Route path="fornecedores/equipe/:equipeId" element={<FornecedorListPage />} />
          <Route path="fornecedores/novo/equipe/:equipeId" element={<FornecedorFormPage />} />
          <Route path="fornecedores/:fornecedorId/editar/equipe/:equipeId" element={<FornecedorFormPage />} />

          {/* --- Rota Catch-all (404) --- */}
          <Route path="*" element={
            <div style={{ padding: '20px' }}>
                <h2>Página Não Encontrada (404)</h2>
                <p>O recurso que você procura não foi encontrado.</p>
                <Link to="/">Voltar para a página inicial</Link>
            </div>
          }/>
        </Route> {/* Fim das rotas protegidas */}

      </Routes>
    </BrowserRouter>
  );
}

export default App;