import React, { useState } from 'react';
// CORREÇÃO: Importar Link junto com useNavigate
import { useNavigate, Link } from 'react-router-dom';
import api from '../services/api';

function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const response = await api.post('/token/', {
         email: email, // Ajuste para 'username' se necessário
         password: password,
      });

      const accessToken = response.data.access;
      const refreshToken = response.data.refresh;

      localStorage.setItem('accessToken', accessToken);
      localStorage.setItem('refreshToken', refreshToken);

      api.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;

      navigate('/dashboard');

    } catch (err) {
      setLoading(false);
      if (err.response) {
        console.error('API Error:', err.response.data);
        const detail = err.response.data?.detail;
        setError(detail || 'Email ou senha inválidos.');
      } else if (err.request) {
        console.error('Network Error:', err.request);
        setError('Erro de conexão com o servidor.');
      } else {
        console.error('Request Setup Error:', err.message);
        setError('Erro ao tentar fazer login.');
      }
    } finally {
        if(loading) setLoading(false);
    }
  };

  // JSX Básico (substitua por componentes UI)
  return (
    <div style={{ maxWidth: '400px', margin: '50px auto', padding: '20px', border: '1px solid #ccc', borderRadius: '8px' }}>
      <h2>Login</h2>
      <form onSubmit={handleSubmit}>
        {error && <div style={{ color: 'red', marginBottom: '10px' }}>{error}</div>}
        <div style={{ marginBottom: '15px' }}>
          <label htmlFor="email">Email:</label><br />
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
          />
        </div>
        <div style={{ marginBottom: '15px' }}>
          <label htmlFor="password">Senha:</label><br />
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          style={{ width: '100%', padding: '10px', backgroundColor: loading ? '#ccc' : '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: loading ? 'not-allowed' : 'pointer' }}
        >
          {loading ? 'Entrando...' : 'Entrar'}
        </button>
      </form>
      {/* Link para a página de registro */}
      <div style={{ marginTop: '20px', textAlign: 'center' }}>
        <p>Não tem conta? <Link to="/register">Crie uma agora</Link></p>
      </div>
    </div>
  );
}

export default LoginPage;