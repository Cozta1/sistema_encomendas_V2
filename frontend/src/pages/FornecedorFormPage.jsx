import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link, Navigate } from 'react-router-dom';
import api from '../services/api';

function FornecedorFormPage() {
  const { fornecedorId, equipeId } = useParams(); // Pega ambos os IDs da URL
  const navigate = useNavigate();
  const isEditing = Boolean(fornecedorId); // Define se está em modo de edição
  const token = localStorage.getItem('accessToken');

  // Estado para os dados do formulário
  const [formData, setFormData] = useState({
    nome: '',
    codigo: '',
    contato: '',
    telefone: '',
    email: '',
    equipe_id: equipeId || '', // Pré-define a equipe com o ID da URL
  });

  // Estados de controle
  const [loading, setLoading] = useState(isEditing); // Carrega se estiver editando
  const [error, setError] = useState(null);
  const [formErrors, setFormErrors] = useState({}); // Para erros de validação da API
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [equipeNome, setEquipeNome] = useState(''); // Para exibir o nome da equipe

  // Busca dados do fornecedor (se editando) ou nome da equipe (se criando)
  useEffect(() => {
    const fetchData = async () => {
      if (!equipeId) {
          setError("ID da Equipe não encontrado na URL.");
          setLoading(false);
          return;
      }

      setLoading(true);
      setError(null);
      
      try {
        if (isEditing) {
          // Modo Edição: Busca dados do fornecedor
          const response = await api.get(`/fornecedores/${fornecedorId}/`);
          const fornecedor = response.data;
          setFormData({
            nome: fornecedor.nome || '',
            codigo: fornecedor.codigo || '',
            contato: fornecedor.contato || '',
            telefone: fornecedor.telefone || '',
            email: fornecedor.email || '',
            equipe_id: fornecedor.equipe_id || equipeId, // Confirma a equipe
          });
          setEquipeNome(fornecedor.equipe_nome || ''); // Pega o nome da equipe
        } else {
          // Modo Criação: Apenas busca o nome da equipe para exibir
           try {
               const teamData = await api.get('/my-teams-invites/');
               const foundTeam = teamData.data.teams.find(t => t.id === equipeId);
               if (foundTeam) {
                   setEquipeNome(foundTeam.nome);
               } else { setEquipeNome(`Equipe (ID: ${equipeId.substring(0,8)}... )`); }
           // eslint-disable-next-line no-unused-vars
           } catch (e) {
               setEquipeNome(`Equipe (ID: ${equipeId.substring(0,8)}... )`);
           }
        }
      } catch (err) {
        console.error("Erro ao carregar dados para formulário:", err);
        setError("Falha ao carregar dados. Verifique o console.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [fornecedorId, equipeId, isEditing]); // Depende dos IDs da URL

  // Handler para mudanças nos campos
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // --- Submissão ---
  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setFormErrors({});

    // Payload final
    const payload = {
      ...formData,
      equipe: equipeId, // Garante que a equipe está sendo enviada (backend espera 'equipe')
    };
    delete payload.equipe_id; 

    console.log("Submit Payload:", payload);

    try {
      if (isEditing) {
        // Requisição PUT para atualizar
        await api.put(`/fornecedores/${fornecedorId}/`, payload);
      } else {
        // Requisição POST para criar
        await api.post('/fornecedores/', payload);
      }
      
      alert(`Fornecedor ${isEditing ? 'atualizado' : 'criado'} com sucesso!`);
      // Redireciona de volta para a lista de fornecedores da equipe
      navigate(`/fornecedores/equipe/${equipeId}`);

    } catch (err) {
      console.error("Erro ao salvar fornecedor:", err.response || err);
      if (err.response?.data && typeof err.response.data === 'object') {
           setFormErrors(err.response.data);
           const nonFieldErrors = err.response.data.non_field_errors || err.response.data.detail;
           setError(nonFieldErrors || "Erro de validação. Verifique os campos marcados.");
      } else {
           setError(err.response?.data?.detail || `Erro ${err.response?.status || ''} ao salvar.`);
      }
      setIsSubmitting(false); // Libera o botão em caso de erro
    }
  };
  
  // --- Funções Auxiliares de Renderização ---
  const getFieldError = (fieldName) => {
     if (formErrors && formErrors[fieldName]) {
         return <small className="text-danger d-block mt-1">{formErrors[fieldName][0]}</small>;
     }
     return null;
  };

  // --- Renderização ---
  if (!token) return <Navigate to="/login" replace />;

  if (loading) {
    return <div style={{ padding: '20px' }}>Carregando dados do formulário...</div>;
  }

  // Erro fatal (ex: equipeId não existe ou falha ao carregar)
  if (error && !Object.keys(formErrors).length) {
     return (
         <div style={{ padding: '20px' }} className="alert alert-danger">
             Erro: {error} <br />
             <Link to="/equipes" className="alert-link">Voltar para equipes</Link>
         </div>
     );
  }

  return (
    <div>
      {/* Cabeçalho */}
      <div className="page-header">
           <h1>
               <i className={`bi bi-${isEditing ? 'pencil-square' : 'truck'} me-3`}></i>
               {isEditing ? `Editar Fornecedor` : 'Novo Fornecedor'}
            </h1>
            <p className="mb-0 text-muted">
              {isEditing ? `Modificando dados de ${formData.nome || 'fornecedor...'}` : `Adicionando fornecedor para a equipe ${equipeNome}`}
            </p>
      </div>

      {/* Exibe erro geral de validação */}
      {error && <div className="alert alert-danger">{error}</div>}

      <form onSubmit={handleSubmit} noValidate>
        <div className="card form-section mb-4">
          <div className="card-header"><h5 className="mb-0">Dados do Fornecedor (Equipe: {equipeNome})</h5></div>
          <div className="card-body">
            <div className="row">
              {/* Nome */}
              <div className="col-md-6 mb-3">
                <label htmlFor="nome" className="form-label">Nome *</label>
                <input
                  type="text"
                  id="nome"
                  name="nome"
                  className={`form-control ${getFieldError('nome') ? 'is-invalid' : ''}`}
                  value={formData.nome}
                  onChange={handleChange}
                  required
                />
                {getFieldError('nome')}
              </div>
              {/* Código */}
              <div className="col-md-6 mb-3">
                <label htmlFor="codigo" className="form-label">Código *</label>
                <input
                  type="text"
                  id="codigo"
                  name="codigo"
                  className={`form-control ${getFieldError('codigo') ? 'is-invalid' : ''}`}
                  value={formData.codigo}
                  onChange={handleChange}
                  required
                />
                {getFieldError('codigo')}
                <small className="text-muted">Deve ser único dentro da equipe.</small>
              </div>
            </div>

            <div className="row">
                {/* Contato */}
                <div className="col-md-6 mb-3">
                    <label htmlFor="contato" className="form-label">Nome de Contato</label>
                    <input
                        type="text"
                        id="contato"
                        name="contato"
                        className={`form-control ${getFieldError('contato') ? 'is-invalid' : ''}`}
                        value={formData.contato}
                        onChange={handleChange}
                    />
                    {getFieldError('contato')}
                </div>
                {/* Telefone */}
                <div className="col-md-6 mb-3">
                    <label htmlFor="telefone" className="form-label">Telefone</label>
                    <input
                        type="tel"
                        id="telefone"
                        name="telefone"
                        className={`form-control ${getFieldError('telefone') ? 'is-invalid' : ''}`}
                        value={formData.telefone}
                        onChange={handleChange}
                        placeholder="(XX) XXXXX-XXXX"
                    />
                    {getFieldError('telefone')}
                </div>
            </div>

            {/* E-mail */}
            <div className="col-12 mb-3">
              <label htmlFor="email" className="form-label">E-mail</label>
              <input
                type="email"
                id="email"
                name="email"
                className={`form-control ${getFieldError('email') ? 'is-invalid' : ''}`}
                value={formData.email}
                onChange={handleChange}
                placeholder="contato@fornecedor.com"
              />
              {getFieldError('email')}
            </div>
          </div>
        </div>

        {/* --- Botões de Ação --- */}
        <div className="d-flex justify-content-between mt-4 mb-5">
            <Link to={`/fornecedores/equipe/${equipeId}`} className="btn btn-secondary">
                <i className="bi bi-x-circle me-2"></i>Cancelar
            </Link>
            <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                {isSubmitting ? (
                    <><span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Salvando...</>
                ) : (
                    <><i className="bi bi-check-circle me-2"></i> {isEditing ? 'Atualizar' : 'Salvar'} Fornecedor</>
                )}
            </button>
        </div>

      </form>
    </div>
  );
}

export default FornecedorFormPage;