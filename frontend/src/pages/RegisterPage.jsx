import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../services/api';

function RegisterPage() {
  const [formData, setFormData] = useState({
    email: '',
    nome_completo: '',
    identificacao: '',
    cargo: '',
    telefone: '',
    password: '',
    password2: '',
  });
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prevState => ({
      ...prevState,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);
    setLoading(true);

    if (formData.password !== formData.password2) {
      setError({ password2: ["As senhas não coincidem."] });
      setLoading(false);
      return;
    }

    try {
      const response = await api.post('/users/register/', formData);
      setSuccessMessage(response.data.message || "Registro bem-sucedido! Redirecionando...");
      setTimeout(() => {
        navigate('/login');
      }, 2000);

    } catch (err) {
      setLoading(false);
      if (err.response) {
        console.error('API Error:', err.response.data);
        if (err.response.data && typeof err.response.data === 'object') {
          setError(err.response.data);
        } else {
          setError(err.response.data?.detail || 'Erro no registro.');
        }
      } else if (err.request) {
        setError('Erro de conexão.');
      } else {
        setError('Erro inesperado.');
      }
    }
  };

  const getFieldError = (fieldName) => {
    if (error && typeof error === 'object' && error[fieldName]) {
      return <div style={{ color: 'red', fontSize: '0.8em', marginTop: '4px' }}>{error[fieldName][0]}</div>;
    }
    return null;
  };

  return (
    <div style={{ maxWidth: '500px', margin: '30px auto', padding: '30px', border: '1px solid #ccc', borderRadius: '8px' }}>
      <h2>Criar Conta</h2>
      <form onSubmit={handleSubmit} noValidate>
        {successMessage && <div style={{ color: 'green', marginBottom: '15px', fontWeight: 'bold' }}>{successMessage}</div>}
        {error && typeof error === 'string' && <div style={{ color: 'red', marginBottom: '15px' }}>{error}</div>}

        {Object.keys(formData).map((key) => {
          if (key === 'telefone' && !formData[key]) formData[key] = '';
          const labelMap = {
            email: 'Email *', nome_completo: 'Nome Completo *', identificacao: 'Identificação (CPF/CNPJ) *', cargo: 'Cargo *',
            telefone: 'Telefone (Opcional)', password: 'Senha *', password2: 'Confirmar Senha *',
          };
          const typeMap = { email: 'email', password: 'password', password2: 'password', telefone: 'tel', /* others default to text */ };
          const isRequired = !['telefone'].includes(key);

          return (
            <div key={key} style={{ marginBottom: '15px' }}>
              <label htmlFor={key}>{labelMap[key]}:</label><br />
              <input
                type={typeMap[key] || 'text'}
                id={key}
                name={key}
                value={formData[key]}
                onChange={handleChange}
                required={isRequired}
                style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
                autoComplete={key.includes('password') ? 'new-password' : 'off'}
              />
              {getFieldError(key)}
            </div>
          );
        })}

        <button
          type="submit"
          disabled={loading}
          style={{ width: '100%', padding: '10px', backgroundColor: loading ? '#ccc' : '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: loading ? 'not-allowed' : 'pointer', marginTop: '10px' }}
        >
          {loading ? 'Registrando...' : 'Criar Conta'}
        </button>
      </form>
      <div style={{ marginTop: '20px', textAlign: 'center' }}>
        <p>Já tem uma conta? <Link to="/login">Faça login aqui</Link></p>
      </div>
    </div>
  );
}

export default RegisterPage;