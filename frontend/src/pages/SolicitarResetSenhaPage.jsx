import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api'; // Importa o serviço de API

function SolicitarResetSenhaPage() {
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null); // Para erros gerais
  const [successMessage, setSuccessMessage] = useState(null); // Para mensagens de sucesso

  // Função para lidar com a submissão do formulário
  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setSuccessMessage(null);

    try {
      // Faz a requisição POST para a API (ajuste o endpoint se necessário)
      // O endpoint do Django antigo era 'auth/solicitar-reset-senha/'
      // Assumindo que a API é '/api/auth/solicitar-reset-senha/'
      await api.post('/api/auth/solicitar-reset-senha/', { email });

      // Sucesso
      setSuccessMessage('Solicitação enviada! Se o e-mail estiver cadastrado, você receberá um link para redefinir sua senha.');
      setEmail(''); // Limpa o campo
      
    } catch (err) {
      console.error("Erro ao solicitar reset de senha:", err.response || err);
      if (err.response?.data && err.response.data.email) {
        setError(err.response.data.email[0]); // Erro de validação específico
      } else if (err.response?.data && err.response.data.detail) {
         setError(err.response.data.detail);
      } else {
        setError('Ocorreu um erro. Tente novamente mais tarde.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    // Reutilizando o estilo do LoginPage para centralizar
    <div className="d-flex align-items-center justify-content-center vh-100" style={{ background: 'var(--page-bg)' }}>
      <div className="card" style={{ width: '100%', maxWidth: '440px', background: 'var(--card-bg)' }}>
        <div className="card-body p-4 p-md-5">
          
          <div className="text-center mb-4">
            <i className="bi bi-shield-lock-fill text-primary" style={{ fontSize: '3rem' }}></i>
            <h3 className="card-title mt-3">Redefinir Senha</h3>
            <p className="text-muted">
              Esqueceu sua senha? Digite seu e-mail abaixo para receber um link de redefinição.
            </p>
          </div>
          
          {/* Alerta de Sucesso */}
          {successMessage && (
            <div className="alert alert-success" role="alert">
              <i className="bi bi-check-circle-fill me-2"></i>{successMessage}
            </div>
          )}

          {/* Alerta de Erro */}
          {error && (
            <div className="alert alert-danger" role="alert">
              <i className="bi bi-exclamation-triangle-fill me-2"></i>{error}
            </div>
          )}

          {/* Se houver sucesso, esconde o formulário */}
          {!successMessage && (
            <form onSubmit={handleSubmit} noValidate>
              {/* Campo E-mail */}
              <div className="mb-3">
                <label htmlFor="email" className="form-label">E-mail</label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  className={`form-control ${error ? 'is-invalid' : ''}`} // Marca inválido se houver erro
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="seu.email@exemplo.com"
                  required
                  disabled={isSubmitting}
                />
              </div>

              {/* Botão de Envio */}
              <div className="d-grid mb-3">
                <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                  {isSubmitting ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                      Enviando...
                    </>
                  ) : (
                    <>
                      <i className="bi bi-envelope-fill me-2"></i>
                      Solicitar Redefinição
                    </>
                  )}
                </button>
              </div>
            </form>
          )}

          {/* Links Inferiores */}
          <div className="text-center text-muted">
            <p className="mb-1">
              <Link to="/login" className="small">Lembrou a senha? Faça Login</Link>
            </p>
            <p className="mb-0">
              <Link to="/register" className="small">Não tem uma conta? Registre-se</Link>
            </p>
          </div>
          
        </div>
      </div>
    </div>
  );
}

export default SolicitarResetSenhaPage;