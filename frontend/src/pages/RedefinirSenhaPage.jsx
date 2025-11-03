import React, { useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import api from '../services/api'; // Importa o serviço de API

function RedefinirSenhaPage() {
  const { token } = useParams(); // Pega o token da URL
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    new_password1: '',
    new_password2: '',
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null); // Para erros gerais (ex: token inválido)
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

    // Validação simples de frontend
    if (formData.new_password1 !== formData.new_password2) {
      setFormErrors({ new_password2: ['As senhas não coincidem.'] });
      setIsSubmitting(false);
      return;
    }
    
    if (formData.new_password1.length < 8) {
       setFormErrors({ new_password1: ['A senha deve ter pelo menos 8 caracteres.'] });
       setIsSubmitting(false);
       return;
    }

    try {
      // Faz a requisição POST para a API
      // O endpoint do Django antigo era 'auth/redefinir-senha/<str:token>/'
      // Assumindo API: '/api/auth/redefinir-senha-confirm/'
      await api.post('/api/auth/redefinir-senha/', {
        token: token,
        password: formData.new_password1,
        password2: formData.new_password2, // A API pode esperar password ou new_password1
      });

      // Sucesso
      setSuccessMessage('Sua senha foi redefinida com sucesso! Você já pode fazer login com a nova senha.');
      
      // Opcional: redirecionar para o login após alguns segundos
      setTimeout(() => {
        navigate('/login');
      }, 5000); // 5 segundos

    } catch (err) {
      console.error("Erro ao redefinir senha:", err.response || err);
      if (err.response?.data && typeof err.response.data === 'object') {
           setFormErrors(err.response.data);
           const nonFieldErrors = err.response.data.non_field_errors || err.response.data.detail || err.response.data.token;
           setError(nonFieldErrors || "Erro de validação. Verifique os campos.");
      } else {
           setError('Link inválido ou expirado. Tente solicitar a redefinição novamente.');
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
    // Reutilizando o estilo do LoginPage para centralizar
    <div className="d-flex align-items-center justify-content-center vh-100" style={{ background: 'var(--page-bg)' }}>
      <div className="card" style={{ width: '100%', maxWidth: '440px', background: 'var(--card-bg)' }}>
        <div className="card-body p-4 p-md-5">
          
          <div className="text-center mb-4">
            <i className="bi bi-key-fill text-primary" style={{ fontSize: '3rem' }}></i>
            <h3 className="card-title mt-3">Definir Nova Senha</h3>
            <p className="text-muted">
              Crie uma nova senha segura para sua conta.
            </p>
          </div>
          
          {/* Alerta de Sucesso */}
          {successMessage && (
            <div className="alert alert-success" role="alert">
              <i className="bi bi-check-circle-fill me-2"></i>{successMessage}
              <div className="mt-2 text-center">
                 <Link to="/login" className="btn btn-success btn-sm">Ir para o Login</Link>
              </div>
            </div>
          )}

          {/* Alerta de Erro Geral */}
          {error && (
            <div className="alert alert-danger" role="alert">
              <i className="bi bi-exclamation-triangle-fill me-2"></i>{error}
            </div>
          )}

          {/* Se NÃO houver sucesso, mostra o formulário */}
          {!successMessage && (
            <form onSubmit={handleSubmit} noValidate>
              {/* Campo Nova Senha */}
              <div className="mb-3">
                <label htmlFor="new_password1" className="form-label">Nova Senha *</label>
                <input
                  type="password"
                  id="new_password1"
                  name="new_password1"
                  className={`form-control ${getFieldError('new_password1') ? 'is-invalid' : ''}`}
                  value={formData.new_password1}
                  onChange={handleChange}
                  placeholder="********"
                  required
                  disabled={isSubmitting}
                />
                {getFieldError('new_password1')}
              </div>
              
               {/* Campo Confirmar Senha */}
              <div className="mb-3">
                <label htmlFor="new_password2" className="form-label">Confirmar Nova Senha *</label>
                <input
                  type="password"
                  id="new_password2"
                  name="new_password2"
                  className={`form-control ${getFieldError('new_password2') ? 'is-invalid' : ''}`}
                  value={formData.new_password2}
                  onChange={handleChange}
                  placeholder="********"
                  required
                  disabled={isSubmitting}
                />
                {getFieldError('new_password2')}
              </div>

              {/* Botão de Envio */}
              <div className="d-grid mb-3">
                <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                  {isSubmitting ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                      Salvando...
                    </>
                  ) : (
                    <>
                      <i className="bi bi-check-circle-fill me-2"></i>
                      Salvar Nova Senha
                    </>
                  )}
                </button>
              </div>
            </form>
          )}

          {/* Links Inferiores */}
          <div className="text-center text-muted">
            <p className="mb-0">
              <Link to="/login" className="small">Voltar para o Login</Link>
            </p>
          </div>
          
        </div>
      </div>
    </div>
  );
}

export default RedefinirSenhaPage;