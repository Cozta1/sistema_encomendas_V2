import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link, Navigate } from 'react-router-dom';
import api from '../services/api';

function ProdutoFormPage() {
  const { produtoId, equipeId } = useParams(); // Pega ambos os IDs da URL
  const navigate = useNavigate();
  const isEditing = Boolean(produtoId); // Define se está em modo de edição
  const token = localStorage.getItem('accessToken');

  // Estado para os dados do formulário
  const [formData, setFormData] = useState({
    nome: '',
    codigo: '',
    categoria: '',
    preco_base: '0.00',
    descricao: '',
    equipe_id: equipeId || '', // Pré-define a equipe com o ID da URL
  });

  // Estados de controle
  const [loading, setLoading] = useState(isEditing); // Carrega se estiver editando
  const [error, setError] = useState(null);
  const [formErrors, setFormErrors] = useState({}); // Para erros de validação da API
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [equipeNome, setEquipeNome] = useState(''); // Para exibir o nome da equipe

  // Busca dados do produto (se editando) ou nome da equipe (se criando)
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
          // Modo Edição: Busca dados do produto
          const response = await api.get(`/produtos/${produtoId}/`);
          const produto = response.data;
          setFormData({
            nome: produto.nome || '',
            codigo: produto.codigo || '',
            categoria: produto.categoria || '',
            preco_base: parseFloat(produto.preco_base || 0).toFixed(2),
            descricao: produto.descricao || '',
            equipe_id: produto.equipe_id || equipeId, // Confirma a equipe
          });
          setEquipeNome(produto.equipe_nome || ''); // Pega o nome da equipe
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
  }, [produtoId, equipeId, isEditing]); // Depende dos IDs da URL

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
      preco_base: parseFloat(formData.preco_base).toFixed(2), // Garante formato decimal
      equipe: equipeId, // Garante que a equipe está sendo enviada (backend espera 'equipe')
    };
    delete payload.equipe_id; 

    console.log("Submit Payload:", payload);

    try {
      if (isEditing) {
        // Requisição PUT para atualizar
        await api.put(`/produtos/${produtoId}/`, payload);
      } else {
        // Requisição POST para criar
        await api.post('/produtos/', payload);
      }
      
      alert(`Produto ${isEditing ? 'atualizado' : 'criado'} com sucesso!`);
      // Redireciona de volta para a lista de produtos da equipe
      navigate(`/produtos/equipe/${equipeId}`);

    } catch (err) {
      console.error("Erro ao salvar produto:", err.response || err);
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
               <i className={`bi bi-${isEditing ? 'pencil-square' : 'box'} me-3`}></i>
               {isEditing ? `Editar Produto` : 'Novo Produto'}
            </h1>
            <p className="mb-0 text-muted">
              {isEditing ? `Modificando dados de ${formData.nome || 'produto...'}` : `Adicionando produto para a equipe ${equipeNome}`}
            </p>
      </div>

      {/* Exibe erro geral de validação */}
      {error && <div className="alert alert-danger">{error}</div>}

      <form onSubmit={handleSubmit} noValidate>
        <div className="card form-section mb-4">
          <div className="card-header"><h5 className="mb-0">Dados do Produto (Equipe: {equipeNome})</h5></div>
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
                {/* Categoria */}
                <div className="col-md-6 mb-3">
                    <label htmlFor="categoria" className="form-label">Categoria</label>
                    <input
                        type="text"
                        id="categoria"
                        name="categoria"
                        className={`form-control ${getFieldError('categoria') ? 'is-invalid' : ''}`}
                        value={formData.categoria}
                        onChange={handleChange}
                    />
                    {getFieldError('categoria')}
                </div>
                {/* Preço Base */}
                <div className="col-md-6 mb-3">
                    <label htmlFor="preco_base" className="form-label">Preço Base *</label>
                    <div className="input-group">
                        <span className="input-group-text">R$</span>
                        <input
                            type="number"
                            step="0.01"
                            min="0.00"
                            id="preco_base"
                            name="preco_base"
                            className={`form-control ${getFieldError('preco_base') ? 'is-invalid' : ''}`}
                            value={formData.preco_base}
                            onChange={handleChange}
                            required
                        />
                    </div>
                    {getFieldError('preco_base')}
                </div>
            </div>

            {/* Descrição */}
            <div className="col-12 mb-3">
              <label htmlFor="descricao" className="form-label">Descrição</label>
              <textarea
                id="descricao"
                name="descricao"
                rows="3"
                className={`form-control ${getFieldError('descricao') ? 'is-invalid' : ''}`}
                value={formData.descricao}
                onChange={handleChange}
              ></textarea>
              {getFieldError('descricao')}
            </div>

          </div>
        </div>

        {/* --- Botões de Ação --- */}
        <div className="d-flex justify-content-between mt-4 mb-5">
            <Link to={`/produtos/equipe/${equipeId}`} className="btn btn-secondary">
                <i className="bi bi-x-circle me-2"></i>Cancelar
            </Link>
            <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                {isSubmitting ? (
                    <><span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Salvando...</>
                ) : (
                    <><i className="bi bi-check-circle me-2"></i> {isEditing ? 'Atualizar' : 'Salvar'} Produto</>
                )}
            </button>
        </div>

      </form>
    </div>
  );
}

export default ProdutoFormPage;