import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import api from '../services/api';

function AceitarConvitePage() {
  const { conviteId } = useParams(); // Pega o ID do convite da URL
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successData, setSuccessData] = useState(null); // Para guardar dados da equipe

  useEffect(() => {
    const aceitarConvite = async () => {
      setLoading(true);
      setError(null);
      try {
        // Tenta fazer o POST para aceitar o convite
        // Assumindo API: POST /api/convites/{id}/aceitar/
        const response = await api.post(`/api/convites/${conviteId}/aceitar/`);
        
        // Sucesso! A API deve retornar os dados da equipe
        const equipe = response.data.equipe; 
        setSuccessData(equipe);

        // Define a nova equipe como ativa na sessão
        sessionStorage.setItem('currentTeamId', equipe.id);

        // Redireciona para o dashboard da nova equipe após 5s
        setTimeout(() => {
          navigate(`/dashboard/${equipe.id}`);
        }, 5000);

      } catch (err) {
        console.error("Erro ao aceitar convite:", err);
        setError(err.response?.data?.detail || "Convite inválido, expirado ou você já faz parte desta equipe.");
      } finally {
        setLoading(false);
      }
    };

    if (conviteId) {
      aceitarConvite();
    } else {
      setError("Nenhum ID de convite fornecido.");
      setLoading(false);
    }
    // O array de dependência vazio [] garante que isso rode apenas uma vez
  }, [conviteId, navigate]); 

  // --- Renderização ---

  const renderContent = () => {
    if (loading) {
      return (
        <div className="text-center">
          <div className="spinner-border text-primary" role="status" style={{ width: '3rem', height: '3rem' }}>
            <span className="visually-hidden">Loading...</span>
          </div>
          <h3 className="mt-3">Processando seu convite...</h3>
        </div>
      );
    }

    if (error) {
      return (
        <div className="text-center">
          <i className="bi bi-x-circle-fill text-danger" style={{ fontSize: '3rem' }}></i>
          <h3 className="mt-3">Erro ao aceitar o convite</h3>
          <p className="text-muted">{error}</p>
          <Link to="/equipes" className="btn btn-primary">
            Ver minhas equipes
          </Link>
        </div>
      );
    }

    if (successData) {
      return (
        <div className="text-center">
          <i className="bi bi-check-circle-fill text-success" style={{ fontSize: '3rem' }}></i>
          <h3 className="mt-3">Bem-vindo(a)!</h3>
          <p className="text-muted">
            Você agora é membro da equipe G. Você será redirecionado em instantes.
          </p>
          <Link to={`/dashboard/${successData.id}`} className="btn btn-success">
            <i className="bi bi-speedometer2 me-2"></i>Ir para o Dashboard
          </Link>
        </div>
      );
    }
    
    return null; // Caso inicial
  };

  return (
    // Esta página será renderizada dentro do Layout
    <div className="d-flex align-items-center justify-content-center" style={{ minHeight: '60vh' }}>
       <div className="card" style={{ width: '100%', maxWidth: '500px' }}>
            <div className="card-body p-4 p-md-5">
                {renderContent()}
            </div>
       </div>
    </div>
  );
}

export default AceitarConvitePage;