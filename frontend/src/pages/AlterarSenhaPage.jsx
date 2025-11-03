import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api'; // Importa o serviço de API

function AlterarSenhaPage() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    old_password: '',
    new_password1: '',
    new_password2: '',
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null); // Para erros gerais
  const [formErrors, setFormErrors] = useState({}); // Para erros de campo
  const [successMessage, setSuccessMessage] = useState(null);

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

    // Validação de frontend
    if (formData.new_password1 !== formData.new_password2) {
      setFormErrors({ new_password2: ['As senhas não coincidem.'] });
      setIsSubmitting(false);
      return;
    }
    if (formData.new_password1.length < 8) {
       setFormErrors({ new_password1: ['A nova senha deve ter pelo menos 8 caracteres.'] });
       setIsSubmitting(false);
       return;
    }

    try {
      // Faz a requisição POST para a API
      // O endpoint do Django antigo era 'auth/alterar-senha/'
      // Assumindo API: '/api/auth/alterar-senha/'
      await api.post('/api/auth/alterar-senha/', {
        old_password: formData.old_password,
        new_password1: formData.new_password1,
        new_password2: formData.new_password2,
      });

      // Sucesso
      setSuccessMessage('Senha alterada com sucesso!');
      // Limpa o formulário
      setFormData({ old_password: '', new_password1: '', new_password2: '' });
      
      // Opcional: redirecionar para o perfil após alguns segundos
      setTimeout(() => {
        navigate('/perfil');
      }, 3000); // 3 segundos

    } catch (err) {
      console.error("Erro ao alterar senha:", err.response || err);
      if (err.response?.data && typeof err.response.data === 'object') {
           setFormErrors(err.response.data);
           const nonFieldErrors = err.response.data.non_field_errors || err.response.data.detail;
           // Erro comum: senha antiga errada
           if (err.response.data.old_password) {
                setFormErrors(prev => ({ ...prev, old_password: err.response.data.old_password }));
           }
           setError(nonFieldErrors || "Erro de validação. Verifique os campos marcados.");
      } else {
           setError('Ocorreu um erro inesperado ao tentar alterar a senha.');
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
               <i className="bi bi-key-fill me-3"></i>
               Alterar Senha
            </h1>
            <p className="mb-0 text-muted">
              Modifique sua senha de acesso.
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
              <h5 className="mb-0">Formulário de Alteração de Senha</h5>
          </div>
          <div className="card-body">
            <form onSubmit={handleSubmit} noValidate>
              
              {/* Senha Antiga */}
              <div className="mb-3">
                <label htmlFor="old_password" className="form-label">Senha Antiga *</label>
                <input
                  type="password"
                  id="old_password"
                  name="old_password"
                  className={`form-control ${getFieldError('old_password') ? 'is-invalid' : ''}`}
                  value={formData.old_password}
                  onChange={handleChange}
                  required
                  disabled={isSubmitting}
                />
                {getFieldError('old_password')}
              </div>
              
              <hr />

              {/* Nova Senha */}
              <div className="mb-3">
                <label htmlFor="new_password1" className="form-label">Nova Senha *</label>
                <input
                  type="password"
                  id="new_password1"
                  name="new_password1"
                  className={`form-control ${getFieldError('new_password1') ? 'is-invalid' : ''}`}
                  value={formData.new_password1}
                  onChange={handleChange}
                  required
                  disabled={isSubmitting}
                />
                {getFieldError('new_password1')}
                <small className="text-muted">A senha deve ter pelo menos 8 caracteres.</small>
              </div>
              
               {/* Confirmar Nova Senha */}
              <div className="mb-3">
                <label htmlFor="new_password2" className="form-label">Confirmar Nova Senha *</label>
                <input
                  type="password"
                  id="new_password2"
                  name="new_password2"
                  className={`form-control ${getFieldError('new_password2') ? 'is-invalid' : ''}`}
                  value={formData.new_password2}
                  onChange={handleChange}
                  required
                  disabled={isSubmitting}
                />
                {getFieldError('new_password2')}
              </div>

              {/* Botões de Ação */}
              <div className="d-flex justify-content-between mt-4">
                  <Link to="/perfil" className="btn btn-secondary">
                      <i className="bi bi-x-circle me-2"></i>Cancelar
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

export default AlterarSenhaPage;