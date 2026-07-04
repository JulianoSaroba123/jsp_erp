import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getCustomers, deleteCustomer, Customer } from '../api/customers';
import { CustomerForm } from './Customers/CustomerForm';
import { usePermissions } from '../auth/usePermissions';
import { LoadingState, ErrorState, EmptyState } from '../components/ui/State';
import { formatDateBR, formatDocumentBR, formatPhoneBR } from '../lib/format';

export function Customers() {
  const [page, setPage] = useState(1);
  const [formMode, setFormMode] = useState<'create' | 'edit' | null>(null);
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null);
  const pageSize = 10;
  const queryClient = useQueryClient();
  const { canCreate, canUpdate, canDelete } = usePermissions();

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['customers', page],
    queryFn: () => getCustomers({ page, page_size: pageSize }),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteCustomer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
    },
    onError: (error: any) => {
      const status = error.response?.status;
      if (status === 404) {
        alert('Cliente não encontrado ou já foi excluído');
      } else if (status === 403) {
        alert('Você não tem permissão para excluir este cliente');
      } else {
        alert(error.response?.data?.detail || 'Erro ao excluir cliente');
      }
    },
  });

  const handleDelete = (customerId: string, customerName: string) => {
    const confirmed = window.confirm(
      `Tem certeza que deseja excluir o cliente "${customerName}"?\n\nEsta ação não pode ser desfeita.`
    );
    if (confirmed) {
      deleteMutation.mutate(customerId);
    }
  };

  const handleEdit = (customer: Customer) => {
    setEditingCustomer(customer);
    setFormMode('edit');
  };

  const handleCloseForm = () => {
    setFormMode(null);
    setEditingCustomer(null);
  };

  const handleOpenCreate = () => {
    setEditingCustomer(null);
    setFormMode('create');
  };

  const editingCustomerFormData = editingCustomer
    ? {
        ...editingCustomer,
        trade_name: editingCustomer.trade_name ?? undefined,
        cpf_cnpj: editingCustomer.cpf_cnpj ?? undefined,
        state_registration: editingCustomer.state_registration ?? undefined,
        email: editingCustomer.email ?? undefined,
        phone: editingCustomer.phone ?? undefined,
        phone2: editingCustomer.phone2 ?? undefined,
        cep: editingCustomer.cep ?? undefined,
        street: editingCustomer.street ?? undefined,
        number: editingCustomer.number ?? undefined,
        address_complement: editingCustomer.address_complement ?? undefined,
        neighborhood: editingCustomer.neighborhood ?? undefined,
        city: editingCustomer.city ?? undefined,
        state: editingCustomer.state ?? undefined,
        notes: editingCustomer.notes ?? undefined,
      }
    : undefined;

  if (isLoading) {
    return <LoadingState description="Carregando clientes..." />;
  }

  if (isError) {
    return (
      <ErrorState 
        title="Erro ao carregar clientes"
        description={error instanceof Error ? error.message : 'Não foi possível carregar. Tente novamente.'}
      />
    );
  }

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Clientes</h1>
        {canCreate('customers') && (
          <button 
            onClick={handleOpenCreate}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            + Novo Cliente
          </button>
        )}
      </div>

      {/* Formulário de criação/edição */}
      {formMode && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            {formMode === 'create' ? 'Criar Novo Cliente' : 'Editar Cliente'}
          </h2>
          <CustomerForm 
            mode={formMode}
            initialData={editingCustomerFormData}
            onSuccess={handleCloseForm} 
            onCancel={handleCloseForm}
          />
        </div>
      )}

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        {data && data.items.length === 0 ? (
          <EmptyState 
            title="Nenhum cliente encontrado"
            description="Comece criando seu primeiro cliente"
            actionLabel={canCreate('customers') ? '+ Novo Cliente' : undefined}
            onAction={canCreate('customers') ? handleOpenCreate : undefined}
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Nome
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      CPF/CNPJ
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Telefone
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Email
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Cidade/UF
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Criado em
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Ações
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {data?.items.map((customer) => (
                    <tr key={customer.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900 dark:text-gray-100">{customer.name}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-700 dark:text-gray-300">{formatDocumentBR(customer.cpf_cnpj)}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-700 dark:text-gray-300">{formatPhoneBR(customer.phone)}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-700 dark:text-gray-300">{customer.email || '-'}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-700 dark:text-gray-300">
                          {customer.city && customer.state 
                            ? `${customer.city}/${customer.state}` 
                            : customer.city || customer.state || '-'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">
                        {formatDateBR(customer.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                        {canUpdate('customers') && (
                          <button
                            onClick={() => handleEdit(customer)}
                            className="text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-300 transition-colors"
                          >
                            Editar
                          </button>
                        )}
                        {canDelete('customers') && (
                          <button
                            onClick={() => handleDelete(customer.id, customer.name)}
                            disabled={deleteMutation.isPending}
                            className="text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300 disabled:opacity-50 transition-colors"
                          >
                            Excluir
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
                    onClick={() => setPage(page - 1)}
                    disabled={page === 1}
                    className="relative inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Anterior
                  </button>
                  <button
                    onClick={() => setPage(page + 1)}
                    disabled={page >= totalPages}
                    className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Próximo
                  </button>
                </div>
                <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      Mostrando{' '}
                      <span className="font-medium">{(page - 1) * pageSize + 1}</span>
                      {' '}até{' '}
                      <span className="font-medium">
                        {Math.min(page * pageSize, data?.total || 0)}
                      </span>
                      {' '}de{' '}
                      <span className="font-medium">{data?.total || 0}</span>
                      {' '}resultados
                    </p>
                  </div>
                  <div>
                    <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                      <button
                        onClick={() => setPage(page - 1)}
                        disabled={page === 1}
                        className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm font-medium text-gray-500 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Anterior
                      </button>
                      <span className="relative inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm font-medium text-gray-700 dark:text-gray-300">
                        Página {page} de {totalPages}
                      </span>
                      <button
                        onClick={() => setPage(page + 1)}
                        disabled={page >= totalPages}
                        className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm font-medium text-gray-500 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Próximo
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
