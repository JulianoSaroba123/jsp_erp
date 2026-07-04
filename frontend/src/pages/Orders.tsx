import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getOrders, deleteOrder, Order } from '../api/orders';
import { OrderForm } from './Orders/OrderForm';
import { usePermissions } from '../auth/usePermissions';
import { LoadingState, ErrorState, EmptyState } from '../components/ui/State';
import { formatCurrencyBRL, formatDateBR } from '../lib/format';

export function Orders() {
  const [page, setPage] = useState(1);
  const [formMode, setFormMode] = useState<'create' | 'edit' | null>(null);
  const [editingOrder, setEditingOrder] = useState<Order | null>(null);
  const pageSize = 10;
  const queryClient = useQueryClient();
  const { canCreate, canUpdate, canDelete } = usePermissions();

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['orders', page],
    queryFn: () => getOrders({ page, page_size: pageSize }),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteOrder,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
    },
    onError: (error: any) => {
      const status = error.response?.status;
      if (status === 404) {
        alert('Pedido não encontrado ou já foi excluído');
      } else if (status === 403) {
        alert('Você não tem permissão para excluir este pedido');
      } else {
        alert(error.response?.data?.detail || 'Erro ao excluir pedido');
      }
    },
  });

  const handleDelete = (orderId: string, description: string) => {
    const confirmed = window.confirm(
      `Tem certeza que deseja excluir o pedido "${description}"?\n\nEsta ação não pode ser desfeita.`
    );
    if (confirmed) {
      deleteMutation.mutate(orderId);
    }
  };

  const handleEdit = (order: Order) => {
    setEditingOrder(order);
    setFormMode('edit');
  };

  const handleCloseForm = () => {
    setFormMode(null);
    setEditingOrder(null);
  };

  const handleOpenCreate = () => {
    setEditingOrder(null);
    setFormMode('create');
  };

  if (isLoading) {
    return <LoadingState description="Carregando pedidos..." />;
  }

  if (isError) {
    return (
      <ErrorState 
        title="Erro ao carregar pedidos"
        description={error instanceof Error ? error.message : 'Não foi possível carregar. Tente novamente.'}
      />
    );
  }

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Pedidos</h1>
        {canCreate('orders') && (
          <button 
            onClick={handleOpenCreate}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            + Novo Pedido
          </button>
        )}
      </div>

      {/* Formulário de criação/edição */}
      {formMode && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            {formMode === 'create' ? 'Criar Novo Pedido' : 'Editar Pedido'}
          </h2>
          <OrderForm 
            mode={formMode}
            initialData={editingOrder ? {
              id: editingOrder.id,
              description: editingOrder.description,
              total: editingOrder.total,
            } : undefined}
            onSuccess={handleCloseForm} 
            onCancel={handleCloseForm}
          />
        </div>
      )}

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        {data && data.items.length === 0 ? (
          <EmptyState 
            title="Nenhum pedido encontrado"
            description="Comece criando seu primeiro pedido"
            actionLabel={canCreate('orders') ? '+ Novo Pedido' : undefined}
            onAction={canCreate('orders') ? handleOpenCreate : undefined}
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Descrição
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Total
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Data
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Ações
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {data?.items.map((order) => (
                    <tr key={order.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">
                        {order.id.substring(0, 8)}...
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900 dark:text-gray-100">
                        {order.description}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                        {formatCurrencyBRL(order.total)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          order.status === 'completed' 
                            ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                            : order.status === 'pending'
                            ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300'
                            : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                        }`}>
                          {order.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {formatDateBR(order.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex justify-end gap-2">
                          {canUpdate('orders') && (
                            <button
                              onClick={() => handleEdit(order)}
                              className="text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-300"
                              title="Editar pedido"
                            >
                              ✏️ Editar
                            </button>
                          )}
                          {canDelete('orders') && (
                            <button
                              onClick={() => handleDelete(order.id, order.description)}
                              disabled={deleteMutation.isPending}
                              className="text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300 disabled:opacity-50 disabled:cursor-not-allowed"
                              title="Excluir pedido"
                            >
                              🗑️ Excluir
                            </button>
                          )}
                          {!canUpdate('orders') && !canDelete('orders') && (
                            <span className="text-gray-400 dark:text-gray-500 text-sm">Sem permissão</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Paginação */}
            <div className="bg-gray-50 dark:bg-gray-700 px-6 py-4 flex items-center justify-between border-t border-gray-200 dark:border-gray-600">
              <div className="flex-1 flex justify-between sm:hidden">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="relative inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Anterior
                </button>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={page >= totalPages}
                  className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Próxima
                </button>
              </div>
              <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm text-gray-700 dark:text-gray-300">
                    Mostrando{' '}
                    <span className="font-medium">{(page - 1) * pageSize + 1}</span>
                    {' '}-{' '}
                    <span className="font-medium">
                      {Math.min(page * pageSize, data?.total || 0)}
                    </span>
                    {' '}de{' '}
                    <span className="font-medium">{data?.total || 0}</span>
                    {' '}resultados
                  </p>
                </div>
                <div>
                  <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                    <button
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                      className="relative inline-flex items-center px-3 py-2 rounded-l-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm font-medium text-gray-500 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Anterior
                    </button>
                    <span className="relative inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm font-medium text-gray-700 dark:text-gray-300">
                      Página {page} de {totalPages}
                    </span>
                    <button
                      onClick={() => setPage((p) => p + 1)}
                      disabled={page >= totalPages}
                      className="relative inline-flex items-center px-3 py-2 rounded-r-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm font-medium text-gray-500 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Próxima
                    </button>
                  </nav>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
