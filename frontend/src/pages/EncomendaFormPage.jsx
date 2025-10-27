import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link, Navigate } from 'react-router-dom';
import api from '../services/api';

// (Optional) Import UI components (TextField, Button, Select, MenuItem, Box, Grid, IconButton, Autocomplete etc.)

// Initial structure for an empty item
const initialItemState = {
    // id: null, // For existing items (added if editing)
    produto_id: '',
    fornecedor_id: '',
    quantidade: 1,
    preco_cotado: '', // Use string to handle comma/dot input
    observacoes: '',
};

// Status choices (could come from API)
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
  const { encomendaId, equipeId: equipeIdFromUrl } = useParams(); // Get IDs from URL
  const navigate = useNavigate();
  const isEditing = Boolean(encomendaId); // Determine if editing
  const token = localStorage.getItem('accessToken');

  // State for main order data
  const [encomendaData, setEncomendaData] = useState({
    cliente_id: '',
    data_encomenda: new Date().toISOString().split('T')[0], // Default to today
    responsavel_criacao: '', // Fill with logged-in user?
    status: 'criada',
    observacoes: '',
    equipe_id: equipeIdFromUrl || '', // Get from URL if creating, will be filled if editing
  });

  // State for the list of items
  const [items, setItems] = useState([{ ...initialItemState }]); // Ensure one initial item

  // State for dropdown options
  const [clienteOptions, setClienteOptions] = useState([{ value: '', label: 'Carregando...' }]);
  const [produtoOptions, setProdutoOptions] = useState([{ value: '', label: 'Carregando...' }]);
  const [fornecedorOptions, setFornecedorOptions] = useState([{ value: '', label: 'Carregando...' }]);

  // Control states
  const [loading, setLoading] = useState(true); // Start loading (for edit or options)
  const [error, setError] = useState(null);
  const [formErrors, setFormErrors] = useState({}); // For API validation errors
  const [isSubmitting, setIsSubmitting] = useState(false);

  // --- Helper Functions ---
  const getCurrentUserResponsavel = () => {
      // Simulation - Ideally fetch from backend or global state/context
      return localStorage.getItem('user_nome') || 'Usuário Desconhecido';
  };

  // --- Data Fetching (Edit Mode) & Dropdown Options ---
  useEffect(() => {
    const fetchDataForForm = async () => {
      setLoading(true); // Ensure loading at the start
      setError(null);
      setFormErrors({}); // Clear previous validation errors
      let currentEquipeId = equipeIdFromUrl;

      // If Editing: Fetch existing order data
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
            equipe_id: data.equipe_id || '', // Get equipe_id from the order
          });
          // Populate items (format for local state if needed)
          setItems(data.itens?.map(item => ({
              id: item.id, // Important for update
              produto_id: item.produto_id || '',
              fornecedor_id: item.fornecedor_id || '',
              quantidade: item.quantidade || 1,
              // Ensure preco_cotado is string and use comma for display
              preco_cotado: item.preco_cotado !== null ? String(item.preco_cotado).replace('.',',') : '',
              observacoes: item.observacoes || '',
          })) || [{ ...initialItemState }]); // Ensure at least one item

          currentEquipeId = data.equipe_id; // Set equipeId based on the fetched order

        } catch (err) {
          console.error("Erro ao buscar encomenda para edição:", err);
          setError("Falha ao carregar dados da encomenda para edição.");
          setLoading(false);
          return; // Stop if order data cannot be loaded
        }
        // Edit mode loading finishes here, but option fetching continues
      } else {
           // If Creating: Fill responsible person and ensure equipeId
           setEncomendaData(prev => ({
               ...prev,
               responsavel_criacao: getCurrentUserResponsavel(),
               equipe_id: equipeIdFromUrl
           }));
           if (!equipeIdFromUrl) {
                setError("ID da Equipe não especificado para criar a encomenda.");
                setLoading(false); // Stop if no team context for creation
                return;
           }
      }

       // Fetch Dropdown Options - Filtered by Team
       if (currentEquipeId) {
           try {
               console.log(`Buscando opções para equipe ${currentEquipeId}`);
               // Use Promise.all to fetch all options in parallel
               const [clientesRes, produtosRes, fornecedoresRes] = await Promise.all([
                   // Fetch clients for the team (add large page_size or remove pagination in API if needed)
                   api.get(`/clientes/?equipe__id=${currentEquipeId}&page_size=1000`), // Ex: High limit
                   // Fetch products for the team
                   api.get(`/produtos/?equipe__id=${currentEquipeId}&page_size=1000`),
                   // Fetch suppliers for the team
                   api.get(`/fornecedores/?equipe__id=${currentEquipeId}&page_size=1000`),
               ]);

               // Format Clients for select: { value: id, label: text }
               const clienteOptionsFormatted = (clientesRes.data.results || clientesRes.data || [])
                   .map(c => ({ value: c.id ?? c.pk, label: `${c.codigo} - ${c.nome}` })) // Use id or pk
                   .sort((a, b) => a.label.localeCompare(b.label)); // Sort alphabetically
               setClienteOptions([{ value: '', label: 'Selecione um Cliente...' }, ...clienteOptionsFormatted]);

               // Format Products
               const produtoOptionsFormatted = (produtosRes.data.results || produtosRes.data || [])
                   .map(p => ({ value: p.id ?? p.pk, label: `${p.codigo} - ${p.nome}` }))
                   .sort((a, b) => a.label.localeCompare(b.label));
               setProdutoOptions([{ value: '', label: 'Selecione um Produto...' }, ...produtoOptionsFormatted]);

               // Format Suppliers
               const fornecedorOptionsFormatted = (fornecedoresRes.data.results || fornecedoresRes.data || [])
                   .map(f => ({ value: f.id ?? f.pk, label: `${f.codigo} - ${f.nome}` }))
                   .sort((a, b) => a.label.localeCompare(b.label));
               setFornecedorOptions([{ value: '', label: 'Selecione um Fornecedor...' }, ...fornecedorOptionsFormatted]);

               console.log("Opções de dropdown carregadas.");

           } catch (fetchOptionsError) {
                console.error("Erro ao buscar opções para dropdowns:", fetchOptionsError);
                setError("Erro ao carregar opções de seleção (Cliente/Produto/Fornecedor). Verifique a API.");
                // Set options to error state
                setClienteOptions([{ value: '', label: 'Erro ao carregar' }]);
                setProdutoOptions([{ value: '', label: 'Erro ao carregar' }]);
                setFornecedorOptions([{ value: '', label: 'Erro ao carregar' }]);
           }
       }
       // Finalize general loading here, after fetching order (if editing) AND options
       setLoading(false);

    }; // End of fetchDataForForm

    useEffect(() => {
      fetchDataForForm();
    }, [encomendaId, isEditing, equipeIdFromUrl]); // Dependencies for initial fetch

  // --- Handlers ---
  const handleEncomendaChange = (e) => {
    const { name, value } = e.target;
    setEncomendaData(prev => ({ ...prev, [name]: value }));
  };

  const handleItemChange = (index, e) => {
     const { name, value } = e.target;
     const newItems = [...items];
     let processedValue = value;

     if (name === 'quantidade') {
         processedValue = parseInt(value, 10);
         // Ensure it's a number >= 1
         if (isNaN(processedValue) || processedValue < 1) {
             processedValue = 1;
         }
     } else if (name === 'preco_cotado') {
         // Allow comma or dot during input, store internally consistently (e.g., with dot)
         processedValue = value.replace(',', '.');
         // Allow empty string, a single dot, or numbers (int or float)
         if (!/^\d*\.?\d*$/.test(processedValue) && processedValue !== '') {
             // If input is invalid (e.g., letters), prevent update
             console.warn("Valor inválido para preço:", value);
             return; // Stop state update for this field
         }
         // Keep the processed value (with dot) in the state
     }

     newItems[index] = { ...newItems[index], [name]: processedValue };
     setItems(newItems);
  };

  const addItem = () => {
      setItems([...items, { ...initialItemState }]); // Add a new empty item
  };

  const removeItem = (index) => {
      if (items.length <= 1) return; // Don't remove the last item
      // Removal logic works with the current serializer (omitted items are deleted on PUT)
      const newItems = items.filter((_, i) => i !== index);
      setItems(newItems);
  };

  // --- Submit ---
  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setFormErrors({});

    // Frontend Validations
    if (!encomendaData.cliente_id) {
        setError("Selecione um cliente."); setIsSubmitting(false); return;
    }

    let itemValidationErrors = false;
    const validItemsData = items
        .map((item, index) => {
            const precoStr = item.preco_cotado.toString().replace(',', '.'); // Ensure dot for parsing
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
                return null; // Invalid item
            }

            return {
                ...(item.id && { id: item.id }), // Include ID if it's an existing item
                produto_id: item.produto_id,
                fornecedor_id: item.fornecedor_id,
                quantidade: item.quantidade,
                preco_cotado: precoNum.toFixed(2), // Final format for API (string with 2 decimals)
                observacoes: item.observacoes,
            };
        })
        .filter(item => item !== null); // Remove null entries (invalid items)

    if (itemValidationErrors) {
        setError("Erros de validação nos itens. Verifique os campos marcados.");
        setIsSubmitting(false);
        return;
    }

    if (validItemsData.length === 0) {
        // This case might be redundant if the item validation above works, but keep as safety
        setError("Adicione pelo menos um item válido com produto, fornecedor e preço positivo.");
        setIsSubmitting(false);
        return;
    }

    const payload = {
      cliente_id: encomendaData.cliente_id,
      data_encomenda: encomendaData.data_encomenda,
      responsavel_criacao: encomendaData.responsavel_criacao,
      status: encomendaData.status,
      observacoes: encomendaData.observacoes,
      itens: validItemsData,
      // equipe_id is needed for creation ONLY if not using nested URL (e.g., POST /api/encomendas/)
      // If using POST /api/equipes/ID/encomendas/, the backend gets it from URL
      ...(!isEditing && !equipeIdFromUrl && encomendaData.equipe_id && { equipe_id: encomendaData.equipe_id }),
    };

    console.log("Submit Payload:", payload); // For debugging

    try {
      let response;
      const apiUrl = isEditing ? `/encomendas/${encomendaId}/` : '/encomendas/';
      const method = isEditing ? 'put' : 'post';

      response = await api[method](apiUrl, payload);

      // --- Success ---
      const resultEncomenda = response.data;
      alert(`Encomenda ${isEditing ? 'atualizada' : 'criada'} com sucesso! Número: #${resultEncomenda.numero_encomenda}`);
      // Redirect to the detail page of the created/updated order
      navigate(`/encomendas/${resultEncomenda.numero_encomenda}`);
      // No need to setIsSubmitting(false) here because we are navigating away

    } catch (err) {
      // --- Error Handling ---
      console.error("Erro ao salvar encomenda:", err.response || err);
      let generalError = "Ocorreu um erro ao salvar a encomenda."; // Default error

      if (err.response?.data && typeof err.response.data === 'object') {
           // If API returns validation errors
           setFormErrors(err.response.data);
           const nonFieldErrors = err.response.data.non_field_errors || err.response.data.detail;
           // Extract item-specific errors for a clearer general message
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
           generalError = nonFieldErrors || `Erro de validação.${itemErrorsSummary || ' Verifique os campos marcados.'}`;
      } else if (err.response?.data?.detail) {
           // If API returns just a detail message
           generalError = err.response.data.detail;
      } else if (err.request) {
           // Network error
           generalError = "Erro de conexão ao salvar encomenda.";
      }
      setError(generalError);
      setIsSubmitting(false); // Re-enable button on error
    }
  };

  // --- Render ---
  if (!token) return <Navigate to="/login" replace />; // Protect route

  if (loading) {
    return <div style={{ padding: '20px' }}>Carregando dados do formulário...</div>;
  }
   // General error (not form validation)
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
    // Error: Missing team ID during creation
    if (!isEditing && !encomendaData.equipe_id) {
        return (
             <div style={{ padding: '20px' }} className="alert alert-danger">
                 Erro: ID da Equipe não especificado para criar a encomenda. <br />
                 <Link to="/equipes" className="alert-link">Selecione uma equipe primeiro.</Link>
             </div>
         );
    }

   // Helper function for field errors (handles nested item errors)
   const getFieldError = (fieldName) => {
       const keys = fieldName.split('.'); // e.g., 'itens.0.produto_id'
       let errorMessages = formErrors;
       try { // Use try-catch for safety when accessing nested properties
           for (const key of keys) {
               if (/^\d+$/.test(key)) { // Check if key is an index number
                   const index = parseInt(key, 10);
                   if (errorMessages && Array.isArray(errorMessages) && errorMessages[index]) {
                       errorMessages = errorMessages[index];
                   } else {
                       return null; // Index out of bounds or not an array
                   }
               } else {
                   if (errorMessages && typeof errorMessages === 'object' && errorMessages[key]) {
                       errorMessages = errorMessages[key];
                   } else {
                       return null; // Key not found
                   }
               }
           }
           // errorMessages should now be the array of errors for the specific field
           if (Array.isArray(errorMessages) && errorMessages.length > 0) {
                // Ensure message is a string before rendering
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
               {/* TODO: Fetch and display team name based on encomendaData.equipe_id */}
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
              {/* Client */}
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
              {/* Order Date */}
              <div className="col-md-3 mb-3">
                <label htmlFor="data_encomenda" className="form-label">Data *</label>
                <input type="date" id="data_encomenda" name="data_encomenda" required
                  className={`form-control ${formErrors.data_encomenda ? 'is-invalid' : ''}`}
                  value={encomendaData.data_encomenda} onChange={handleEncomendaChange} />
                {getFieldError('data_encomenda')}
              </div>
               {/* Responsible Person */}
              <div className="col-md-3 mb-3">
                <label htmlFor="responsavel_criacao" className="form-label">Responsável *</label>
                <input type="text" id="responsavel_criacao" name="responsavel_criacao" required
                  className={`form-control ${formErrors.responsavel_criacao ? 'is-invalid' : ''}`}
                  value={encomendaData.responsavel_criacao} onChange={handleEncomendaChange} />
                 {getFieldError('responsavel_criacao')}
              </div>
              {/* Status */}
              <div className="col-md-6 mb-3">
                 <label htmlFor="status" className="form-label">Status</label>
                 <select id="status" name="status" value={encomendaData.status} onChange={handleEncomendaChange}
                    className={`form-select ${formErrors.status ? 'is-invalid' : ''}`} >
                     {STATUS_CHOICES.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                 </select>
                 {getFieldError('status')}
              </div>
              {/* Observations */}
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
                {/* General errors related to the 'itens' array itself */}
                {getFieldError('itens') && typeof formErrors.itens === 'string' && <div className="alert alert-danger">{formErrors.itens}</div>}
                {getFieldError('non_field_errors') && <div className="alert alert-danger">{formErrors.non_field_errors[0]}</div>}

                {items.map((item, index) => (
                    <div key={item.id ?? `new-${index}`} // Use existing ID or index for new items
                         className={`item-form border rounded p-3 mb-3 position-relative ${formErrors.itens?.[index] ? 'border-danger bg-danger bg-opacity-10' : ''}`}>
                         {items.length > 1 && ( <button type="button" className="btn btn-danger btn-sm position-absolute top-0 end-0 m-2" style={{ zIndex: 1 }} title="Remover Item" onClick={() => removeItem(index)}><i className="bi bi-trash"></i></button> )}

                         {/* Display non_field_errors specific to this item */}
                         {getFieldError(`itens.${index}.non_field_errors`) && <div className="alert alert-danger p-1 small mb-2">{formErrors.itens[index].non_field_errors[0]}</div>}

                         <div className="row g-2">
                            {/* Product */}
                            <div className="col-md-4">
                                <label htmlFor={`item-${index}-produto_id`} className="form-label small mb-1">Produto *</label>
                                <select id={`item-${index}-produto_id`} name="produto_id" required value={item.produto_id} onChange={(e) => handleItemChange(index, e)}
                                    className={`form-select form-select-sm ${formErrors.itens?.[index]?.produto_id ? 'is-invalid' : ''}`} >
                                     {produtoOptions.map(opt => <option key={opt.value} value={opt.value} disabled={opt.value === ''}>{opt.label}</option>)}
                                </select>
                                {getFieldError(`itens.${index}.produto_id`)}
                            </div>
                            {/* Supplier */}
                             <div className="col-md-4">
                                <label htmlFor={`item-${index}-fornecedor_id`} className="form-label small mb-1">Fornecedor *</label>
                                <select id={`item-${index}-fornecedor_id`} name="fornecedor_id" required value={item.fornecedor_id} onChange={(e) => handleItemChange(index, e)}
                                    className={`form-select form-select-sm ${formErrors.itens?.[index]?.fornecedor_id ? 'is-invalid' : ''}`} >
                                     {fornecedorOptions.map(opt => <option key={opt.value} value={opt.value} disabled={opt.value === ''}>{opt.label}</option>)}
                                </select>
                                {getFieldError(`itens.${index}.fornecedor_id`)}
                            </div>
                             {/* Quantity */}
                            <div className="col-md-1">
                                <label htmlFor={`item-${index}-quantidade`} className="form-label small mb-1">Qtd *</label>
                                <input type="number" id={`item-${index}-quantidade`} name="quantidade" required min="1" value={item.quantidade} onChange={(e) => handleItemChange(index, e)}
                                    className={`form-control form-control-sm ${formErrors.itens?.[index]?.quantidade ? 'is-invalid' : ''}`} />
                                {getFieldError(`itens.${index}.quantidade`)}
                            </div>
                            {/* Quoted Price */}
                             <div className="col-md-3">
                                <label htmlFor={`item-${index}-preco_cotado`} className="form-label small mb-1">Preço Unit. *</label>
                                <div className="input-group input-group-sm">
                                    <span className="input-group-text">R$</span>
                                    <input type="text" id={`item-${index}-preco_cotado`} name="preco_cotado" required placeholder="0,00" inputMode="decimal"
                                        className={`form-control ${formErrors.itens?.[index]?.preco_cotado ? 'is-invalid' : ''}`}
                                        value={item.preco_cotado} // State handles comma/dot display
                                        onChange={(e) => handleItemChange(index, e)} />
                                </div>
                                {getFieldError(`itens.${index}.preco_cotado`)}
                            </div>
                            {/* Item Observations */}
                            <div className="col-12 mt-2">
                                <label htmlFor={`item-${index}-observacoes`} className="form-label small mb-1">Observações (Item)</label>
                                <input type="text" id={`item-${index}-observacoes`} name="observacoes" placeholder="Opcional"
                                    className={`form-control form-control-sm ${formErrors.itens?.[index]?.observacoes ? 'is-invalid' : ''}`}
                                    value={item.observacoes} onChange={(e) => handleItemChange(index, e)} />
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

