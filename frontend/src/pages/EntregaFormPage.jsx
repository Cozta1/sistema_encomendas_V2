import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api from '../services/api';

// Função utilitária para formatar data ISO para o input datetime-local
// (Ex: "2024-01-01T10:00:00Z" -> "2024-01-01T07:00")
const formatISOToLocalInput = (isoDate) => {
  if (!isoDate) return '';
  // Cria um objeto Date, que usa o fuso horário local
  const date = new Date(isoDate);
  // Ajusta para o fuso local e remove segundos/milissegundos
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
  return date.toISOString().slice(0, 16);
};

// Função utilitária para formatar a data local para ISO (UTC)
const formatLocalInputToISO = (localDate) => {
    if (!localDate) return null;
    const date = new Date(localDate);
    // Converte de volta para ISO string (UTC)
    return date.toISOString();
}


function EntregaFormPage() {
  // Se 'entregaId' existir, estamos editando.
  // Se 'encomendaId' existir (sem 'entregaId'), estamos criando.
  const { encomendaId, entregaId } = useParams();
  const navigate = useNavigate();
  const isEditing = Boolean(entregaId);

  // Estados do formulário
  const [formData, setFormData] = useState({
    data_entrega: formatISOToLocalInput(new Date().toISOString()), // Padrão: agora
    status_entrega: 'AGENDADA',
    recebido_por: '',
    observacoes: '',
  });

  // Estados de controle
  const [loading, setLoading] = useState(isEditing); // Só carrega se estiver editando
  const [error, setError] = useState(null);
  const [formErrors, setFormErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Guarda o ID da encomenda (necessário para navegar de volta)
  const [encomendaIdAssociada, setEncomendaIdAssociada] = useState(encomendaId);
  const [encomendaNumero, setEncomendaNumero] = useState(''); // Para o título

  // Busca dados da Entrega (se editando) ou da Encomenda (se criando)
  useEffect(() => {
    const fetchData = async () => {
      setError(null);
      try {
        if (isEditing) {
          // Modo Edição: Busca dados da entrega existente
          setLoading(true);
          const response = await api.get(`/api/entregas/${entregaId}/`);
          const entrega = response.data;
          
          setFormData({
            data_entrega: formatISOToLocalInput(entrega.data_entrega),
            status_entrega: entrega.status_entrega || 'AGENDADA',
            recebido_por: entrega.recebido_por || '',
            observacoes: entrega.observacoes || '',
          });
          // Guarda o ID e número da encomenda-pai
          setEncomendaIdAssociada(entrega.encomenda_id);
          setEncomendaNumero(entrega.encomenda_numero || '');
          
        } else if (encomendaId) {
          // Modo Criação: Apenas busca o número da encomenda para o título
          setLoading(true); // Usamos o loading para buscar o num da encomenda
          const response = await api.get(`/api/encomendas/${encomendaId}/`);
          setEncomendaNumero(response.data.numero_encomenda || '');
        }
      } catch (err) {
        console.error("Erro ao carregar dados:", err);
        setError("Falha ao carregar dados. Verifique se a encomenda ou entrega existe.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [entregaId, encomendaId, isEditing]);

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

    // Prepara o payload para a API
    const payload = {
      ...formData,
      // Converte a data local do input de volta para o formato ISO (UTC)
      data_entrega: formatLocalInputToISO(formData.data_entrega), 
      encomenda: encomendaIdAssociada, // Associa à encomenda
    };
    
    // Remove o ID da encomenda-pai se estava no payload de criação
    if (!isEditing) {
        payload.encomenda = encomendaId; // Garante que está no payload de criação
    }

    try {
      if (isEditing) {
        // Requisição PUT para atualizar
        await api.put(`/api/entregas/${entregaId}/`, payload);
      } else {
        // Requisição POST para criar
        await api.post('/api/entregas/', payload);
      }
      
      alert(`Agendamento ${isEditing ? 'atualizado' : 'criado'} com sucesso!`);
      // Redireciona de volta para os detalhes da encomenda
      navigate(`/encomendas/${encomendaIdAssociada}`);

    } catch (err) {
      console.error("Erro ao salvar agendamento:", err.response || err);
      if (err.response?.data && typeof err.response.data === 'object') {
           setFormErrors(err.response.data);
           const nonFieldErrors = err.response.data.non_field_errors || err.response.data.detail;
           setError(nonFieldErrors || "Erro de validação. Verifique os campos marcados.");
      } else {
           setError(err.response?.data?.detail || `Erro ${err.response?.status || ''} ao salvar.`);
      }
    } finally {
      setIsSubmitting(false);
    }
  };
  
  // Funções Auxiliares de Renderização
  const getFieldError = (fieldName) => {
     if (formErrors && formErrors[fieldName]) {
         return <small className="text-danger d-block mt-1">{formErrors[fieldName][0]}</small>;
     }
     return null;
  };

  // Opções de Status (baseado no models.py)
  const statusOptions = [
      { value: 'AGENDADA', label: 'Agendada' },
      { value: 'REALIZADA', label: 'Realizada' },
      { value: 'PROBLEMA', label: 'Problema na Entrega' },
  ];

  // --- Renderização ---
  if (loading) {
    return <div style={{ padding: '20px' }}>Carregando dados do formulário...</div>;
  }

  if (error) {
     return (
         <div style={{ padding: '20px' }} className="alert alert-danger">
             Erro: {error} <br />
             <Link to={encomendaIdAssociada ? `/encomendas/${encomendaIdAssociada}` : '/encomendas'} className="alert-link">
                 Voltar
             </Link>
         </div>
     );
  }

  return (
    <div>
      {/* Cabeçalho */}
      <div className="page-header">
           <h1>
               <i className={`bi bi-${isEditing ? 'pencil-square' : 'calendar-plus'} me-3`}></i>
               {isEditing ? `Editar Agendamento` : 'Novo Agendamento'}
            </h1>
            <p className="mb-0 text-muted">
              {encomendaNumero ? `Para a Encomenda #${encomendaNumero}` : 'Agendamento de entrega'}
            </p>
      </div>

      {/* Exibe erro geral de validação */}
      {error && <div className="alert alert-danger">{error}</div>}

      <form onSubmit={handleSubmit} noValidate>
        <div className="card form-section mb-4">
          <div className="card-header"><h5 className="mb-0">Detalhes da Entrega</h5></div>
          <div className="card-body">
            <div className="row">
              {/* Data/Hora */}
              <div className="col-md-6 mb-3">
                <label htmlFor="data_entrega" className="form-label">Data e Hora da Entrega *</label>
                <input
                  type="datetime-local"
                  id="data_entrega"
                  name="data_entrega"
                  className={`form-control ${getFieldError('data_entrega') ? 'is-invalid' : ''}`}
                  value={formData.data_entrega}
                  onChange={handleChange}
                  required
                  disabled={isSubmitting}
                />
                {getFieldError('data_entrega')}
              </div>
              {/* Status */}
              <div className="col-md-6 mb-3">
                <label htmlFor="status_entrega" className="form-label">Status *</label>
                <select
                    id="status_entrega"
                    name="status_entrega"
                    className={`form-select ${getFieldError('status_entrega') ? 'is-invalid' : ''}`}
                    value={formData.status_entrega}
                    onChange={handleChange}
                    disabled={isSubmitting}
                >
                    {statusOptions.map(opt => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                </select>
                {getFieldError('status_entrega')}
              </div>
            </div>

            {/* Recebido Por */}
            <div className="col-12 mb-3">
              <label htmlFor="recebido_por" className="form-label">Recebido Por</label>
              <input
                type="text"
                id="recebido_por"
                name="recebido_por"
                className={`form-control ${getFieldError('recebido_por') ? 'is-invalid' : ''}`}
                value={formData.recebido_por}
                onChange={handleChange}
                placeholder="Nome de quem recebeu (se status 'Realizada')"
                disabled={isSubmitting}
              />
              {getFieldError('recebido_por')}
            </div>
            
            {/* Observações */}
            <div className="col-12 mb-3">
              <label htmlFor="observacoes" className="form-label">Observações</label>
              <textarea
                id="observacoes"
                name="observacoes"
                rows="3"
                className={`form-control ${getFieldError('observacoes') ? 'is-invalid' : ''}`}
                value={formData.observacoes}
                onChange={handleChange}
                placeholder="Detalhes sobre a entrega, ou motivo do 'Problema'"
                disabled={isSubmitting}
              ></textarea>
              {getFieldError('observacoes')}
            </div>
          </div>
        </div>

        {/* --- Botões de Ação --- */}
        <div className="d-flex justify-content-between mt-4 mb-5">
            <Link to={`/encomendas/${encomendaIdAssociada}`} className="btn btn-secondary">
                <i className="bi bi-x-circle me-2"></i>Cancelar
            </Link>
            <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                {isSubmitting ? (
                    <><span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Salvando...</>
                ) : (
                    <><i className="bi bi-check-circle me-2"></i> {isEditing ? 'Atualizar' : 'Salvar'} Agendamento</>
                )}
            </button>
        </div>

      </form>
    </div>
  );
}

export default EntregaFormPage;