import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../services/api';

function ConvidarMembroPage() {
  const { equipeId } = useParams();

  // Estados
  const [equipeNome, setEquipeNome] = useState('');
  const [convitesPendentes, setConvitesPendentes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null); // Erros de carregamento
  
  // Estados do formulário
  const [formData, setFormData] = useState({ email: '', papel: 'MEMBRO' });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState(null); // Erros de envio do form
  const [formSuccess, setFormSuccess] = useState(null);

  // --- Busca de Dados ---
  const fetchData = useCallback(async () => {
    // Não precisa de setLoading(true) aqui para o refresh não piscar
    try {
      // 1. Buscar nome da equipe (opcional, mas bom para UX)
      if (!equipeNome) { // Só busca se não tiver
        const equipeResponse = await api.get(`/api/equipes/${equipeId}/`);
        setEquipeNome(equipeResponse.data.nome);
      }

      // 2. Buscar convites pendentes
      const convitesResponse = await api.get(`/api/equipes/${equipeId}/convites/`);
      setConvitesPendentes(convitesResponse.data);

    } catch (err) {
      console.error("Erro ao buscar dados de convite:", err);
      setError("Falha ao carregar dados. Você pode não ter permissão.");
    } finally {
      setLoading(false);
    }
  }, [equipeId, equipeNome]);

  // Busca inicial
  useEffect(() => {
    fetchData();
  }, [fetchData]); // Removido 'fetchData' da dependência para evitar loop se useCallback não for usado

  // --- Handlers ---

  // Formulário
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // Enviar convite
  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setFormError(null);
    setFormSuccess(null);

    try {
      // Assumindo API: POST /api/equipes/{id}/convidar/
      await api.post(`/api/equipes/${equipeId}/convidar/`, formData);
      setFormSuccess(`Convite enviado com sucesso para ${formData.email}!`);
      setFormData({ email: '', papel: 'MEMBRO' }); // Limpa o formulário
      fetchData(); // Recarrega a lista de convites
    } catch (err) {
      console.error("Erro ao enviar convite:", err);
      setFormError(err.response?.data?.email || err.response?.data?.detail || "Erro ao enviar convite.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Cancelar convite pendente
  const handleCancelarConvite = async (conviteId) => {
    if (!window.confirm('Tem certeza que deseja cancelar este convite?')) return;

    try {
      // Assumindo API: DELETE /api/convites/{conviteId}/
      await api.delete(`/api/convites/${conviteId}/`);
      alert('Convite cancelado.');
      fetchData(); // Recarrega a lista
    } catch (err) {
      console.error("Erro ao cancelar convite:", err);
      alert(err.response?.data?.detail || "Erro ao tentar cancelar.");
    }
  };

  // --- Renderização ---

  if (loading) {
    return <div style={{ padding: '20px' }}>Carregando convites...</div>;
  }

  if (error) {
    return (
      <div className="alert alert-danger">
        {error} <Link to={`/equipes/${equipeId}/gerenciar`} className="alert-link ms-2">Voltar</Link>
      </div>
    );
  }

  return (
    <div>
      {/* Cabeçalho */}
      <div className="page-header">
           <h1>
               <i className="bi bi-person-plus-fill me-3"></i>
               Convidar Membro para {equipeNome}
            </h1>
      </div>

      {/* Seção 1: Formulário de Convite */}
      <div className="card form-section mb-4">
        <div className="card-header"><h5 className="mb-0">Enviar Novo Convite</h5></div>
        <div className="card-body">
          
          {formSuccess && <div className="alert alert-success">{formSuccess}</div>}
          {formError && <div className="alert alert-danger">{formError}</div>}
          
          <form onSubmit={handleSubmit} noValidate>
            <div className="row">
              <div className="col-md-7 mb-3">
                <label htmlFor="email" className="form-label">E-mail do Convidado *</label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  className="form-control"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="email@exemplo.com"
                  required
                  disabled={isSubmitting}
                />
              </div>
              <div className="col-md-5 mb-3">
                 <label htmlFor="papel" className="form-label">Papel (Função) *</label>
                 <select
                    id="papel"
                    name="papel"
                    className="form-select"
                    value={formData.papel}
                    onChange={handleChange}
                    disabled={isSubmitting}
                 >
                    <option value="MEMBRO">Membro</option>
                    <option value="ADMIN">Administrador</option>
                 </select>
              </div>
            </div>
            
            <div className="d-flex justify-content-end">
              <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                {isSubmitting ? 'Enviando...' : 'Enviar Convite'}
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Seção 2: Convites Pendentes */}
      <div className="card mb-4">
        <div className="card-header">
          <h5 className="mb-0"><i className="bi bi-clock-history me-2"></i>Convites Pendentes</h5>
        </div>
        <div className="card-body p-0">
          {convitesPendentes.length === 0 ? (
            <div className="text-center p-4 text-muted">Nenhum convite pendente.</div>
          ) : (
            <div className="table-responsive">
              <table className="table table-hover mb-0">
                <thead>
                  <tr>
                    <th>E-mail</th>
                    <th>Papel</th>
                    <th>Enviado em</th>
                    <th>Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {convitesPendentes.map(convite => (
                    <tr key={convite.id}>
                      <td><strong>{convite.email}</strong></td>
                      <td><span className={`badge bg-${convite.papel === 'ADMIN' ? 'primary' : 'secondary'}`}>{convite.papel_display}</span></td>
                      <td>{new Date(convite.data_criacao).toLocaleString('pt-BR')}</td>
                      <td>
                        <button 
                          className="btn btn-outline-danger btn-sm"
                          title="Cancelar Convite"
                          onClick={() => handleCancelarConvite(convite.id)}
                        >
                          <i className="bi bi-x-circle"></i> Cancelar
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
      
       {/* Botão Voltar */}
      <div className="mt-4">
         <Link to={`/equipes/${equipeId}/gerenciar`} className="btn btn-secondary">
              <i className="bi bi-arrow-left me-2"></i>Voltar ao Gerenciamento
          </Link>
      </div>
    </div>
  );
}

export default ConvidarMembroPage;