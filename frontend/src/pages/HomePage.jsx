import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * Esta página serve como a rota "index" (/).
 * Ela verifica se o usuário tem uma equipe ativa na sessão
 * e o redireciona para o dashboard dessa equipe ou para a lista de equipes.
 */
function HomePage() {
  const navigate = useNavigate();

  useEffect(() => {
    // Tenta buscar a equipe ativa no sessionStorage
    const activeTeamId = sessionStorage.getItem('currentTeamId');
    
    if (activeTeamId) {
      // Se encontrou, vai para o dashboard da equipe ativa
      navigate(`/dashboard/${activeTeamId}`, { replace: true });
    } else {
      // Se não encontrou, vai para a seleção de equipes
      navigate('/equipes', { replace: true });
    }
  }, [navigate]); // Dependência: navigate

  // Renderiza um loader ou mensagem enquanto redireciona
  return <div style={{ padding: '20px' }}>Carregando página inicial...</div>;
}

export default HomePage;