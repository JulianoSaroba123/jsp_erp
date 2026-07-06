import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getProposals,
  deleteProposal,
  changeProposalStatus,
  convertProposalToOS,
  ProposalSummary,
  getProposalStatusLabel,
  getProposalStatusColor,
  getProposalStatusIcon,
  formatCurrency,
  formatDate,
} from '../api/proposals';
import { usePermissions } from '../auth/usePermissions';
import { LoadingState, ErrorState, EmptyState } from '../components/ui/State';
import { useNavigate } from 'react-router-dom';

export function Proposals() {
  const [page, setPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [showConvertModal, setShowConvertModal] = useState<ProposalSummary | null>(null);
  const pageSize = 15;
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { canCreate, canUpdate, canDelete } = usePermissions();

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['proposals', page, searchTerm, filterStatus],
    queryFn: () =>
      getProposals({
        page,
        page_size: pageSize,
        search: searchTerm || undefined,
        status: filterStatus || undefined,
      }),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteProposal,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposals'] });
      alert('Proposta excluída com sucesso!');
    },
    onError: (error: any) => {
      const status = error.response?.status;
      if (status === 404) {
        alert('Proposta não encontrada ou já foi excluída');
      } else if (status === 403) {
        alert('Você não tem permissão para excluir esta proposta');
      } else {
        alert(error.response?.data?.detail || 'Erro ao excluir proposta');
      }
    },
  });

  const statusMutation = useMutation({
    mutationFn: ({ id, new_status }: { id: string; new_status: string }) =>
      changeProposalStatus(id, new_status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposals'] });
      alert('Status atualizado com sucesso!');
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Erro ao alterar status');
    },
  });

  const convertMutation = useMutation({
    mutationFn: ({ id }: { id: string }) =>
      convertProposalToOS(id, {}),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['proposals'] });
      queryClient.invalidateQueries({ queryKey: ['service-orders'] });
      setShowConvertModal(null);
      alert(
        `✅ ${response.message}\n\n` +
        `OS Gerada: ${response.service_order_number}\n` +
        `Proposta: ${response.proposal_number}`
      );
      // Redirecionar para a OS criada
      navigate('/service-orders');
    },
    onError: (error: any) => {
      const status = error.response?.status;
      const detail = error.response?.data?.detail || 'Erro ao converter proposta';
      
      if (status === 400) {
        alert(`❌ Conversão Bloqueada:\n\n${detail}\n\nApenas propostas APROVADAS podem ser convertidas.`);
      } else if (status === 409) {
        alert(`⚠️ Duplicidade Detectada:\n\n${detail}\n\nEsta proposta já possui uma Ordem de Serviço gerada.`);
      } else if (status === 404) {
        alert('Proposta não encontrada');
      } else {
        alert(`Erro ao converter: ${detail}`);
      }
    },
  });

  const handleDelete = (proposal: ProposalSummary) => {
    const confirmed = window.confirm(
      `Tem certeza que deseja excluir a proposta ${proposal.number} - "${proposal.title}"?\n\nEsta ação não pode ser desfeita.`
    );
    if (confirmed) {
      deleteMutation.mutate(proposal.id);
    }
  };

  const handleChangeStatus = (proposal: ProposalSummary, new_status: string) => {
    const confirmed = window.confirm(
      `Alterar status da proposta ${proposal.number} para "${getProposalStatusLabel(new_status)}"?`
    );
    if (confirmed) {
      statusMutation.mutate({ id: proposal.id, new_status });
    }
  };

  const handleConvert = (proposal: ProposalSummary) => {
    setShowConvertModal(proposal);
  };

  const confirmConvert = () => {
    if (showConvertModal) {
      convertMutation.mutate({ id: showConvertModal.id });
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
  };

  if (isLoading) {
    return <LoadingState description="Carregando propostas..." />;
  }

  if (isError) {
    return (
      <ErrorState
        title="Erro ao carregar propostas"
        description={error instanceof Error ? error.message : 'Não foi possível carregar. Tente novamente.'}
      />
    );
  }

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Propostas Comerciais
        </h1>
        {canCreate('proposals') && (
          <button
            onClick={() => navigate('/proposals/new')}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            + Nova Proposta
          </button>
        )}
      </div>

      {/* Filtros */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mb-6">
        <form onSubmit={handleSearch} className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Buscar por número ou título..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            />
          </div>
          <div className="w-full md:w-48">
            <select
              value={filterStatus}
              onChange={(e) => {
                setFilterStatus(e.target.value);
                setPage(1);
              }}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              aria-label="Filtrar por status"
            >
              <option value="">Todos os status</option>
              <option value="rascunho">Rascunho</option>
              <option value="enviada">Enviada</option>
              <option value="aprovada">Aprovada</option>
              <option value="rejeitada">Rejeitada</option>
              <option value="cancelada">Cancelada</option>
            </select>
          </div>
          <button
            type="submit"
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Buscar
          </button>
        </form>
      </div>

      {/* Tabela */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        {data && data.items.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Número
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Cliente
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Título
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Valor Total
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Data Emissão
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Ações
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {data.items.map((proposal) => (
                    <tr key={proposal.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {proposal.number}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900 dark:text-gray-100">
                          {proposal.customer_name}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900 dark:text-gray-100 max-w-xs truncate">
                          {proposal.title}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                          {formatCurrency(proposal.total_amount)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getProposalStatusColor(
                            proposal.status
                          )}`}
                        >
                          {getProposalStatusIcon(proposal.status)} {getProposalStatusLabel(proposal.status)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {formatDate(proposal.issue_date)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                        {/* Botão GERAR OS (apenas para aprovadas sem OS) */}
                        {proposal.status === 'aprovada' && !proposal.has_service_order && (
                          <button
                            onClick={() => handleConvert(proposal)}
                            className="px-3 py-1 bg-gradient-to-r from-teal-500 to-teal-600 text-white rounded-md hover:from-teal-600 hover:to-teal-700 transition-all text-xs font-semibold shadow-sm"
                            title="Gerar Ordem de Serviço"
                          >
                            📋 Gerar OS
                          </button>
                        )}

                        {/* Indicador de OS já gerada */}
                        {proposal.has_service_order && (
                          <span className="px-2 py-1 bg-teal-100 dark:bg-teal-900/30 text-teal-800 dark:text-teal-300 border border-teal-300 dark:border-teal-700 rounded text-xs font-medium" title="Proposta já possui OS gerada">
                            ✅ OS Gerada
                          </span>
                        )}

                        {/* Botão Gerar PDF */}
                        <button
                          onClick={async () => {
                            const token = localStorage.getItem('access_token');
                            console.log('Iniciando geração de PDF...', {
                              proposalId: proposal.id,
                              proposalNumber: proposal.number,
                              hasToken: !!token
                            });
                            
                            try {
                              const url = `http://localhost:8000/proposals/${proposal.id}/pdf`;
                              console.log('URL:', url);
                              
                              const response = await fetch(url, {
                                headers: {
                                  'Authorization': `Bearer ${token}`
                                }
                              });
                              
                              console.log('Response status:', response.status);
                              console.log('Response ok:', response.ok);
                              
                              if (response.ok) {
                                const blob = await response.blob();
                                console.log('Blob recebido:', blob.size, 'bytes');
                                
                                const downloadUrl = window.URL.createObjectURL(blob);
                                const a = document.createElement('a');
                                a.href = downloadUrl;
                                a.download = `proposta-${proposal.number || proposal.id}.pdf`;
                                document.body.appendChild(a);
                                a.click();
                                window.URL.revokeObjectURL(downloadUrl);
                                document.body.removeChild(a);
                                
                                console.log('✅ PDF baixado com sucesso!');
                              } else {
                                const errorText = await response.text();
                                console.error('❌ Erro HTTP:', {
                                  status: response.status,
                                  statusText: response.statusText,
                                  body: errorText
                                });
                                alert(`Erro ao gerar PDF (${response.status}): ${response.statusText}\n\n${errorText.substring(0, 200)}`);
                              }
                            } catch (error) {
                              console.error('❌ Exceção ao gerar PDF:', error);
                              if (error instanceof Error) {
                                alert(`Erro ao gerar PDF: ${error.message}`);
                              } else {
                                alert('Erro ao gerar PDF: erro desconhecido');
                              }
                            }
                          }}
                          className="text-purple-600 dark:text-purple-400 hover:text-purple-900 dark:hover:text-purple-300"
                          title="Gerar PDF"
                        >
                          📄
                        </button>

                        {/* Ícones de ação */}
                        {canUpdate('proposals') && proposal.status !== 'aprovada' && (
                          <button
                            onClick={() => navigate(`/proposals/${proposal.id}/edit`)}
                            className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-900 dark:hover:text-indigo-300"
                            title="Editar"
                          >
                            ✏️
                          </button>
                        )}

                        {/* Ações de mudança de status */}
                        {proposal.status === 'rascunho' && (
                          <>
                            <button
                              onClick={() => handleChangeStatus(proposal, 'enviada')}
                              className="text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-300"
                              title="Enviar Proposta"
                            >
                              📤
                            </button>
                            <button
                              onClick={() => handleChangeStatus(proposal, 'cancelada')}
                              className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-300"
                              title="Cancelar"
                            >
                              🚫
                            </button>
                          </>
                        )}

                        {proposal.status === 'enviada' && (
                          <>
                            <button
                              onClick={() => handleChangeStatus(proposal, 'aprovada')}
                              className="text-green-600 dark:text-green-400 hover:text-green-900 dark:hover:text-green-300"
                              title="Aprovar"
                            >
                              ✅
                            </button>
                            <button
                              onClick={() => handleChangeStatus(proposal, 'rejeitada')}
                              className="text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300"
                              title="Rejeitar"
                            >
                              ❌
                            </button>
                          </>
                        )}

                        {canDelete('proposals') && (
                          <button
                            onClick={() => handleDelete(proposal)}
                            className="text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300"
                            title="Excluir"
                          >
                            🗑️
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Paginação */}
            <div className="bg-gray-50 dark:bg-gray-700 px-6 py-4 flex items-center justify-between">
              <div className="text-sm text-gray-700 dark:text-gray-300">
                Mostrando {(page - 1) * pageSize + 1} a {Math.min(page * pageSize, data.total)} de{' '}
                {data.total} propostas
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100 dark:hover:bg-gray-600 text-gray-900 dark:text-gray-100"
                >
                  Anterior
                </button>
                <span className="px-4 py-2 text-gray-900 dark:text-gray-100">
                  Página {page} de {totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100 dark:hover:bg-gray-600 text-gray-900 dark:text-gray-100"
                >
                  Próxima
                </button>
              </div>
            </div>
          </>
        ) : (
          <EmptyState
            title="Nenhuma proposta encontrada"
            description="Crie sua primeira proposta clicando no botão acima"
          />
        )}
      </div>

      {/* Modal de Confirmação de Conversão */}
      {showConvertModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">
              🔄 Gerar Ordem de Serviço
            </h3>
            <div className="mb-6 text-gray-700 dark:text-gray-300">
              <p className="mb-2">
                Confirma a conversão da proposta <strong>{showConvertModal.number}</strong> em Ordem de Serviço?
              </p>
              <div className="mt-4 p-4 bg-teal-50 dark:bg-teal-900/20 border border-teal-300 dark:border-teal-700 rounded-md">
                <p className="text-sm text-teal-800 dark:text-teal-300">
                  <strong>📋 A OS gerada terá:</strong>
                </p>
                <ul className="mt-2 text-sm text-teal-700 dark:text-teal-400 space-y-1">
                  <li>• Tipo: <strong>Projeto</strong></li>
                  <li>• Valores ocultos no relatório</li>
                  <li>• Vinculada à proposta {showConvertModal.number}</li>
                  <li>• Status inicial: Pendente</li>
                </ul>
              </div>
              <p className="mt-4 text-xs text-gray-500 dark:text-gray-400">
                ⚠️ Esta proposta não poderá gerar outra OS (prevenção de duplicatas)
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setShowConvertModal(null)}
                className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-900 dark:text-gray-100"
              >
                Cancelar
              </button>
              <button
                onClick={confirmConvert}
                disabled={convertMutation.isPending}
                className="flex-1 px-4 py-2 bg-teal-600 text-white rounded-md hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {convertMutation.isPending ? 'Gerando...' : 'Confirmar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
