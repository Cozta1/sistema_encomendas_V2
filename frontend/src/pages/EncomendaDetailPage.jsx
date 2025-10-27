import React, { useState, useEffect, useCallback } from 'react';
// Removido useNavigate, pois não está sendo usado nesta página específica
import { useParams, Link, Navigate } from 'react-router-dom';
import api from '../services/api';

// (Opcional) Importar componentes UI (Card, Button, Table, Badge, Dropdown, Spinner etc.)

// Constante para opções de status (pode vir da API ou ser definida aqui)
const STATUS_CHOICES = [
    { value: 'criada', label: 'Criada' },
    { value: 'cotacao', label: 'Em Cotação' },
    { value: 'aprovada', label: 'Aprovada' },
    { value: 'em_andamento', label: 'Em Andamento' },
    { value: 'pronta', label: 'Pronta para Entrega' },
    { value: 'entregue', label: 'Entregue' },
    { value: 'cancelada', label: 'Cancelada' },
];

function EncomendaDetailPage() {
  const { encomendaId } = useParams(); // Pega o ID da URL
  // const navigate = useNavigate(); // Removido
  const [encomenda, setEncomenda] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusUpdateLoading, setStatusUpdateLoading] = useState(false);
  const [statusUpdateError, setStatusUpdateError] = useState(null);
  const token = localStorage.getItem('accessToken'); // Verifica autenticação

  // Função para buscar dados da encomenda
  const fetchEncomenda = useCallback(async () => {
    setLoading(true);
    setError(null);
    setStatusUpdateError(null);
    try {
      const response = await api.get(`/encomendas/${encomendaId}/`);
      setEncomenda(response.data);
    } catch (err) {
      console.error(`Erro ao buscar encomenda ${encomendaId}:`, err);
      if (err.response && (err.response.status === 401 || err.response.status === 403 || err.response.status === 404)) {
        setError('Encomenda não encontrada ou acesso negado.');
      } else {
        setError('Falha ao carregar dados da encomenda.');
      }
    } finally {
      setLoading(false);
    }
  }, [encomendaId]);

  // Busca os dados ao montar ou quando o ID muda
  useEffect(() => {
    fetchEncomenda();
  }, [fetchEncomenda]);

  // Função para atualizar o status
  const handleStatusUpdate = async (newStatus) => {
    if (!encomenda || newStatus === encomenda.status) return;

    setStatusUpdateLoading(true);
    setStatusUpdateError(null);
    try {
      const response = await api.post(`/encomenda/${encomendaId}/status/`, { status: newStatus });
      setEncomenda(prev => ({ ...prev, status: response.data.status_code, status_display: response.data.status_display }));
      alert(response.data.message || 'Status atualizado com sucesso!');
    } catch (err) {
      console.error("Erro ao atualizar status:", err);
      const errorMsg = err.response?.data?.error || err.response?.data?.detail || 'Falha ao atualizar status.';
      setStatusUpdateError(errorMsg);
      alert(`Erro: ${errorMsg}`);
    } finally {
      setStatusUpdateLoading(false);
    }
  };

  // Função para gerar PDF
  const handleGeneratePdf = () => {
      const pdfUrl = `${api.defaults.baseURL}/encomendas/${encomendaId}/pdf/`;
      window.open(pdfUrl, '_blank');
  };

  // --- Renderização ---
  if (!token) {
    return <Navigate to="/login" replace />;
  }
   if (loading) {
     return <div style={{ padding: '20px' }}>Carregando detalhes da encomenda...</div>;
   }

   if (error) {
     return (
         <div style={{ padding: '20px' }} className="alert alert-danger">
             Erro: {error} <br />
             <Link to="/encomendas" className="alert-link">Voltar para a lista</Link>
         </div>
     );
   }

   if (!encomenda) {
     return (
         <div style={{ padding: '20px' }} className="alert alert-warning">
             Encomenda não encontrada. <br/>
             <Link to="/encomendas" className="alert-link">Voltar para a lista</Link>
         </div>
     );
   }


  // Funções de formatação
  const formatDate = (dateString) => dateString ? new Date(dateString).toLocaleDateString('pt-BR', { timeZone: 'UTC' }) : 'N/A';
  const formatDateTime = (dateString) => dateString ? new Date(dateString).toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo'}) : 'N/A';
  // const formatTime = (timeString) => { /* Removido pois não estava sendo usado */ };
  const valorRestante = (parseFloat(encomenda.valor_total || 0) - parseFloat(encomenda.entrega?.valor_pago_adiantamento || 0)).toFixed(2);

  // --- JSX Principal ---
  return (
    <div>
        {/* Cabeçalho */}
        <div className="page-header">
           <div className="d-flex justify-content-between align-items-center flex-wrap gap-2">
              <div>
                <h1><i className="bi bi-clipboard-data me-3"></i>Encomenda #{encomenda.numero_encomenda}</h1>
                <p className="mb-0 text-muted">{encomenda.cliente_nome} - {encomenda.equipe_nome}</p>
              </div>
              <div className="text-end">
                <span className={`status-badge status-${encomenda.status}`}>
                  {encomenda.status_display}
                </span>
                <div className="mt-2"><small>Criada em: {formatDateTime(encomenda.data_criacao)}</small></div>
                 <div className="mt-1"><small>Última Atualização: {formatDateTime(encomenda.updated_at)}</small></div>
              </div>
            </div>
        </div>

        {/* Botões de Ação */}
        <div className="card action-buttons mb-4" style={{ position: 'sticky', top: '70px', zIndex: 100 }}>
             <div className="card-body p-2">
                 <div className="d-flex flex-wrap gap-2 justify-content-between align-items-center">
                    {/* Botões Esquerda */}
                    <div className="d-flex flex-wrap gap-2">
                        <Link to="/encomendas" className="btn btn-secondary btn-sm"><i className="bi bi-arrow-left me-1"></i>Voltar</Link>
                        <Link to={`/encomendas/${encomenda.numero_encomenda}/editar`} className="btn btn-primary btn-sm"><i className="bi bi-pencil me-1"></i>Editar</Link>
                        {!encomenda.entrega ? (
                            <Link to={`/encomendas/${encomenda.numero_encomenda}/entrega/nova`} className="btn btn-success btn-sm"><i className="bi bi-truck me-1"></i>Programar Entrega</Link>
                        ) : (
                            <Link to={`/entregas/${encomenda.entrega.id}/editar`} className="btn btn-info btn-sm"><i className="bi bi-truck me-1"></i>Editar Entrega</Link>
                        )}
                    </div>
                    {/* Botões Direita */}
                    <div className="d-flex flex-wrap gap-2 align-items-center">
                         <button onClick={handleGeneratePdf} className="btn btn-outline-primary btn-sm"><i className="bi bi-file-pdf me-1"></i>PDF</button>
                         <div className="dropdown">
                            <button className="btn btn-warning btn-sm dropdown-toggle" type="button" data-bs-toggle="dropdown" disabled={statusUpdateLoading}>
                                {statusUpdateLoading ? <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> : <><i className="bi bi-arrow-repeat me-1"></i>Alterar Status</>}
                            </button>
                            <ul className="dropdown-menu dropdown-menu-end">
                                {STATUS_CHOICES.map(statusOpt => (
                                <li key={statusOpt.value}>
                                    <button
                                        className={`dropdown-item ${statusOpt.value === encomenda.status ? 'active disabled' : ''}`}
                                        onClick={() => handleStatusUpdate(statusOpt.value)}
                                        disabled={statusOpt.value === encomenda.status || statusUpdateLoading}
                                        type="button"
                                    >
                                        {statusOpt.label}
                                    </button>
                                </li>
                                ))}
                            </ul>
                        </div>
                        {statusUpdateError && <span className="text-danger small ms-2">{statusUpdateError}</span>}
                         {encomenda.entrega && !encomenda.entrega.data_realizada && (
                            <button onClick={() => {/* TODO: Chamar API /marcar-entregue/ */}} className="btn btn-success btn-sm" disabled><i className="bi bi-check-circle me-1"></i>Marcar Entregue</button>
                         )}
                         <Link to={`/encomendas/${encomenda.numero_encomenda}/excluir`} className="btn btn-outline-danger btn-sm"><i className="bi bi-trash me-1"></i>Excluir</Link>
                    </div>
                </div>
             </div>
        </div>

        {/* Card: Informações Gerais */}
        <div className="card mb-3">
             <div className="card-header"><h5 className="mb-0"><i className="bi bi-info-circle me-2"></i>Informações Gerais</h5></div>
             <div className="card-body">
                <div className="row">
                    <div className="col-md-4 mb-2"><p><strong>Número:</strong> #{encomenda.numero_encomenda}</p></div>
                    <div className="col-md-4 mb-2"><p><strong>Data Encomenda:</strong> {formatDate(encomenda.data_encomenda)}</p></div>
                    <div className="col-md-4 mb-2"><p><strong>Responsável:</strong> {encomenda.responsavel_criacao}</p></div>
                    <div className="col-md-4 mb-2"><p><strong>Equipe:</strong> {encomenda.equipe_nome}</p></div>
                    <div className="col-md-4 mb-2"><p><strong>Status:</strong> <span className={`status-badge status-${encomenda.status}`}>{encomenda.status_display}</span></p></div>
                     <div className="col-md-4 mb-2"><p><strong>Valor Total:</strong> R$ {parseFloat(encomenda.valor_total).toFixed(2)}</p></div>
                     <div className="col-12"><p><strong>Observações Gerais:</strong> {encomenda.observacoes || '-'}</p></div>
                </div>
             </div>
        </div>

        {/* Card: Cliente */}
        <div className="card mb-3">
             <div className="card-header"><h5 className="mb-0"><i className="bi bi-person me-2"></i>Cliente</h5></div>
             <div className="card-body">
                <p><strong>Nome:</strong> {encomenda.cliente_nome}</p>
                {/* Adicionar busca de detalhes do cliente aqui se necessário */}
             </div>
        </div>

        {/* Card: Itens */}
        <div className="card mb-3">
             <div className="card-header"><h5 className="mb-0"><i className="bi bi-box me-2"></i>Itens da Encomenda ({encomenda.itens?.length || 0})</h5></div>
             <div className="card-body p-0">
                 {encomenda.itens && encomenda.itens.length > 0 ? (
                    <div className="table-responsive">
                        <table className="table table-striped table-hover mb-0">
                           <thead>
                               <tr>
                                   <th>Produto</th>
                                   <th>Fornecedor</th>
                                   <th className="text-center">Qtd.</th>
                                   <th className="text-end">Preço Unit.</th>
                                   <th className="text-end">Total Item</th>
                                   <th>Obs.</th>
                               </tr>
                           </thead>
                           <tbody>
                               {encomenda.itens.map(item => (
                                   <tr key={item.id}>
                                       <td>{item.produto_nome}</td>
                                       <td>{item.fornecedor_nome}</td>
                                       <td className="text-center">{item.quantidade}</td>
                                       <td className="text-end">R$ {parseFloat(item.preco_cotado).toFixed(2)}</td>
                                       <td className="text-end">R$ {parseFloat(item.valor_total).toFixed(2)}</td>
                                       <td>{item.observacoes || '-'}</td>
                                   </tr>
                               ))}
                           </tbody>
                            <tfoot className="table-group-divider">
                               <tr className="fw-bold">
                                   <td colSpan="4" className="text-end border-0">Total Geral dos Itens:</td>
                                   <td className="text-end border-0">R$ {parseFloat(encomenda.valor_total).toFixed(2)}</td>
                                   <td className="border-0"></td>
                               </tr>
                           </tfoot>
                        </table>
                    </div>
                 ) : ( <p className="text-muted p-3 text-center">Nenhum item encontrado para esta encomenda.</p> )}
             </div>
        </div>

        {/* Card: Entrega */}
        {encomenda.entrega ? (
              <div className="card mb-3">
                 <div className="card-header"><h5 className="mb-0"><i className="bi bi-truck me-2"></i>Informações de Entrega</h5></div>
                 <div className="card-body">
                     <div className="row">
                        <div className="col-md-6 border-end mb-3 mb-md-0"> {/* Programação */}
                            <h6 className="text-primary mb-3">Programação</h6>
                            <p><strong>Data Prog.:</strong> {formatDate(encomenda.entrega.data_entrega)}</p>
                            <p><strong>Responsável Prog.:</strong> {encomenda.entrega.responsavel_entrega}</p>
                            <p><strong>Valor Adiant.:</strong> R$ {parseFloat(encomenda.entrega.valor_pago_adiantamento).toFixed(2)}</p>
                            <p><strong>Valor Restante:</strong> R$ {valorRestante}</p>
                            <p><strong>Obs. Entrega:</strong> {encomenda.entrega.observacoes_entrega || '-'}</p>
                         </div>
                         <div className="col-md-6"> {/* Realização */}
                             <h6 className="text-success mb-3">Realização</h6>
                             {encomenda.entrega.data_realizada ? (
                                <>
                                    <p><strong>Data/Hora Real.:</strong> {formatDateTime(encomenda.entrega.data_realizada)}</p>
                                    <p><strong>Entregue por:</strong> {encomenda.entrega.entregue_por || '-'}</p>
                                    <p><strong>Cliente Assinou:</strong> {encomenda.entrega.assinatura_cliente ? <span className="text-success fw-bold">Sim ✓</span> : <span className="text-danger fw-bold">Não ✗</span>}</p>
                                </>
                             ) : ( <p className="text-warning fst-italic">Entrega ainda não realizada.</p> )}
                        </div>
                    </div>
                 </div>
              </div>
            ) : (
               <div className="alert alert-info d-flex justify-content-between align-items-center">
                   Nenhuma informação de entrega programada para esta encomenda.
                   <Link to={`/encomendas/${encomenda.numero_encomenda}/entrega/nova`} className="btn btn-success btn-sm">
                       <i className="bi bi-truck me-1"></i>Programar Agora
                   </Link>
               </div>
            )}
    </div> // Fim div principal
  );
}

export default EncomendaDetailPage;

