import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api'; // Importa o serviço de API

function PerfilPage() {


  const [formData, setFormData] = useState({
    nome_completo: '',
    email: '',
  });

  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null); // Para erros gerais
  const [formErrors, setFormErrors] = useState({}); // Para erros de campo
  const [successMessage, setSuccessMessage] = useState(null);

  // Busca os dados do usuário logado ao carregar a página
  useEffect(() => {
    const fetchUserData = async () => {
      setLoading(true);
      setError(null);
      try {
        // Assumindo que a API de 'user' (ou 'me') retorna os dados do usuário
        const response = await api.get('/api/auth/user/'); 
        const user = response.data;
        setFormData({
          nome_completo: user.nome_completo || '',
          email: user.email || '',
        });
      } catch (err) {
        console.error("Erro ao buscar dados do perfil:", err);
        setError("Não foi possível carregar os dados do seu perfil.");
      } finally {
        setLoading(false);
      }
    };
    fetchUserData();
  }, []); // Roda apenas uma vez

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
    setSuccessMessage(null);

    try {
      // Faz a requisição PUT ou PATCH para a API de 'user'
      const response = await api.patch('/api/auth/user/', formData);

      // Sucesso
      setSuccessMessage('Perfil atualizado com sucesso!');
      
      // Atualiza os dados do localStorage se necessário
      localStorage.setItem('user_nome', response.data.nome_completo);
      localStorage.setItem('user_email', response.data.email);
      
      // Opcional: recarregar a página para a navbar refletir a mudança
      setTimeout(() => {
        window.location.reload(); 
      }, 1500);

    } catch (err) {
      console.error("Erro ao atualizar perfil:", err.response || err);
      if (err.response?.data && typeof err.response.data === 'object') {
           setFormErrors(err.response.data);
           const nonFieldErrors = err.response.data.non_field_errors || err.response.data.detail;
           setError(nonFieldErrors || "Erro de validação. Verifique os campos marcados.");
      } else {
           setError('Ocorreu um erro inesperado ao tentar salvar o perfil.');
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
  
  if (loading) {
    return <div style={{ padding: '20px' }}>Carregando perfil...</div>;
  }

  return (
    <div>
      {/* Cabeçalho */}
      <div className="page-header">
           <h1>
               <i className="bi bi-person-circle me-3"></i>
               Meu Perfil
            </h1>
            <p className="mb-0 text-muted">
              Atualize suas informações pessoais e e-mail.
            </p>
      </div>

      {/* Alerta de Sucesso */}
      {successMessage && (
        <div className="alert alert-success" role="alert">
          <i className="bi bi-check-circle-fill me-2"></i>{successMessage}
        </div>
      )}

      {/* Alerta de Erro Geral */}
      {error && (
        <div className="alert alert-danger" role="alert">
          <i className="bi bi-exclamation-triangle-fill me-2"></i>{error}
        </div>
      )}

      {/* Card do Formulário */}
      <div className="card form-section mb-4" style={{ maxWidth: '700px' }}>
          <div className="card-header">
              <h5 className="mb-0">Informações do Usuário</h5>
          </div>
          <div className="card-body">
            <form onSubmit={handleSubmit} noValidate>
              
              {/* Nome Completo */}
              <div className="mb-3">
                <label htmlFor="nome_completo" className="form-label">Nome Completo *</label>
                <input
                  type="text"
                  id="nome_completo"
                  name="nome_completo"
                  className={`form-control ${getFieldError('nome_completo') ? 'is-invalid' : ''}`}
                  value={formData.nome_completo}
                  onChange={handleChange}
                  required
                  disabled={isSubmitting}
                />
                {getFieldError('nome_completo')}
              </div>
              
              {/* Email */}
              <div className="mb-3">
                <label htmlFor="email" className="form-label">E-mail *</label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  className={`form-control ${getFieldError('email') ? 'is-invalid' : ''}`}
                  value={formData.email}
                  onChange={handleChange}
                  required
                  disabled={isSubmitting}
                />
                {getFieldError('email')}
              </div>
              
              {/* Botões de Ação */}
              <div className="d-flex justify-content-between mt-4">
                  <Link to="/alterar-senha" className="btn btn-outline-secondary">
                      <i className="bi bi-key me-2"></i>Alterar Senha
                  </Link>
                  <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                      {isSubmitting ? (
                          <><span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Salvando...</>
                      ) : (
                          <><i className="bi bi-check-circle me-2"></i> Salvar Alterações</>
                      )}
                  </button>
              </div>
            </form>
          </div>
      </div>
    </div>
  );
}

export default PerfilPage;