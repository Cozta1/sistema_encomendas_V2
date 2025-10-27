import React, { useState, useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import api from '../services/api';

function EncomendasPage() {
  const [encomendas, setEncomendas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchEncomendas = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await api.get('/encomendas/');

         // Verifica se a resposta contém 'results' (paginação DRF)
         if (response.data && Array.isArray(response.data)) {
             setEncomendas(response.data);
         } else if (response.data && response.data.results && Array.isArray(response.data.results)) {
             setEncomendas(response.data.results);
         } else {
              console.warn("Resposta da API não esperada:", response.data);
              setEncomendas([]);
         }

      } catch (err) {
        console.error('Erro ao buscar encomendas:', err);
        if (err.response) {
          if (err.response.status === 401 || err.response.status === 403) {
            setError('Acesso negado.');
            // Lógica de logout/redirecionamento pode ser adicionada
          } else {
            setError(`Erro da API: ${err.response.status}`);
          }
        } else {
          setError('Erro de conexão.');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchEncomendas();
  }, []);

   // Proteção básica da rota
   const token = localStorage.getItem('accessToken');
   if (!token && !loading) {
       return <Navigate to="/login" replace />;
   }

  if (loading) return <div style={{ padding: '20px' }}>Carregando...</div>;
  if (error) return <div style={{ padding: '20px', color: 'red' }}>Erro: {error}</div>;

  return (
    <div style={{ padding: '20px' }}>
      <h1>Lista de Encomendas</h1>
      {encomendas.length === 0 ? (
        <p>Nenhuma encomenda encontrada.</p>
      ) : (
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {encomendas.map((encomenda) => (
            <li key={encomenda.numero_encomenda} style={{ borderBottom: '1px solid #eee', padding: '10px 0' }}>
              <strong>#{encomenda.numero_encomenda}</strong> - {encomenda.cliente_nome} ({encomenda.equipe_nome})<br />
              Status: {encomenda.status_display} | Valor: R$ {encomenda.valor_total}<br />
              <small>Criada em: {new Date(encomenda.data_criacao).toLocaleString('pt-BR')}</small>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default EncomendasPage;