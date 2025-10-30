import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link, Navigate } from 'react-router-dom';
import api from '../services/api';

function ClienteFormPage() {
  const { clienteId, equipeId: equipeIdFromUrl } = useParams();
  const navigate = useNavigate();
  const isEditing = Boolean(clienteId);
  const token = localStorage.getItem('accessToken');

  const [formData, setFormData] = useState({
    nome: '',
    codigo: '',
    endereco: '',
    bairro: '',
    referencia: '',
    telefone: '',
  });
  
  // Armazena o ID da equipe (seja da URL na criação ou do cliente na edição)
  const [equipeId, setEquipeId] = useState(equipeIdFromUrl || null);
  const [equipeNome, setEquipeNome] = useState(''); // Para exibir o nome da equipe
  
  const [loading, setLoading] = useState(isEditing); // Só carrega se estiver editando
  const [error, setError] = useState(null);
  const [formErrors, setFormErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Efeito para buscar dados do cliente (se editando) ou dados da equipe (se criando)
  useEffect(() => {
    const fetchData = async () => {
      if (isEditing) {
        // Modo Edição: Buscar dados do cliente
        setLoading(true);
        setError(null);
        try {
          const response = await api.get(`/clientes/${clienteId}/`);
          setFormData({
            nome: response.data.nome || '',
            codigo: response.data.codigo || '',
            endereco: response.data.endereco || '',
            bairro: response.data.bairro || '',
            referencia: response.data.referencia || '',
            telefone: response.data.telefone || '',
          });
          // Define a equipe com base nos dados do cliente
          setEquipeId(response.data.equipe_id); // Assumindo que o serializer envia equipe_id
          setEquipeNome(response.data.equipe_nome || ''); // Assumindo que o serializer envia equipe_nome
        } catch (err) {
          console.error("Erro ao buscar cliente:", err);
          setError("Falha ao carregar dados do cliente.");
        } finally {
          setLoading(false);
        }
      } else if (equipeIdFromUrl) {
        // Modo Criação: Apenas definir o ID da equipe e buscar o nome
        setEquipeId(equipeIdFromUrl);
         // Tenta buscar o nome da equipe para exibir no título (opcional)
         api.get(`/equipes/${equipeIdFromUrl}/`) // Assume endpoint /api/equipes/{id}/
             .then(res => setEquipeNome(res.data.nome))
             .catch(() => setEquipeNome(`Equipe ${equipeIdFromUrl.substring(0,8)}...`));
        setLoading(false); // Não há dados de cliente para carregar
      } else {
        // Erro: Nem editando, nem criando com ID de equipe
        setError("ID da Equipe não especificado para criar um novo cliente.");
        setLoading(false);
      }
    };

    fetchData();
  }, [clienteId, isEditing, equipeIdFromUrl]);

  // Handler para mudanças nos campos
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // Handler para submissão
  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setFormErrors({});

    const payload = { ...formData };

    try {
      let response;
      if (isEditing) {
        // Modo Edição (PUT)
        // Não precisamos enviar equipe_id, pois o backend não deve permitir mudar a equipe de um cliente
        response = await api.put(`/clientes/${clienteId}/`, payload);
      } else {
        // Modo Criação (POST)
        // Adicionamos equipe_id ao payload para o ViewSet saber a qual equipe associar
        payload.equipe_id = equipeId;
        // eslint-disable-next-line no-unused-vars
        response = await api.post('/clientes/', payload);
      }
      
      // Sucesso
      alert(`Cliente ${isEditing ? 'atualizado' : 'criado'} com sucesso!`);
      navigate(`/clientes/equipe/${equipeId}`); // Retorna para a lista de clientes da equipe

    } catch (err) {
      console.error("Erro ao salvar cliente:", err.response || err);
      if (err.response?.data && typeof err.response.data === 'object') {
           setFormErrors(err.response.data);
           const nonFieldErrors = err.response.data.non_field_errors || err.response.data.detail;
           setError(nonFieldErrors || "Erro de validação. Verifique os campos marcados.");
      } else {
           setError(err.response?.data?.detail || `Erro ${err.response?.status || ''} ao salvar.`);
      }
      setIsSubmitting(false); // Libera o botão
    }
  };
  
  // Função auxiliar para erros de formulário
  const getFieldError = (fieldName) => {
    if (formErrors && formErrors[fieldName]) {
        return <small className="text-danger d-block mt-1">{formErrors[fieldName][0]}</small>;
    }
    return null;
  };

  // --- Renderização ---
  if (!token) return <Navigate to="/login" replace />;

  if (loading) {
    return <div style={{ padding: '20px' }}>Carregando dados do cliente...</div>;
  }
  
  // Erro geral (não de validação de formulário)
   if (error && !Object.keys(formErrors).length) {
        return (
            <div style={{ padding: '20px' }} className="alert alert-danger">
                Erro: {error} <br />
                <Link to={equipeId ? `/clientes/equipe/${equipeId}` : '/equipes'} className="alert-link">
                   Voltar para a lista
                </Link>
            </div>
        );
   }
   // Erro: Falta equipeId
    if (!equipeId) {
         return (
             <div style={{ padding: '20px' }} className="alert alert-danger">
                 Erro: Nenhuma equipe selecionada. <br />
                 <Link to="/equipes" className="alert-link">Selecione uma equipe primeiro.</Link>
             </div>
         );
    }


  return (
    <div>
      {/* Cabeçalho */}
      <div className="page-header">
        <h1>
          <i className={`bi bi-${isEditing ? 'pencil-square' : 'person-plus'} me-3`}></i>
          {isEditing ? `Editar Cliente (Cód: ${formData.codigo})` : 'Novo Cliente'}
        </h1>
        <p className="mb-0 text-muted">
           {isEditing ? `Editando dados de ${formData.nome}` : `Criando novo cliente para a equipe: ${equipeNome}`}
        </p>
      </div>
      
      {/* Exibe erro geral de validação */}
      {error && <div className="alert alert-danger">{error}</div>}

      <form onSubmit={handleSubmit} noValidate>
        <div className="card form-section mb-4">
          <div className="card-header">
            <h5 className="mb-0">Dados do Cliente {equipeNome ? `(Equipe: ${equipeNome})` : ''}</h5>
          </div>
          <div className="card-body">
            <div className="row">
              {/* Nome */}
              <div className="col-md-6 mb-3">
                <label htmlFor="nome" className="form-label">Nome Completo *</label>
                <input
                  type="text" id="nome" name="nome" required
                  className={`form-control ${getFieldError('nome') ? 'is-invalid' : ''}`}
                  value={formData.nome}
                  onChange={handleChange}
                  placeholder="Nome completo do cliente"
                />
                {getFieldError('nome')}
              </div>
              {/* Código */}
              <div className="col-md-6 mb-3">
                <label htmlFor="codigo" className="form-label">Código *</label>
                <input
                  type="text" id="codigo" name="codigo" required
                  className={`form-control ${getFieldError('codigo') ? 'is-invalid' : ''}`}
                  value={formData.codigo}
                  onChange={handleChange}
                  placeholder="Código único do cliente (ex: CLI001)"
                />
                {getFieldError('codigo')}
                {!isEditing && <small className="text-muted">Deve ser único dentro da equipe.</small>}
              </div>
            </div>
            
            {/* Endereço */}
            <div className="col-12 mb-3">
              <label htmlFor="endereco" className="form-label">Endereço *</label>
              <textarea
                id="endereco" name="endereco" required rows="3"
                className={`form-control ${getFieldError('endereco') ? 'is-invalid' : ''}`}
                value={formData.endereco}
                onChange={handleChange}
                placeholder="Rua, número, complemento..."
              ></textarea>
              {getFieldError('endereco')}
            </div>
            
            <div className="row">
              {/* Bairro */}
              <div className="col-md-6 mb-3">
                <label htmlFor="bairro" className="form-label">Bairro *</label>
                <input
                  type="text" id="bairro" name="bairro" required
                  className={`form-control ${getFieldError('bairro') ? 'is-invalid' : ''}`}
                  value={formData.bairro}
                  onChange={handleChange}
                  placeholder="Bairro"
                />
                {getFieldError('bairro')}
              </div>
              {/* Telefone */}
              <div className="col-md-6 mb-3">
                <label htmlFor="telefone" className="form-label">Telefone (Opcional)</label>
                <input
                  type="tel" id="telefone" name="telefone"
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
              <label htmlFor="referencia" className="form-label">Referência (Opcional)</label>
              <input
                type="text" id="referencia" name="referencia"
                className={`form-control ${getFieldError('referencia') ? 'is-invalid' : ''}`}
                value={formData.referencia}
                onChange={handleChange}
                placeholder="Ponto de referência (ex: Próximo à padaria)"
              />
              {getFieldError('referencia')}
            </div>
            
          </div>
        </div>

        {/* Botões de Ação */}
        <div className="d-flex justify-content-between mt-4 mb-5">
          <Link to={`/clientes/equipe/${equipeId}`} className="btn btn-secondary">
            <i className="bi bi-x-circle me-2"></i>Cancelar
          </Link>
          <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
            {isSubmitting ? (
              <><span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Salvando...</>
            ) : (
              <><i className="bi bi-check-circle me-2"></i> {isEditing ? 'Atualizar Cliente' : 'Criar Cliente'}</>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

export default ClienteFormPage;
