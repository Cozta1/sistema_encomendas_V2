import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import api from '../services/api';

function EquipeManagePage() {
  const { equipeId } = useParams();
  const navigate = useNavigate();

  // Estados
  const [equipe, setEquipe] = useState(null);
  const [membros, setMembros] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Estado para o formulário de edição da equipe
  const [formData, setFormData] = useState({ nome: '', descricao: '' });

  // --- Busca de Dados ---
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Buscar detalhes da equipe
      const equipeResponse = await api.get(`/api/equipes/${equipeId}/`);
      setEquipe(equipeResponse.data);
      setFormData({
        nome: equipeResponse.data.nome,
        descricao: equipeResponse.data.descricao || '',
      });

      // 2. Buscar membros da equipe (Assumindo endpoint /api/equipes/{id}/membros/)
      const membrosResponse = await api.get(`/api/equipes/${equipeId}/membros/`);
      setMembros(membrosResponse.data);

    } catch (err) {
      console.error("Erro ao buscar dados da equipe:", err);
      setError("Falha ao carregar dados. Você pode não ter permissão para gerenciar esta equipe.");
    } finally {
      setLoading(false);
    }
  }, [equipeId]);

  // Busca inicial
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // --- Handlers ---

  // Edição do formulário da equipe
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // Submissão do formulário da equipe
  const handleEquipeSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      // Assumindo API: PATCH /api/equipes/{id}/
      const response = await api.patch(`/api/equipes/${equipeId}/`, formData);
      setEquipe(response.data); // Atualiza o estado da equipe
      alert('Informações da equipe atualizadas com sucesso!');
    } catch (err) {
      console.error("Erro ao atualizar equipe:", err);
      setError(err.response?.data?.detail || "Erro ao salvar alterações.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Alterar papel de um membro
  const handleAlterarPapel = async (membroId, novoPapel) => {
    if (!window.confirm(`Tem certeza que deseja alterar o papel deste membro para "${novoPapel}"?`)) return;

    try {
      // Assumindo API: POST /api/equipes/{id}/membros/{membroId}/alterar-papel/
      await api.post(`/api/equipes/${equipeId}/alterar-papel/${membroId}/`, { papel: novoPapel });
      alert('Papel alterado com sucesso!');
      fetchData(); // Recarrega os dados
    } catch (err) {
      console.error("Erro ao alterar papel:", err);
      alert(err.response?.data?.detail || "Erro ao tentar alterar o papel.");
    }
  };

  // Remover membro
  const handleRemoverMembro = async (membroId, membroNome) => {
    if (!window.confirm(`Tem certeza que deseja remover "${membroNome}" da equipe?`)) return;

    try {
      // Assumindo API: POST /api/equipes/{id}/remover/{membroId}/
      await api.post(`/api/equipes/${equipeId}/remover/${membroId}/`);
      alert('Membro removido com sucesso!');
      fetchData(); // Recarrega os dados
    } catch (err) {
      console.error("Erro ao remover membro:", err);
      alert(err.response?.data?.detail || "Erro ao tentar remover o membro.");
    }
  };

  // Sair da equipe
  const handleSairEquipe = async () => {
    if (!window.confirm('Tem certeza que deseja SAIR desta equipe? Esta ação não pode ser desfeita.')) return;

    try {
      // Assumindo API: POST /api/equipes/{id}/sair/
      await api.post(`/api/equipes/${equipeId}/sair/`);
      alert('Você saiu da equipe.');
      sessionStorage.removeItem('currentTeamId'); // Limpa a equipe ativa
      navigate('/equipes'); // Redireciona para a lista
    } catch (err) {
      console.error("Erro ao sair da equipe:", err);
      alert(err.response?.data?.detail || "Erro ao tentar sair da equipe.");
    }
  };

  // --- Renderização ---

  if (loading) {
    return <div style={{ padding: '20px' }}>Carregando gerenciamento da equipe...</div>;
  }

  if (error) {
    return (
      <div className="alert alert-danger">
        {error} <Link to="/equipes" className="alert-link ms-2">Voltar para equipes</Link>
      </div>
    );
  }

  return (
    <div>
      {/* Cabeçalho */}
      <div className="page-header">
           <h1>
               <i className="bi bi-gear-fill me-3"></i>
               Gerenciar Equipe: {equipe?.nome}
            </h1>
            <p className="mb-0 text-muted">
              Altere as configurações, gerencie membros e convites.
            </p>
      </div>

      {/* Seção 1: Editar Informações da Equipe */}
      <div className="card form-section mb-4">
        <div className="card-header"><h5 className="mb-0">Configurações da Equipe</h5></div>
        <div className="card-body">
          <form onSubmit={handleEquipeSubmit} noValidate>
            <div className="mb-3">
              <label htmlFor="nome" className="form-label">Nome da Equipe *</label>
              <input
                type="text"
                id="nome"
                name="nome"
                className="form-control"
                value={formData.nome}
                onChange={handleChange}
                required
                disabled={isSubmitting}
              />
            </div>
            <div className="mb-3">
              <label htmlFor="descricao" className="form-label">Descrição</label>
              <textarea
                id="descricao"
                name="descricao"
                rows="3"
                className="form-control"
                value={formData.descricao}
                onChange={handleChange}
                disabled={isSubmitting}
              ></textarea>
            </div>
            <div className="d-flex justify-content-end">
              <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                {isSubmitting ? 'Salvando...' : 'Salvar Alterações'}
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Seção 2: Membros da Equipe */}
      <div className="card mb-4">
        <div className="card-header d-flex justify-content-between align-items-center">
          <h5 className="mb-0"><i className="bi bi-people me-2"></i>Membros ({membros.length})</h5>
          <Link to={`/equipes/${equipeId}/convidar`} className="btn btn-success btn-sm">
            <i className="bi bi-person-plus-fill me-2"></i>Convidar Novo Membro
          </Link>
        </div>
        <div className="card-body p-0">
          <div className="table-responsive">
            <table className="table table-hover mb-0">
              <thead>
                <tr>
                  <th>Usuário</th>
                  <th>E-mail</th>
                  <th>Papel</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {membros.map(membro => (
                  <tr key={membro.id}>
                    <td><strong>{membro.usuario.nome_completo || membro.usuario.email}</strong></td>
                    <td>{membro.usuario.email}</td>
                    <td>
                      {/* Lógica de Alteração de Papel (Simplificada) */}
                      {/* Para um <select> completo, você precisaria da lógica da API */}
                      <span className={`badge bg-${membro.papel === 'ADMIN' ? 'primary' : 'secondary'}`}>
                        {membro.papel_display}
                      </span>
                      {/* Exemplo de botões de troca rápida (se for admin) */}
                      {membro.papel === 'MEMBRO' && (
                        <button 
                          className="btn btn-outline-primary btn-sm ms-2" 
                          title="Promover a Admin"
                          onClick={() => handleAlterarPapel(membro.id, 'ADMIN')}
                        ><i className="bi bi-arrow-up-circle"></i></button>
                      )}
                      {membro.papel === 'ADMIN' && (
                         <button 
                          className="btn btn-outline-secondary btn-sm ms-2" 
                          title="Rebaixar para Membro"
                          onClick={() => handleAlterarPapel(membro.id, 'MEMBRO')}
                        ><i className="bi bi-arrow-down-circle"></i></button>
                      )}
                    </td>
                    <td>
                      <button 
                        className="btn btn-outline-danger btn-sm"
                        title="Remover da Equipe"
                        onClick={() => handleRemoverMembro(membro.id, membro.usuario.nome_completo || membro.usuario.email)}
                      >
                        <i className="bi bi-trash"></i>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Seção 3: Zona de Perigo */}
      <div className="card text-white bg-danger mb-4">
         <div className="card-header"><h5 className="mb-0">Zona de Perigo</h5></div>
         <div className="card-body">
            <p>Esta ação não pode ser desfeita.</p>
            <button 
              className="btn btn-light"
              onClick={handleSairEquipe}
            >
                <i className="bi bi-box-arrow-left me-2"></i>Sair desta Equipe
            </button>
            {/* TODO: Adicionar botão de Excluir Equipe se for o dono */}
         </div>
      </div>
      
       {/* Botão Voltar */}
      <div className="mt-4">
         <Link to={`/dashboard/${equipeId}`} className="btn btn-secondary">
              <i className="bi bi-arrow-left me-2"></i>Voltar ao Dashboard
          </Link>
      </div>

    </div>
  );
}

export default EquipeManagePage;