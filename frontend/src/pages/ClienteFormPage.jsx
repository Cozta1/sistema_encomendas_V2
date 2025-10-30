import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link, Navigate } from 'react-router-dom';
import api from '../services/api';

// (Opcional) Importar componentes UI (Card, Button, TextField, etc.)

function ClienteFormPage() {
  const { clienteId, equipeId } = useParams(); // Pega ambos os IDs da URL
  const navigate = useNavigate();
  const isEditing = Boolean(clienteId); // Define se está em modo de edição
  const token = localStorage.getItem('accessToken');

  // Estado para os dados do formulário
  const [formData, setFormData] = useState({
    nome: '',
    codigo: '',
    endereco: '',
    bairro: '',
    referencia: '',
    telefone: '',
    equipe_id: equipeId || '', // Pré-define a equipe com o ID da URL
  });

  // Estados de controle
  const [loading, setLoading] = useState(isEditing); // Carrega se estiver editando
  const [error, setError] = useState(null);
  const [formErrors, setFormErrors] = useState({}); // Para erros de validação da API
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [equipeNome, setEquipeNome] = useState(''); // Para exibir o nome da equipe

  // Busca dados do cliente (se editando) ou nome da equipe (se criando)
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
          // Modo Edição: Busca dados do cliente
          const response = await api.get(`/clientes/${clienteId}/`);
          const cliente = response.data;
          setFormData({
            nome: cliente.nome || '',
            codigo: cliente.codigo || '',
            endereco: cliente.endereco || '',
            bairro: cliente.bairro || '',
            referencia: cliente.referencia || '',
            telefone: cliente.telefone || '',
            equipe_id: cliente.equipe_id || equipeId, // Confirma a equipe
          });
          setEquipeNome(cliente.equipe_nome || ''); // Pega o nome da equipe
        } else {
          // Modo Criação: Apenas busca o nome da equipe para exibir
          // (Esta chamada pode falhar se a API não tiver /api/equipes/{id})
          // Uma alternativa é buscar /my-teams-invites/ e filtrar
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
  }, [clienteId, equipeId, isEditing]); // Depende dos IDs da URL

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
    // Remove equipe_id se 'equipe' já está presente
    delete payload.equipe_id; 

    console.log("Submit Payload:", payload);

    try {
      if (isEditing) {
        // Requisição PUT para atualizar
        await api.put(`/clientes/${clienteId}/`, payload);
      } else {
        // Requisição POST para criar
        await api.post('/clientes/', payload);
      }
      
      alert(`Cliente ${isEditing ? 'atualizado' : 'criado'} com sucesso!`);
      // Redireciona de volta para a lista de clientes da equipe
      navigate(`/clientes/equipe/${equipeId}`);

    } catch (err) {
      console.error("Erro ao salvar cliente:", err.response || err);
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
               <i className={`bi bi-${isEditing ? 'pencil-square' : 'person-plus'} me-3`}></i>
               {isEditing ? `Editar Cliente` : 'Novo Cliente'}
            </h1>
            <p className="mb-0 text-muted">
              {isEditing ? `Modificando dados de ${formData.nome || 'cliente...'}` : `Adicionando cliente para a equipe ${equipeNome}`}
            </p>
      </div>

      {/* Exibe erro geral de validação */}
      {error && <div className="alert alert-danger">{error}</div>}

      <form onSubmit={handleSubmit} noValidate>
        <div className="card form-section mb-4">
          <div className="card-header"><h5 className="mb-0">Dados do Cliente</h5></div>
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

            {/* Endereço */}
            <div className="col-12 mb-3">
              <label htmlFor="endereco" className="form-label">Endereço</label>
              <textarea
                id="endereco"
                name="endereco"
                rows="3"
                className={`form-control ${getFieldError('endereco') ? 'is-invalid' : ''}`}
                value={formData.endereco}
                onChange={handleChange}
              ></textarea>
              {getFieldError('endereco')}
            </div>
            
            <div className="row">
                {/* Bairro */}
                <div className="col-md-6 mb-3">
                    <label htmlFor="bairro" className="form-label">Bairro</label>
                    <input
                        type="text"
                        id="bairro"
                        name="bairro"
                        className={`form-control ${getFieldError('bairro') ? 'is-invalid' : ''}`}
                        value={formData.bairro}
                        onChange={handleChange}
                    />
                    {getFieldError('bairro')}
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

            {/* Referência */}
            <div className="col-12 mb-3">
              <label htmlFor="referencia" className="form-label">Referência</label>
              <input
                type="text"
                id="referencia"
                name="referencia"
                className={`form-control ${getFieldError('referencia') ? 'is-invalid' : ''}`}
                value={formData.referencia}
                onChange={handleChange}
                placeholder="Ponto de referência (opcional)"
              />
              {getFieldError('referencia')}
            </div>
          </div>
        </div>

        {/* --- Botões de Ação --- */}
        <div className="d-flex justify-content-between mt-4 mb-5">
            <Link to={`/clientes/equipe/${equipeId}`} className="btn btn-secondary">
                <i className="bi bi-x-circle me-2"></i>Cancelar
            </Link>
            <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                {isSubmitting ? (
                    <><span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Salvando...</>
                ) : (
                    <><i className="bi bi-check-circle me-2"></i> {isEditing ? 'Atualizar' : 'Salvar'} Cliente</>
                )}
            </button>
        </div>

      </form>
    </div>
  );
}

export default ClienteFormPage;

