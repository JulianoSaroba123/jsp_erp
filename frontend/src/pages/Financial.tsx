import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  getFinancialEntries, 
  deleteFinancialEntry, 
  updateFinancialStatus,
  type FinancialEntry 
} from '../api/financial';
import { usePermissions } from '../auth/usePermissions';
import { FinancialForm } from './Financial/FinancialForm';
import { LoadingState, ErrorState, EmptyState } from '../components/ui/State';
import { formatCurrencyBRL, formatDateBR } from '../lib/format';

export function Financial() {
  const [page, setPage] = useState(1);
  const pageSize = 10;
  const [formMode, setFormMode] = useState<'create' | null>(null);
  const [statusChangeEntry, setStatusChangeEntry] = useState<FinancialEntry | null>(null);
  const [newStatus, setNewStatus] = useState<'pending' | 'paid' | 'canceled'>('pending');
  
  // Filtros
  const [filters, setFilters] = useState<{ kind: string; status: string }>({
    kind: '',
    status: '',
  });
  const [appliedFilters, setAppliedFilters] = useState<{ kind: string; status: string }>({
    kind: '',
    status: '',
  });

  const queryClient = useQueryClient();
  const { canCreate, canUpdate, canDelete } = usePermissions();

  // Buscar lançamentos
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['financial', page, pageSize, appliedFilters],
    queryFn: () => {
      const params: any = { page, page_size: pageSize };
      
      // Adicionar filtros apenas se preenchidos
      if (appliedFilters.kind) {
        params.kind = appliedFilters.kind as 'revenue' | 'expense';
      }
      if (appliedFilters.status) {
        params.status = appliedFilters.status as 'pending' | 'paid' | 'canceled';
      }
      
      return getFinancialEntries(params);
    },
  });

  // Mutation para deletar
  const deleteMutation = useMutation({
    mutationFn: deleteFinancialEntry,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['financial'] });
    },
    onError: (error: any) => {
      const status = error.response?.status;
      if (status === 404) {
        alert('Lançamento não encontrado ou já foi excluído');
      } else if (status === 403) {
        alert('Você não tem permissão para excluir este lançamento');
      } else {
        alert(error.response?.data?.detail || 'Erro ao excluir lançamento');
      }
    },
  });

  // Mutation para alterar status
  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: 'pending' | 'paid' | 'canceled' }) =>
      updateFinancialStatus(id, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['financial'] });
      setStatusChangeEntry(null);
      alert('Status atualizado com sucesso!');
    },
    onError: (error: any) => {
      const status = error.response?.status;
      if (status === 404) {
        alert('Lançamento não encontrado');
      } else if (status === 403) {
        alert('Sem permissão para alterar status');
      } else if (status === 400) {
        alert('Transição de status inválida: ' + (error.response?.data?.detail || ''));
      } else {
        alert(error.response?.data?.detail || 'Erro ao atualizar status');
      }
    },
  });

  const handleDelete = (entryId: string, description: string) => {
    const confirmed = window.confirm(
      `Tem certeza que deseja excluir o lançamento "${description}"?\n\nEsta ação não pode ser desfeita.`
    );
    if (confirmed) {
      deleteMutation.mutate(entryId);
    }
  };

  const handleOpenCreate = () => {
    setFormMode('create');
  };

  const handleCloseForm = () => {
    setFormMode(null);
  };

  const handleOpenStatusChange = (entry: FinancialEntry) => {
    setStatusChangeEntry(entry);
    setNewStatus(entry.status);
  };

  const handleStatusChange = () => {
    if (statusChangeEntry) {
      statusMutation.mutate({ id: statusChangeEntry.id, status: newStatus });
    }
  };

  const handleApplyFilters = () => {
    setAppliedFilters(filters);
    setPage(1); // Reset para primeira página ao aplicar filtros
  };

  const handleClearFilters = () => {
    setFilters({ kind: '', status: '' });
    setAppliedFilters({ kind: '', status: '' });
    setPage(1);
  };

  const formatCurrency = formatCurrencyBRL;
  const formatDate = formatDateBR;

  if (isLoading) {
    return <LoadingState description="Carregando lançamentos..." />;
  }

  if (isError) {
    return (
      <ErrorState 
        title="Erro ao carregar lançamentos"
        description={error instanceof Error ? error.message : 'Não foi possível carregar. Tente novamente.'}
      />
    );
  }

  const entries = data?.items || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / pageSize);

  return (
    <div>
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Financeiro</h1>
        {canCreate('financial') && (
          <button
            onClick={handleOpenCreate}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
          >
            + Novo Lançamento
          </button>
        )}
      </div>

      {/* Filtros */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Tipo
            </label>
            <select
              aria-label="Filtro de tipo"
              value={filters.kind}
              onChange={(e) => setFilters({ ...filters, kind: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            >
              <option value="">Todos</option>
              <option value="revenue">Receita</option>
              <option value="expense">Despesa</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Status
            </label>
            <select
              aria-label="Filtro de status"
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            >
              <option value="">Todos</option>
              <option value="pending">Pendente</option>
              <option value="paid">Pago</option>
              <option value="canceled">Cancelado</option>
            </select>
          </div>

          <div className="flex items-end gap-2">
            <button
              onClick={handleApplyFilters}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
            >
              🔍 Aplicar
            </button>
            <button
              onClick={handleClearFilters}
              className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-lg font-medium transition-colors"
            >
              ✖ Limpar
            </button>
          </div>

          <div className="flex items-end text-sm text-gray-600 dark:text-gray-400">
            {(appliedFilters.kind || appliedFilters.status) && (
              <p>
                Filtros ativos: 
                {appliedFilters.kind && ` Tipo=${appliedFilters.kind === 'revenue' ? 'Receita' : 'Despesa'}`}
                {appliedFilters.status && ` Status=${appliedFilters.status}`}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Modal de Criação */}
      {formMode === 'create' && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-2xl w-full p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Novo Lançamento</h2>
              <button
                onClick={handleCloseForm}
                className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
              >
                ✕
              </button>
            </div>
            <FinancialForm onSuccess={handleCloseForm} />
          </div>
        </div>
      )}

      {/* Modal de Alteração de Status */}
      {statusChangeEntry && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-md w-full p-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">Alterar Status</h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Lançamento: <strong>{statusChangeEntry.description}</strong>
            </p>
            <label className="block mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
              Novo Status:
            </label>
            <select
              aria-label="Novo status do lançamento"
              value={newStatus}
              onChange={(e) => setNewStatus(e.target.value as any)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg mb-4 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            >
              <option value="pending">Pendente</option>
              <option value="paid">Pago</option>
              <option value="canceled">Cancelado</option>
            </select>
            <div className="flex gap-3">
              <button
                onClick={handleStatusChange}
                disabled={statusMutation.isPending}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium disabled:opacity-50"
              >
                {statusMutation.isPending ? 'Salvando...' : 'Salvar'}
              </button>
              <button
                onClick={() => setStatusChangeEntry(null)}
                className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 px-4 py-2 rounded-lg font-medium"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {entries.length === 0 ? (
        <EmptyState 
          title="Nenhum lançamento encontrado"
          description="Comece criando seu primeiro lançamento financeiro"
          actionLabel={canCreate('financial') ? '+ Novo Lançamento' : undefined}
          onAction={canCreate('financial') ? handleOpenCreate : undefined}
        />
      ) : (
        <>
          <div className="bg-white dark:bg-gray-800 shadow-md rounded-lg overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Descrição
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Tipo
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Valor
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Data
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Ações
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {entries.map((entry) => (
                  <tr key={entry.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="px-6 py-4 text-sm text-gray-900 dark:text-gray-100">
                      {entry.description}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      {entry.kind === 'revenue' ? (
                        <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300">
                          Receita
                        </span>
                      ) : (
                        <span className="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300">
                          Despesa
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm font-medium">
                      <span className={entry.kind === 'revenue' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
                        {formatCurrency(entry.amount)}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm">
                      {entry.status === 'paid' && (
                        <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">
                          Pago
                        </span>
                      )}
                      {entry.status === 'pending' && (
                        <span className="px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300">
                          Pendente
                        </span>
                      )}
                      {entry.status === 'canceled' && (
                        <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">
                          Cancelado
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">
                      {formatDate(entry.occurred_at)}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <div className="flex gap-2">
                        {canUpdate('financial') && (
                          <button
                            onClick={() => handleOpenStatusChange(entry)}
                            className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-medium"
                          >
                            📝 Status
                          </button>
                        )}
                        {canDelete('financial') && (
                          <button
                            onClick={() => handleDelete(entry.id, entry.description)}
                            disabled={deleteMutation.isPending}
                            className="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300 font-medium disabled:opacity-50"
                          >
                            🗑️ Excluir
                          </button>
                        )}
                        {!canUpdate('financial') && !canDelete('financial') && (
                          <span className="text-gray-400 dark:text-gray-500 text-xs">Sem permissão</span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Paginação */}
          <div className="mt-4 flex items-center justify-between">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Mostrando {entries.length} de {total} lançamentos
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Anterior
              </button>
              <span className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300">
                Página {page} de {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Próxima
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
