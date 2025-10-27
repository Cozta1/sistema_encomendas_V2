import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, Link, useParams } from 'react-router-dom';

// Layout e Páginas Existentes
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import EncomendasPage from './pages/EncomendasPage';
import EquipesPage from './pages/EquipesPage';
import TeamDashboardPage from './pages/TeamDashboardPage'; // Usando o componente real agora

// --- NOVOS PLACEHOLDERS ---
const PlaceholderPage = ({ title }) => {
    const params = useParams(); // Para pegar IDs da URL
    return (
        <div style={{ padding: '20px' }}>
            <h1>{title || 'Página em Construção'}</h1>
            <p>Esta página será implementada.</p>
            {/* Mostra parâmetros da URL para debug */}
            {Object.keys(params).length > 0 && (
                <pre>Parâmetros da URL: {JSON.stringify(params)}</pre>
            )}
            <p><Link to="/equipes">Voltar para Equipes</Link></p>
        </div>
    );
};

const EncomendaFormPage = () => <PlaceholderPage title="Formulário de Encomenda (Criar/Editar)" />;
const EncomendaDetailPage = () => <PlaceholderPage title="Detalhes da Encomenda" />;
const ClienteFormPage = () => <PlaceholderPage title="Formulário de Cliente" />;
const ProdutoFormPage = () => <PlaceholderPage title="Formulário de Produto" />;
const FornecedorFormPage = () => <PlaceholderPage title="Formulário de Fornecedor" />;
const ClienteListPage = () => <PlaceholderPage title="Lista de Clientes da Equipe" />;
const ProdutoListPage = () => <PlaceholderPage title="Lista de Produtos da Equipe" />;
const FornecedorListPage = () => <PlaceholderPage title="Lista de Fornecedores da Equipe" />;
const CriarEquipePage = () => <PlaceholderPage title="Criar Nova Equipe" />;
const GerenciarEquipePage = () => <PlaceholderPage title="Gerenciar Equipe" />;
const PerfilPage = () => <PlaceholderPage title="Meu Perfil" />;
// --- FIM NOVOS PLACEHOLDERS ---


// --- Componente App principal ---
function App() {
  return (
    <BrowserRouter> {/* Habilita o roteamento */}
      <Routes> {/* Define o container das rotas */}

        <Route path="/" element={<Layout />}>

          {/* Index e Rotas de Equipe */}
          <Route index element={<EquipesPage />} />
          <Route path="equipes" element={<EquipesPage />} />
          <Route path="equipes/criar" element={<CriarEquipePage />} />
          <Route path="equipes/:equipeId/gerenciar" element={<GerenciarEquipePage />} />
          <Route path="dashboard/:equipeId" element={<TeamDashboardPage />} />

          {/* Rotas de Encomendas */}
          <Route path="encomendas" element={<EncomendasPage />} />
          {/* Nota: :encomendaId deve ser tratado como número no componente */}
          <Route path="encomendas/:encomendaId" element={<EncomendaDetailPage />} />
          <Route path="encomendas/:encomendaId/editar" element={<EncomendaFormPage />} />
          <Route path="encomendas/nova/equipe/:equipeId" element={<EncomendaFormPage />} />

          {/* Rotas de Clientes (por equipe) */}
          <Route path="clientes/equipe/:equipeId" element={<ClienteListPage />} />
          <Route path="clientes/novo/equipe/:equipeId" element={<ClienteFormPage />} />
          {/* Adicionar rota para editar cliente depois */}
          {/* <Route path="clientes/:clienteId/editar/equipe/:equipeId" element={<ClienteFormPage />} /> */}

          {/* Rotas de Produtos (por equipe) */}
          <Route path="produtos/equipe/:equipeId" element={<ProdutoListPage />} />
          <Route path="produtos/novo/equipe/:equipeId" element={<ProdutoFormPage />} />
          {/* Adicionar rota para editar produto depois */}

          {/* Rotas de Fornecedores (por equipe) */}
          <Route path="fornecedores/equipe/:equipeId" element={<FornecedorListPage />} />
          <Route path="fornecedores/novo/equipe/:equipeId" element={<FornecedorFormPage />} />
          {/* Adicionar rota para editar fornecedor depois */}

          {/* Rota de Perfil */}
          <Route path="perfil" element={<PerfilPage />} />

          {/* Rota Catch-all (404) DENTRO do layout */}
          <Route path="*" element={
            <div style={{ padding: '20px' }}>
                <h2>Página Não Encontrada (404)</h2>
                <p>O recurso que você procura não foi encontrado dentro da aplicação.</p>
                <Link to="/equipes">Voltar para a página inicial</Link>
            </div>
          }/>
        </Route> {/* Fim das rotas protegidas dentro do Layout */}

        {/* Rotas Públicas (fora do Layout) */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        
      </Routes>
    </BrowserRouter>
  );
}

export default App;
