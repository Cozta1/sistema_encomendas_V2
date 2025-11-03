import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api'; // Importa o serviço de API

function EquipeCreatePage() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    nome: '',
    descricao: '',
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null); // Para erros gerais
  const [formErrors, setFormErrors] = useState({}); // Para erros de campo

  // Handler para mudanças nos campos
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // Função para lidar com a submissão do formulário
  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setFormErrors({});

    try {
      // --- CORREÇÃO ---
      // O endpoint do Django antigo era 'equipes/criar/'
      // API: POST /equipes/ (o /api/ já está no baseURL)
      const response = await api.post('/equipes/', formData);
      // --- FIM DA CORREÇÃO ---

      // Sucesso!
      const novaEquipe = response.data;
      
      // Define a equipe recém-criada como ativa na sessão
      sessionStorage.setItem('currentTeamId', novaEquipe.id);
      
      alert(`Equipe "${novaEquipe.nome}" criada com sucesso!`);
      
      // Redireciona para o dashboard da nova equipe
      navigate(`/dashboard/${novaEquipe.id}`);

    } catch (err) {
      console.error("Erro ao criar equipe:", err.response || err);
      if (err.response?.data && typeof err.response.data === 'object') {
           setFormErrors(err.response.data);
           const nonFieldErrors = err.response.data.non_field_errors || err.response.data.detail;
           setError(nonFieldErrors || "Erro de validação. Verifique os campos marcados.");
      } else {
           setError('Ocorreu um erro inesperado ao tentar criar a equipe.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };
  
  // Função auxiliar para exibir erros de formulário
  const getFieldError = (fieldName) => {
     if (formErrors && formErrors[fieldName]) {
         return <small className="text-danger d-block mt-1">{formErrors[fieldName][0]}</small>;
     }
     return null;
  };

  return (
    <div>
      {/* Cabeçalho */}
      <div className="page-header">
           <h1>
               <i className="bi bi-people-fill me-3"></i>
               Criar Nova Equipe
            </h1>
            <p className="mb-0 text-muted">
              Crie um novo espaço de trabalho para organizar suas encomendas.
            </p>
      </div>

      {/* Alerta de Erro Geral */}
      {error && (
        <div className="alert alert-danger" role="alert">
          <i className="bi bi-exclamation-triangle-fill me-2"></i>{error}
        </div>
      )}

      {/* Card do Formulário */}
      <div className="card form-section mb-4" style={{ maxWidth: '700px' }}>
          <div className="card-header">
              <h5 className="mb-0">Informações da Equipe</h5>
          </div>
          <div className="card-body">
            <form onSubmit={handleSubmit} noValidate>
              
              {/* Nome da Equipe */}
              <div className="mb-3">
                <label htmlFor="nome" className="form-label">Nome da Equipe *</label>
                <input
                  type="text"
                  id="nome"
                  name="nome"
                  className={`form-control ${getFieldError('nome') ? 'is-invalid' : ''}`}
                  value={formData.nome}
                  onChange={handleChange}
                  placeholder="Ex: Farmácia Matriz"
                  required
                  disabled={isSubmitting}
                />
                {getFieldError('nome')}
              </div>
              
              {/* Descrição */}
              <div className="mb-3">
                <label htmlFor="descricao" className="form-label">Descrição</label>
                <textarea
                  id="descricao"
                  name="descricao"
                  rows="3"
                  className={`form-control ${getFieldError('descricao') ? 'is-invalid' : ''}`}
                  value={formData.descricao}
                  onChange={handleChange}
                  placeholder="Uma breve descrição sobre esta equipe (opcional)"
                  disabled={isSubmitting}
                ></textarea>
                {getFieldError('descricao')}
              </div>
              
              {/* Botões de Ação */}
              <div className="d-flex justify-content-between mt-4">
                  <Link to="/equipes" className="btn btn-secondary">
                      <i className="bi bi-x-circle me-2"></i>Cancelar
                  </Link>
                  <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                      {isSubmitting ? (
                          <><span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Criando...</>
                      ) : (
                          <><i className="bi bi-check-circle me-2"></i> Criar Equipe</>
                      )}
                  </button>
              </div>
            </form>
          </div>
      </div>
    </div>
  );
}

export default EquipeCreatePage;