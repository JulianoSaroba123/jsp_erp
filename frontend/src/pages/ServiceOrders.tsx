import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getServiceOrders,
  deleteServiceOrder,
  changeServiceOrderStatus,
  getServiceOrderById,
  ServiceOrder,
  getStatusLabel,
  getStatusColor,
  getPriorityLabel,
  getPriorityColor,
  getTipoOrdemLabel,
  getTipoOrdemColor,
} from '../api/serviceOrders';
import { usePermissions } from '../auth/usePermissions';
import { LoadingState, ErrorState, EmptyState } from '../components/ui/State';
import { formatDateBR, formatCurrencyBRL } from '../lib/format';
import { ServiceOrderFormExpanded } from './ServiceOrders/ServiceOrderFormExpanded';

export function ServiceOrders() {
  const [page, setPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterPriority, setFilterPriority] = useState<string>('');
  const [formMode, setFormMode] = useState<'create' | 'edit' | null>(null);
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);
  const pageSize = 15;
  const queryClient = useQueryClient();
  const { canCreate, canUpdate, canDelete } = usePermissions();

  // Carregar ordem de serviço para edição
  const { data: selectedOrderData } = useQuery({
    queryKey: ['service-order', selectedOrderId],
    queryFn: () => getServiceOrderById(selectedOrderId!),
    enabled: !!selectedOrderId && formMode === 'edit',
  });

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['service-orders', page, searchTerm, filterStatus, filterPriority],
    queryFn: () =>
      getServiceOrders({
        page,
        page_size: pageSize,
        search: searchTerm || undefined,
        status: filterStatus || undefined,
        priority: filterPriority || undefined,
      }),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteServiceOrder,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['service-orders'] });
    },
    onError: (error: any) => {
      const status = error.response?.status;
      if (status === 404) {
        alert('Ordem de serviço não encontrada ou já foi excluída');
      } else if (status === 403) {
        alert('Você não tem permissão para excluir esta ordem de serviço');
      } else {
        alert(error.response?.data?.detail || 'Erro ao excluir ordem de serviço');
      }
    },
  });

  const statusMutation = useMutation({
    mutationFn: ({ id, new_status }: { id: string; new_status: ServiceOrder['status'] }) =>
      changeServiceOrderStatus(id, { new_status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['service-orders'] });
      alert('Status atualizado com sucesso!');
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Erro ao alterar status');
    },
  });

  const handleDelete = (order: ServiceOrder) => {
    const confirmed = window.confirm(
      `Tem certeza que deseja excluir a OS ${order.number} - "${order.title}"?\n\nEsta ação não pode ser desfeita.`
    );
    if (confirmed) {
      deleteMutation.mutate(order.id);
    }
  };

  const handleChangeStatus = (order: ServiceOrder, new_status: ServiceOrder['status']) => {
    statusMutation.mutate({ id: order.id, new_status });
  };

  const handleView = (order: ServiceOrder) => {
    // TODO: Implementar modal/página de visualização detalhada
    alert(`Visualizar OS ${order.number}\n\nVisualização detalhada em desenvolvimento...`);
  };

  const handleEdit = (order: ServiceOrder) => {
    setSelectedOrderId(order.id);
    setFormMode('edit');
  };

  const handleOpenCreate = () => {
    setSelectedOrderId(null);
    setFormMode('create');
  };

  const handleCloseForm = () => {
    setFormMode(null);
    setSelectedOrderId(null);
    queryClient.invalidateQueries({ queryKey: ['service-orders'] });
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
  };

  if (isLoading) {
    return <LoadingState description="Carregando ordens de serviço..." />;
  }

  if (isError) {
    return (
      <ErrorState
        title="Erro ao carregar ordens de serviço"
        description={error instanceof Error ? error.message : 'Não foi possível carregar. Tente novamente.'}
      />
    );
  }

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Ordens de Serviço
        </h1>
        {canCreate('service_orders') && (
          <button
            onClick={handleOpenCreate}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            + Nova OS
          </button>
        )}
      </div>

      {/* Formulário de Criação/Edição */}
      {formMode && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            {formMode === 'create' ? '🔧 Nova Ordem de Serviço' : '✏️ Editar Ordem de Serviço'}
          </h2>
          {formMode === 'edit' && !selectedOrderData ? (
            <div className="py-8 text-center text-gray-500 dark:text-gray-400">
              Carregando dados da OS...
            </div>
          ) : (
            <ServiceOrderFormExpanded
              mode={formMode}
              initialData={
                formMode === 'edit' && selectedOrderData
                  ? {
                      id: selectedOrderData.id,
                      customer_id: selectedOrderData.customer_id,
                      order_type: selectedOrderData.order_type,
                      service_type: selectedOrderData.service_type,
                      location: selectedOrderData.location,
                      title: selectedOrderData.title,
                      description: selectedOrderData.description,
                      requester: selectedOrderData.requester,
                      problem_description: selectedOrderData.problem_description,
                      status: selectedOrderData.status,
                      priority: selectedOrderData.priority,
                      opening_date: selectedOrderData.opening_date,
                      expected_date: selectedOrderData.expected_date,
                      scheduled_date: selectedOrderData.scheduled_date,
                      completed_date: selectedOrderData.completed_date,
                      start_time: selectedOrderData.start_time,
                      end_time: selectedOrderData.end_time,
                      total_hours: selectedOrderData.total_hours,
                      initial_km: selectedOrderData.initial_km,
                      final_km: selectedOrderData.final_km,
                      total_km: selectedOrderData.total_km,
                      technician: selectedOrderData.technician,
                      equipment: selectedOrderData.equipment,
                      brand_model: selectedOrderData.brand_model,
                      serial_number: selectedOrderData.serial_number,
                      reported_defect: selectedOrderData.reported_defect,
                      technical_diagnosis: selectedOrderData.technical_diagnosis,
                      solution: selectedOrderData.solution,
                      notes: selectedOrderData.notes,
                      attachments_notes: selectedOrderData.attachments_notes,
                      service_amount: selectedOrderData.service_amount,
                      parts_amount: selectedOrderData.parts_amount,
                      total_amount: selectedOrderData.total_amount,
                      warranty_days: selectedOrderData.warranty_days,
                      discount_amount: selectedOrderData.discount_amount,
                      payment_condition: selectedOrderData.payment_condition,
                      installment_count: selectedOrderData.installment_count,
                      down_payment: selectedOrderData.down_payment,
                      payment_status: selectedOrderData.payment_status,
                      items: selectedOrderData.items,
                      products: selectedOrderData.products,
                      installments: selectedOrderData.installments,
                      attachments: selectedOrderData.attachments,
                    }
                  : undefined
              }
              onSuccess={handleCloseForm}
              onCancel={handleCloseForm}
            />
          )}
        </div>
      )}

      {/* Filtros */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mb-6">
        <form onSubmit={handleSearch} className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label htmlFor="search-input" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Buscar
            </label>
            <input
              id="search-input"
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Número, título, cliente..."
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            />
          </div>

          <div>
            <label htmlFor="status-filter" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Status
            </label>
            <select
              id="status-filter"
              value={filterStatus}
              onChange={(e) => {
                setFilterStatus(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="">Todos</option>
              <option value="pendente">Pendente</option>
              <option value="em_execucao">Em Execução</option>
              <option value="finalizada">Finalizada</option>
              <option value="cancelada">Cancelada</option>
            </select>
          </div>

          <div>
            <label htmlFor="priority-filter" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Prioridade
            </label>
            <select
              id="priority-filter"
              value={filterPriority}
              onChange={(e) => {
                setFilterPriority(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="">Todas</option>
              <option value="baixa">Baixa</option>
              <option value="normal">Normal</option>
              <option value="alta">Alta</option>
              <option value="urgente">Urgente</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              className="w-full px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
            >
              Buscar
            </button>
          </div>
        </form>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        {data && data.items.length === 0 ? (
          <EmptyState
            title="Nenhuma ordem de serviço encontrada"
            description="Comece criando sua primeira ordem de serviço"
            actionLabel={canCreate('service_orders') ? '+ Nova OS' : undefined}
            onAction={canCreate('service_orders') ? handleOpenCreate : undefined}
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Número
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Título
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Cliente
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Tipo
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Técnico
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Prioridade
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Data Abertura
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Valor Total
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
                        {order.number}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900 dark:text-gray-100">
                        <div className="max-w-xs truncate">{order.title}</div>
                        {order.equipment && (
                          <div className="text-xs text-gray-500 dark:text-gray-400 truncate max-w-xs">
                            {order.equipment}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                        {order.customer_name || 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getTipoOrdemColor(order.order_type)}`}>
                          {getTipoOrdemLabel(order.order_type)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                        {order.technician || 'Sem técnico'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(
                            order.status
                          )}`}
                        >
                          {getStatusLabel(order.status)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getPriorityColor(
                            order.priority
                          )}`}
                        >
                          {getPriorityLabel(order.priority)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                        {formatDateBR(order.opening_date)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                        {formatCurrencyBRL(order.total_amount)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                        <button
                          onClick={() => handleView(order)}
                          className="text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-300"
                          title="Visualizar"
                        >
                          👁️
                        </button>

                        {canUpdate('service_orders') && order.status !== 'finalizada' && order.status !== 'cancelada' && (
                          <>
                            <button
                              onClick={() => handleEdit(order)}
                              className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-900 dark:hover:text-indigo-300"
                              title="Editar"
                            >
                              ✏️
                            </button>

                            {order.status === 'pendente' && (
                              <button
                                onClick={() => handleChangeStatus(order, 'em_execucao')}
                                className="text-green-600 dark:text-green-400 hover:text-green-900 dark:hover:text-green-300"
                                title="Iniciar Execução"
                              >
                                ▶️
                              </button>
                            )}

                            {order.status === 'em_execucao' && (
                              <button
                                onClick={() => handleChangeStatus(order, 'finalizada')}
                                className="text-green-600 dark:text-green-400 hover:text-green-900 dark:hover:text-green-300"
                                title="Finalizar"
                              >
                                ✅
                              </button>
                            )}
                          </>
                        )}

                        {canDelete('service_orders') && order.status === 'pendente' && (
                          <button
                            onClick={() => handleDelete(order)}
                            className="text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300"
                            disabled={deleteMutation.isPending}
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
            {totalPages > 1 && (
              <div className="bg-white dark:bg-gray-800 px-4 py-3 flex items-center justify-between border-t border-gray-200 dark:border-gray-700 sm:px-6">
                <div className="flex-1 flex justify-between sm:hidden">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="relative inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Anterior
                  </button>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Próxima
                  </button>
                </div>
                <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      Mostrando <span className="font-medium">{(page - 1) * pageSize + 1}</span> até{' '}
                      <span className="font-medium">
                        {Math.min(page * pageSize, data?.total || 0)}
                      </span>{' '}
                      de <span className="font-medium">{data?.total || 0}</span> resultados
                    </p>
                  </div>
                  <div>
                    <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                      <button
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                        disabled={page === 1}
                        className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm font-medium text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        ←
                      </button>
                      {[...Array(totalPages)].slice(Math.max(0, page - 3), Math.min(totalPages, page + 2)).map((_, idx) => {
                        const pageNum = Math.max(0, page - 3) + idx + 1;
                        return (
                          <button
                            key={pageNum}
                            onClick={() => setPage(pageNum)}
                            className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                              page === pageNum
                                ? 'z-10 bg-blue-50 dark:bg-blue-900 border-blue-500 text-blue-600 dark:text-blue-300'
                                : 'bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
                            }`}
                          >
                            {pageNum}
                          </button>
                        );
                      })}
                      <button
                        onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                        disabled={page === totalPages}
                        className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm font-medium text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        →
                      </button>
                    </nav>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
