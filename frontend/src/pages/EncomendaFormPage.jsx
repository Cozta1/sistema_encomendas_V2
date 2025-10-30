import React, { useState, useEffect } from 'react'; // Removido useCallback
import { useParams, useNavigate, Link, Navigate } from 'react-router-dom';
import api from '../services/api';
// IMPORTANTE: Importar Autocomplete e TextField do Material UI
import { Autocomplete, TextField } from '@mui/material';

// Estrutura inicial de um item vazio
const initialItemState = {
    produto_id: null,
    fornecedor_id: null,
    quantidade: 1,
    preco_base: '', // <-- Adicionado para Preço Base
    preco_cotado: '',
    observacoes: '',
};

// Opções de Status
const STATUS_CHOICES = [
     { value: 'criada', label: 'Criada' },
     { value: 'cotacao', label: 'Em Cotação' },
     { value: 'aprovada', label: 'Aprovada' },
     { value: 'em_andamento', label: 'Em Andamento' },
     { value: 'pronta', label: 'Pronta para Entrega' },
     { value: 'entregue', label: 'Entregue' },
     { value: 'cancelada', label: 'Cancelada' },
];

function EncomendaFormPage() {
  const { encomendaId, equipeId: equipeIdFromUrl } = useParams();
  const navigate = useNavigate();
  const isEditing = Boolean(encomendaId);
  const token = localStorage.getItem('accessToken');

  // Estados
  const [encomendaData, setEncomendaData] = useState({
    cliente_id: '',
    data_encomenda: new Date().toISOString().split('T')[0],
    responsavel_criacao: '',
    status: 'criada',
    observacoes: '',
    equipe_id: equipeIdFromUrl || '',
  });
  const [items, setItems] = useState([{ ...initialItemState }]);
  const [clienteOptions, setClienteOptions] = useState([{ value: '', label: 'Carregando...' }]);
  const [produtoOptions, setProdutoOptions] = useState([]);
  const [fornecedorOptions, setFornecedorOptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [formErrors, setFormErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // --- Função Auxiliar ---
  const getCurrentUserResponsavel = () => {
      return localStorage.getItem('user_nome') || 'Usuário Desconhecido';
  };

  // --- Busca de Dados (Edição) e Opções de Dropdown ---
  // MODIFICAÇÃO: Movida a lógica de 'fetchDataForForm' para DENTRO do useEffect
  useEffect(() => {
    // 1. Definir a função de busca
    const fetchDataForForm = async () => {
      setLoading(true);
      setError(null);
      setFormErrors({});
      let currentEquipeId = equipeIdFromUrl;

      // Se Editando: Buscar dados da encomenda
      if (isEditing) {
        try {
          const response = await api.get(`/encomendas/${encomendaId}/`);
          const data = response.data;
          setEncomendaData({
            cliente_id: data.cliente_id || '',
            data_encomenda: data.data_encomenda || new Date().toISOString().split('T')[0],
            responsavel_criacao: data.responsavel_criacao || '',
            status: data.status || 'criada',
            observacoes: data.observacoes || '',
            equipe_id: data.equipe_id || '',
          });
          setItems(data.itens?.map(item => ({
              id: item.id,
              produto_id: item.produto_id || null,
              fornecedor_id: item.fornecedor_id || null,
              preco_base: '', // Placeholder
              preco_cotado: item.preco_cotado !== null ? String(item.preco_cotado).replace('.',',') : '',
              observacoes: item.observacoes || '',
          })) || [{ ...initialItemState }]);
          currentEquipeId = data.equipe_id;
        } catch (err) {
          console.error("Erro ao buscar encomenda para edição:", err);
          setError("Falha ao carregar dados da encomenda para edição.");
          setLoading(false);
          return;
        }
      } else {
           // Se Criando: Preenche responsável
           setEncomendaData(prev => ({
               ...prev,
               responsavel_criacao: getCurrentUserResponsavel(),
               equipe_id: equipeIdFromUrl
           }));
           if (!equipeIdFromUrl) {
                setError("ID da Equipe não especificado para criar a encomenda.");
                setLoading(false);
                return;
           }
      }

       // Buscar Opções de Dropdowns (Clientes, Produtos, Fornecedores)
       if (currentEquipeId) {
           try {
               console.log(`Buscando opções para equipe ${currentEquipeId}`);
               const [clientesRes, produtosRes, fornecedoresRes] = await Promise.all([
                   api.get(`/clientes/?equipe__id=${currentEquipeId}&page_size=1000`),
                   api.get(`/produtos/?equipe__id=${currentEquipeId}&page_size=1000`),
                   api.get(`/fornecedores/?equipe__id=${currentEquipeId}&page_size=1000`),
               ]);

               // Formata Clientes (para <select> normal)
               const clienteOptionsFormatted = (clientesRes.data.results || clientesRes.data || [])
                   .map(c => ({ value: c.id ?? c.pk, label: `${c.codigo} - ${c.nome}` }))
                   .sort((a, b) => a.label.localeCompare(b.label));
               setClienteOptions([{ value: '', label: 'Selecione um Cliente...' }, ...clienteOptionsFormatted]);

               // Formata Produtos (para Autocomplete)
               const produtoOptionsFormatted = (produtosRes.data.results || produtosRes.data || [])
                   .map(p => ({ 
                       value: p.id ?? p.pk, 
                       label: `${p.codigo} - ${p.nome}`,
                       preco_base: p.preco_base // Armazena o preco_base
                   }))
                   .sort((a, b) => a.label.localeCompare(b.label));
               setProdutoOptions(produtoOptionsFormatted);

               // Formata Fornecedores (para Autocomplete)
               const fornecedorOptionsFormatted = (fornecedoresRes.data.results || fornecedoresRes.data || [])
                   .map(f => ({ value: f.id ?? f.pk, label: `${f.codigo} - ${f.nome}` }))
                   .sort((a, b) => a.label.localeCompare(b.label));
               setFornecedorOptions(fornecedorOptionsFormatted);

               // NOVO: Atualiza preco_base para itens existentes (Modo Edição)
               if (isEditing) {
                   const productMap = new Map(produtoOptionsFormatted.map(p => [p.value, p.preco_base]));
                   setItems(prevItems => 
                       prevItems.map(item => {
                           if (item.produto_id) {
                               const foundBasePrice = productMap.get(item.produto_id);
                               return {
                                   ...item,
                                   preco_base: foundBasePrice ? String(foundBasePrice).replace('.', ',') : '' 
                               };
                           }
                           return item;
                       })
                   );
               }

           } catch (fetchOptionsError) {
                console.error("Erro ao buscar opções para dropdowns:", fetchOptionsError);
                setError("Erro ao carregar opções de seleção. Verifique a API.");
                setClienteOptions([{ value: '', label: 'Erro ao carregar' }]);
                setProdutoOptions([]);
                setFornecedorOptions([]);
           }
       }
       setLoading(false);
    }; // Fim de fetchDataForForm

    // 2. Chamar a função
    fetchDataForForm();
    
  }, [encomendaId, isEditing, equipeIdFromUrl]); // Dependências do useEffect

  // --- Handlers ---
  const handleEncomendaChange = (e) => {
    const { name, value } = e.target;
    setEncomendaData(prev => ({ ...prev, [name]: value }));
  };

  // Handler para inputs normais dos ITENS
  const handleItemInputChange = (index, e) => {
     const { name, value } = e.target;
     const newItems = [...items];
     let processedValue = value;

     if (name === 'quantidade') {
         processedValue = parseInt(value, 10);
         if (isNaN(processedValue) || processedValue < 1) processedValue = 1;
     } else if (name === 'preco_cotado') {
         processedValue = value.replace(',', '.');
         if (!/^\d*\.?\d*$/.test(processedValue) && processedValue !== '') {
             console.warn("Valor inválido para preço:", value);
             return;
         }
     }
     newItems[index] = { ...newItems[index], [name]: processedValue };
     setItems(newItems);
  };

  // Handler para campos Autocomplete (Produto e Fornecedor)
  const handleItemAutocompleteChange = (index, name, newValue) => {
    const newItems = [...items];
    const currentItem = { ...newItems[index] };

    if (name === 'produto_id') {
        const basePrice = newValue ? newValue.preco_base : ''; // Pega o preco_base
        currentItem.produto_id = newValue ? newValue.value : null;
        // Define o preco_base (inalterável)
        currentItem.preco_base = basePrice ? String(basePrice).replace('.', ',') : '';
        // Define o preco_cotado (editável) como sugestão
        currentItem.preco_cotado = basePrice ? String(basePrice).replace('.', ',') : '';
    } else if (name === 'fornecedor_id') {
        currentItem.fornecedor_id = newValue ? newValue.value : null;
    }
    
    newItems[index] = currentItem;
    setItems(newItems);
  };

  const addItem = () => {
      setItems([...items, { ...initialItemState }]);
  };

  const removeItem = (index) => {
      if (items.length <= 1) return;
      const newItems = items.filter((_, i) => i !== index);
      setItems(newItems);
  };

  // --- Submit ---
  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setFormErrors({});

    if (!encomendaData.cliente_id) {
        setError("Selecione um cliente."); setIsSubmitting(false); return;
    }

    let itemValidationErrors = false;
    const validItemsData = items
        .map((item, index) => {
            const precoStr = item.preco_cotado.toString().replace(',', '.');
            const precoNum = parseFloat(precoStr);
            let currentItemErrors = {};

            if (!item.produto_id) currentItemErrors.produto_id = ['Selecione um produto.'];
            if (!item.fornecedor_id) currentItemErrors.fornecedor_id = ['Selecione um fornecedor.'];
            if (isNaN(precoNum) || precoNum <= 0) currentItemErrors.preco_cotado = ['Preço deve ser maior que zero.'];
            if (!item.quantidade || item.quantidade < 1) currentItemErrors.quantidade = ['Quantidade deve ser pelo menos 1.'];

            if (Object.keys(currentItemErrors).length > 0) {
                setFormErrors(prev => ({
                    ...prev,
                    itens: { ...(prev.itens || {}), [index]: currentItemErrors }
                }));
                itemValidationErrors = true;
                return null;
            }

            return {
                ...(item.id && { id: item.id }),
                produto_id: item.produto_id,
                fornecedor_id: item.fornecedor_id,
                quantidade: item.quantidade,
                preco_cotado: precoNum.toFixed(2),
                observacoes: item.observacoes,
            };
        })
        .filter(item => item !== null);

    if (itemValidationErrors) {
        setError("Erros de validação nos itens. Verifique os campos marcados.");
        setIsSubmitting(false);
        return;
    }
    if (validItemsData.length === 0) {
        setError("Adicione pelo menos um item válido com produto, fornecedor e preço positivo.");
        setIsSubmitting(false);
        return;
    }
    if(formErrors.itens) setFormErrors({});

    const payload = {
      cliente_id: encomendaData.cliente_id,
      data_encomenda: encomendaData.data_encomenda,
      responsavel_criacao: encomendaData.responsavel_criacao,
      status: encomendaData.status,
      observacoes: encomendaData.observacoes,
      itens: validItemsData,
      ...(!isEditing && !equipeIdFromUrl && encomendaData.equipe_id && { equipe_id: encomendaData.equipe_id }),
    };

    console.log("Submit Payload:", payload);

    try {
      let response;
      const apiUrl = isEditing ? `/encomendas/${encomendaId}/` : '/encomendas/';
      const method = isEditing ? 'put' : 'post';

      response = await api[method](apiUrl, payload);

      const resultEncomenda = response.data;
      alert(`Encomenda ${isEditing ? 'atualizada' : 'criada'} com sucesso! Número: #${resultEncomenda.numero_encomenda}`);
      navigate(`/encomendas/${resultEncomenda.numero_encomenda}`);

    } catch (err) {
      console.error("Erro ao salvar encomenda:", err.response || err);
      let generalError = "Ocorreu um erro ao salvar a encomenda.";

      if (err.response?.data && typeof err.response.data === 'object') {
           setFormErrors(err.response.data);
           const nonFieldErrors = err.response.data.non_field_errors || err.response.data.detail;
           let itemErrorsSummary = '';
            if (err.response.data.itens && Array.isArray(err.response.data.itens)) {
                err.response.data.itens.forEach((itemErr, index) => {
                    if (itemErr && typeof itemErr === 'object' && Object.keys(itemErr).length > 0) {
                        itemErrorsSummary += ` Item ${index + 1}: ${Object.values(itemErr).flat().join(' ')}.`;
                    } else if (typeof itemErr === 'string') {
                         itemErrorsSummary += ` Item ${index + 1}: ${itemErr}.`;
                    }
                });
            }
           generalError = nonFieldErrors || `Erro de validação.${itemErrorsSummary || ' Verifique os campos.'}`;
      } else if (err.response?.data?.detail) {
           generalError = err.response.data.detail;
      } else if (err.request) {
           generalError = "Erro de conexão ao salvar encomenda.";
      }
      setError(generalError);
      setIsSubmitting(false);
    }
  };

  // --- Render ---
  if (!token) return <Navigate to="/login" replace />;

  if (loading) {
    return <div style={{ padding: '20px' }}>Carregando dados do formulário...</div>;
  }
   if (error && !Object.keys(formErrors).length) {
        return (
            <div style={{ padding: '20px' }} className="alert alert-danger">
                Erro: {error} <br />
                <Link to={isEditing ? `/encomendas/${encomendaId}`: '/encomendas'} className="alert-link">
                   {isEditing ? 'Voltar para Detalhes' : 'Voltar para a Lista'}
                </Link>
            </div>
        );
   }
    if (!isEditing && !encomendaData.equipe_id) {
        return (
             <div style={{ padding: '20px' }} className="alert alert-danger">
                 Erro: ID da Equipe não especificado para criar a encomenda. <br />
                 <Link to="/equipes" className="alert-link">Selecione uma equipe primeiro.</Link>
             </div>
         );
    }

   const getFieldError = (fieldName) => {
       const keys = fieldName.split('.');
       let errorMessages = formErrors;
       try {
           for (const key of keys) {
               if (/^\d+$/.test(key)) {
                   const index = parseInt(key, 10);
                   if (errorMessages && Array.isArray(errorMessages) && errorMessages[index]) {
                       errorMessages = errorMessages[index];
                   } else {
                       return null;
                   }
               } else {
                   if (errorMessages && typeof errorMessages === 'object' && errorMessages[key]) {
                       errorMessages = errorMessages[key];
                   } else {
                       return null;
                   }
               }
           }
           if (Array.isArray(errorMessages) && errorMessages.length > 0) {
                const message = typeof errorMessages[0] === 'string' ? errorMessages[0] : JSON.stringify(errorMessages[0]);
                return <small className="text-danger d-block mt-1">{message}</small>;
           }
       } catch (e) {
            console.error("Error accessing form error:", fieldName, e);
       }
       return null;
   };

  return (
    <div>
      {/* Header */}
      <div className="page-header">
           <h1>
               <i className={`bi bi-${isEditing ? 'pencil-square' : 'clipboard-plus'} me-3`}></i>
               {isEditing ? `Editar Encomenda #${encomendaId}` : 'Nova Encomenda'}
            </h1>
            <p className="mb-0 text-muted">Preencha os dados da encomenda</p>
      </div>

      {/* General validation error message */}
      {error && <div className="alert alert-danger">{error}</div>}

      <form onSubmit={handleSubmit} noValidate>

        {/* --- Basic Information Section --- */}
        <div className="card form-section mb-4">
          <div className="card-header"><h5 className="mb-0">Informações Básicas</h5></div>
          <div className="card-body">
            <div className="row">
              {/* Client (ainda <select> normal) */}
              <div className="col-md-6 mb-3">
                <label htmlFor="cliente_id" className="form-label">Cliente *</label>
                <select
                  id="cliente_id" name="cliente_id" required
                  className={`form-select ${formErrors.cliente_id ? 'is-invalid' : ''}`}
                  value={encomendaData.cliente_id} onChange={handleEncomendaChange}
                >
                   {clienteOptions.map(opt => <option key={opt.value} value={opt.value} disabled={opt.value === ''}>{opt.label}</option>)}
                </select>
                {getFieldError('cliente_id')}
              </div>
              {/* Outros campos... */}
              <div className="col-md-3 mb-3">
                <label htmlFor="data_encomenda" className="form-label">Data *</label>
                <input type="date" id="data_encomenda" name="data_encomenda" required
                  className={`form-control ${formErrors.data_encomenda ? 'is-invalid' : ''}`}
                  value={encomendaData.data_encomenda} onChange={handleEncomendaChange} />
                {getFieldError('data_encomenda')}
              </div>
              <div className="col-md-3 mb-3">
                <label htmlFor="responsavel_criacao" className="form-label">Responsável *</label>
                <input type="text" id="responsavel_criacao" name="responsavel_criacao" required
                  className={`form-control ${formErrors.responsavel_criacao ? 'is-invalid' : ''}`}
                  value={encomendaData.responsavel_criacao} onChange={handleEncomendaChange} />
                 {getFieldError('responsavel_criacao')}
              </div>
              <div className="col-md-6 mb-3">
                 <label htmlFor="status" className="form-label">Status</label>
                 <select id="status" name="status" value={encomendaData.status} onChange={handleEncomendaChange}
                    className={`form-select ${formErrors.status ? 'is-invalid' : ''}`} >
                     {STATUS_CHOICES.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                 </select>
                 {getFieldError('status')}
              </div>
               <div className="col-12 mb-3">
                 <label htmlFor="observacoes" className="form-label">Observações</label>
                 <textarea id="observacoes" name="observacoes" rows="3"
                   className={`form-control ${formErrors.observacoes ? 'is-invalid' : ''}`}
                   value={encomendaData.observacoes} onChange={handleEncomendaChange}
                 ></textarea>
                 {getFieldError('observacoes')}
              </div>
            </div>
          </div>
        </div>

        {/* --- Order Items Section --- */}
        <div className="card form-section mb-4">
           <div className="card-header d-flex justify-content-between align-items-center">
                <h5 className="mb-0">Itens da Encomenda</h5>
                <button type="button" className="btn btn-success btn-sm" onClick={addItem}>
                    <i className="bi bi-plus-circle me-1"></i> Adicionar Item
                </button>
           </div>
           <div className="card-body">
                {getFieldError('itens') && typeof formErrors.itens === 'string' && <div className="alert alert-danger">{formErrors.itens}</div>}
                {getFieldError('non_field_errors') && <div className="alert alert-danger">{formErrors.non_field_errors[0]}</div>}

                {items.map((item, index) => (
                    <div key={item.id ?? `new-${index}`}
                         className={`item-form border rounded p-3 mb-3 position-relative ${formErrors.itens?.[index] ? 'border-danger bg-danger bg-opacity-10' : ''}`}>
                         {items.length > 1 && ( <button type="button" className="btn btn-danger btn-sm position-absolute top-0 end-0 m-2" style={{ zIndex: 1 }} title="Remover Item" onClick={() => removeItem(index)}><i className="bi bi-trash"></i></button> )}

                         {getFieldError(`itens.${index}.non_field_errors`) && <div className="alert alert-danger p-1 small mb-2">{formErrors.itens[index].non_field_errors[0]}</div>}

                         {/* ATUALIZADO Layout da Linha (col-md-3, 3, 1, 2, 3) */}
                         <div className="row g-2">
                            {/* --- Produto (Autocomplete) --- */}
                            <div className="col-md-3">
                                <label htmlFor={`item-${index}-produto_id`} className="form-label small mb-1">Produto *</label>
                                <Autocomplete
                                    id={`item-${index}-produto_id`}
                                    options={produtoOptions}
                                    getOptionLabel={(option) => option.label || ''}
                                    value={produtoOptions.find(opt => opt.value === item.produto_id) || null}
                                    onChange={(event, newValue) => handleItemAutocompleteChange(index, 'produto_id', newValue)}
                                    isOptionEqualToValue={(option, value) => option && value && option.value === value.value}
                                    size="small"
                                    sx={{ 
                                        "& .MuiInputBase-root": { backgroundColor: "var(--form-control-bg)", color: "var(--text-color)", borderRadius: '8px' },
                                        "& .MuiOutlinedInput-notchedOutline": { borderColor: "var(--form-control-border)" },
                                        "& .MuiSvgIcon-root": { color: "var(--text-muted-color)" },
                                        "& .Mui-focused .MuiOutlinedInput-notchedOutline": { borderColor: "var(--link-color)" },
                                        "& label.Mui-focused": { color: "var(--link-color)" },
                                        "&.Mui-focused .MuiSvgIcon-root": { color: "var(--link-color)" }
                                    }}
                                    renderInput={(params) => (
                                        <TextField
                                            {...params}
                                            placeholder="Pesquisar produto..."
                                            error={!!getFieldError(`itens.${index}.produto_id`)}
                                        />
                                    )}
                                />
                                {getFieldError(`itens.${index}.produto_id`)}
                            </div>

                            {/* --- Fornecedor (Autocomplete) --- */}
                             <div className="col-md-3">
                                <label htmlFor={`item-${index}-fornecedor_id`} className="form-label small mb-1">Fornecedor *</label>
                                <Autocomplete
                                    id={`item-${index}-fornecedor_id`}
                                    options={fornecedorOptions}
                                    getOptionLabel={(option) => option.label || ''}
                                    value={fornecedorOptions.find(opt => opt.value === item.fornecedor_id) || null}
                                    onChange={(event, newValue) => handleItemAutocompleteChange(index, 'fornecedor_id', newValue)}
                                    isOptionEqualToValue={(option, value) => option && value && option.value === value.value}
                                    size="small"
                                    sx={{ 
                                        "& .MuiInputBase-root": { backgroundColor: "var(--form-control-bg)", color: "var(--text-color)", borderRadius: '8px' },
                                        "& .MuiOutlinedInput-notchedOutline": { borderColor: "var(--form-control-border)" },
                                        "& .MuiSvgIcon-root": { color: "var(--text-muted-color)" },
                                        "& .Mui-focused .MuiOutlinedInput-notchedOutline": { borderColor: "var(--link-color)" },
                                        "& label.Mui-focused": { color: "var(--link-color)" },
                                        "&.Mui-focused .MuiSvgIcon-root": { color: "var(--link-color)" }
                                    }}
                                    renderInput={(params) => (
                                        <TextField
                                            {...params}
                                            placeholder="Pesquisar fornecedor..."
                                            error={!!getFieldError(`itens.${index}.fornecedor_id`)}
                                        />
                                    )}
                                />
                                {getFieldError(`itens.${index}.fornecedor_id`)}
                            </div>

                             {/* Quantidade (col-md-1) */}
                            <div className="col-md-1">
                                <label htmlFor={`item-${index}-quantidade`} className="form-label small mb-1">Qtd *</label>
                                <input type="number" id={`item-${index}-quantidade`} name="quantidade" required min="1" value={item.quantidade} onChange={(e) => handleItemInputChange(index, e)}
                                    className={`form-control form-control-sm ${getFieldError(`itens.${index}.quantidade`) ? 'is-invalid' : ''}`} />
                                {getFieldError(`itens.${index}.quantidade`)}
                            </div>
                            
                            {/* --- NOVO: Preço Base (col-md-2) --- */}
                            <div className="col-md-2">
                                <label htmlFor={`item-${index}-preco_base`} className="form-label small mb-1">Preço Base</label>
                                <div className="input-group input-group-sm">
                                    <span className="input-group-text">R$</span>
                                    <input 
                                        type="text" 
                                        id={`item-${index}-preco_base`} 
                                        name="preco_base"
                                        className="form-control"
                                        value={item.preco_base} // Vem do estado (já formatado com vírgula)
                                        readOnly 
                                        disabled
                                        style={{ backgroundColor: 'var(--form-control-bg)', opacity: 0.7 }}
                                    />
                                </div>
                            </div>
                            
                            {/* --- Preço Cotado (col-md-3) --- */}
                             <div className="col-md-3">
                                <label htmlFor={`item-${index}-preco_cotado`} className="form-label small mb-1">Preço Cotado *</label>
                                <div className="input-group input-group-sm">
                                    <span className="input-group-text">R$</span>
                                    <input type="text" id={`item-${index}-preco_cotado`} name="preco_cotado" required placeholder="0,00" inputMode="decimal"
                                        className={`form-control ${getFieldError(`itens.${index}.preco_cotado`) ? 'is-invalid' : ''}`}
                                        value={item.preco_cotado.toString().replace('.',',')} // Exibe com vírgula
                                        onChange={(e) => handleItemInputChange(index, e)} />
                                </div>
                                {getFieldError(`itens.${index}.preco_cotado`)}
                            </div>

                            {/* Observações do Item (col-12) */}
                            <div className="col-12 mt-2">
                                <label htmlFor={`item-${index}-observacoes`} className="form-label small mb-1">Observações (Item)</label>
                                <input type="text" id={`item-${index}-observacoes`} name="observacoes" placeholder="Opcional"
                                    className={`form-control form-control-sm ${getFieldError(`itens.${index}.observacoes`) ? 'is-invalid' : ''}`}
                                    value={item.observacoes} onChange={(e) => handleItemInputChange(index, e)} />
                                {getFieldError(`itens.${index}.observacoes`)}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>

        {/* --- Action Buttons --- */}
        <div className="d-flex justify-content-between mt-4 mb-5">
            <Link to={isEditing ? `/encomendas/${encomendaId}` : '/encomendas'} className="btn btn-secondary">
                <i className="bi bi-x-circle me-2"></i>Cancelar
            </Link>
            <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                {isSubmitting ? (
                    <><span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Salvando...</>
                ) : (
                    <><i className="bi bi-check-circle me-2"></i> {isEditing ? 'Atualizar' : 'Criar'} Encomenda</>
                )}
            </button>
        </div>

      </form>
    </div>
  );
}

export default EncomendaFormPage;

