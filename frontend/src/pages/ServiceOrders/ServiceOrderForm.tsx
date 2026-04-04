import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createServiceOrder, updateServiceOrder } from '../../api/serviceOrders';
import { getCustomers } from '../../api/customers';
import { useEffect } from 'react';

const serviceOrderSchema = z.object({
  customer_id: z.string().uuid('Selecione um cliente'),
  title: z.string().min(3, 'Título muito curto').max(200, 'Título muito longo'),
  description: z.string().optional(),
  requester: z.string().optional(),
  problem_description: z.string().optional(),
  priority: z.enum(['baixa', 'normal', 'alta', 'urgente']).default('normal'),
  expected_date: z.string().optional(),
  technician: z.string().optional(),
  equipment: z.string().optional(),
  brand_model: z.string().optional(),
  serial_number: z.string().optional(),
  reported_defect: z.string().optional(),
});

type ServiceOrderFormData = z.infer<typeof serviceOrderSchema>;

interface ServiceOrderFormProps {
  mode: 'create' | 'edit';
  initialData?: {
    id: string;
    customer_id: string;
    title: string;
    description?: string;
    requester?: string;
    problem_description?: string;
    priority: 'baixa' | 'normal' | 'alta' | 'urgente';
    expected_date?: string;
    technician?: string;
    equipment?: string;
    brand_model?: string;
    serial_number?: string;
    reported_defect?: string;
  };
  onSuccess: () => void;
  onCancel: () => void;
}

export function ServiceOrderForm({ mode, initialData, onSuccess, onCancel }: ServiceOrderFormProps) {
  const queryClient = useQueryClient();

  // Carregar clientes para o select
  const { data: customersData } = useQuery({
    queryKey: ['customers', 1, 100],
    queryFn: () => getCustomers({ page: 1, page_size: 100 }),
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setError,
  } = useForm<ServiceOrderFormData>({
    resolver: zodResolver(serviceOrderSchema),
    defaultValues: initialData ? {
      customer_id: initialData.customer_id,
      title: initialData.title,
      description: initialData.description || '',
      requester: initialData.requester || '',
      problem_description: initialData.problem_description || '',
      priority: initialData.priority,
      expected_date: initialData.expected_date || '',
      technician: initialData.technician || '',
      equipment: initialData.equipment || '',
      brand_model: initialData.brand_model || '',
      serial_number: initialData.serial_number || '',
      reported_defect: initialData.reported_defect || '',
    } : {
      priority: 'normal',
    },
  });

  useEffect(() => {
    if (mode === 'edit' && initialData) {
      reset({
        customer_id: initialData.customer_id,
        title: initialData.title,
        description: initialData.description || '',
        requester: initialData.requester || '',
        problem_description: initialData.problem_description || '',
        priority: initialData.priority,
        expected_date: initialData.expected_date || '',
        technician: initialData.technician || '',
        equipment: initialData.equipment || '',
        brand_model: initialData.brand_model || '',
        serial_number: initialData.serial_number || '',
        reported_defect: initialData.reported_defect || '',
      });
    }
  }, [mode, initialData, reset]);

  const mutation = useMutation({
    mutationFn: (data: ServiceOrderFormData) => {
      if (mode === 'edit' && initialData) {
        return updateServiceOrder(initialData.id, data);
      }
      return createServiceOrder(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['service-orders'] });
      reset();
      onSuccess();
    },
    onError: (error: any) => {
      const status = error.response?.status;
      
      if (status === 422) {
        const detail = error.response.data?.detail;
        if (Array.isArray(detail)) {
          detail.forEach((err: any) => {
            const field = err.loc?.[1] as keyof ServiceOrderFormData;
            if (field) {
              setError(field, { message: err.msg });
            }
          });
        } else {
          setError('root', { message: detail || 'Erro de validação' });
        }
      } else if (status === 403) {
        setError('root', { message: 'Você não tem permissão para realizar esta ação' });
      } else if (status === 404) {
        setError('root', { message: 'Ordem de serviço não encontrada' });
      } else {
        setError('root', { 
          message: error.response?.data?.detail || `Erro ao ${mode === 'edit' ? 'atualizar' : 'criar'} ordem de serviço` 
        });
      }
    },
  });

  const onSubmit = (data: ServiceOrderFormData) => {
    mutation.mutate(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {errors.root && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded">
          {errors.root.message}
        </div>
      )}

      {/* Seção: Dados Básicos */}
      <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">📋 Dados Básicos</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Cliente */}
          <div>
            <label htmlFor="customer_id" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Cliente *
            </label>
            <select
              id="customer_id"
              {...register('customer_id')}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white"
            >
              <option value="">Selecione um cliente...</option>
              {customersData?.items.map((customer) => (
                <option key={customer.id} value={customer.id}>
                  {customer.name} {customer.cpf_cnpj ? `(${customer.cpf_cnpj})` : ''}
                </option>
              ))}
            </select>
            {errors.customer_id && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.customer_id.message}</p>
            )}
          </div>

          {/* Prioridade */}
          <div>
            <label htmlFor="priority" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Prioridade
            </label>
            <select
              id="priority"
              {...register('priority')}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white"
            >
              <option value="baixa">Baixa</option>
              <option value="normal">Normal</option>
              <option value="alta">Alta</option>
              <option value="urgente">Urgente</option>
            </select>
            {errors.priority && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.priority.message}</p>
            )}
          </div>

          {/* Título */}
          <div className="md:col-span-2">
            <label htmlFor="title" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Título *
            </label>
            <input
              id="title"
              type="text"
              {...register('title')}
              placeholder="Ex: Manutenção Preventiva - Computador Dell"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white"
            />
            {errors.title && (
              <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.title.message}</p>
            )}
          </div>

          {/* Solicitante */}
          <div>
            <label htmlFor="requester" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Solicitante
            </label>
            <input
              id="requester"
              type="text"
              {...register('requester')}
              placeholder="Nome do solicitante"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white"
            />
          </div>

          {/* Data Prevista */}
          <div>
            <label htmlFor="expected_date" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Data Prevista de Conclusão
            </label>
            <input
              id="expected_date"
              type="date"
              {...register('expected_date')}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white"
            />
          </div>

          {/* Técnico */}
          <div className="md:col-span-2">
            <label htmlFor="technician" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Técnico Responsável
            </label>
            <input
              id="technician"
              type="text"
              {...register('technician')}
              placeholder="Nome do técnico"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white"
            />
          </div>

          {/* Descrição */}
          <div className="md:col-span-2">
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Descrição Geral
            </label>
            <textarea
              id="description"
              {...register('description')}
              rows={3}
              placeholder="Descreva a ordem de serviço..."
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white"
            />
          </div>
        </div>
      </div>

      {/* Seção: Equipamento */}
      <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4">🖥️ Equipamento</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Equipamento */}
          <div>
            <label htmlFor="equipment" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Equipamento
            </label>
            <input
              id="equipment"
              type="text"
              {...register('equipment')}
              placeholder="Ex: Notebook, Impressora, etc."
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white"
            />
          </div>

          {/* Marca/Modelo */}
          <div>
            <label htmlFor="brand_model" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Marca/Modelo
            </label>
            <input
              id="brand_model"
              type="text"
              {...register('brand_model')}
              placeholder="Ex: Dell Inspiron 15"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white"
            />
          </div>

          {/* Número de Série */}
          <div>
            <label htmlFor="serial_number" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Número de Série
            </label>
            <input
              id="serial_number"
              type="text"
              {...register('serial_number')}
              placeholder="Ex: ABC123456789"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white"
            />
          </div>

          {/* Defeito Relatado */}
          <div className="md:col-span-3">
            <label htmlFor="reported_defect" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Defeito Relatado
            </label>
            <textarea
              id="reported_defect"
              {...register('reported_defect')}
              rows={2}
              placeholder="Descreva o problema reportado..."
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white"
            />
          </div>

          {/* Descrição do Problema */}
          <div className="md:col-span-3">
            <label htmlFor="problem_description" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Descrição Detalhada do Problema
            </label>
            <textarea
              id="problem_description"
              {...register('problem_description')}
              rows={3}
              placeholder="Informações adicionais sobre o problema..."
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-white"
            />
          </div>
        </div>
      </div>

      {/* Botões de Ação */}
      <div className="flex gap-3 justify-end pt-4 border-t border-gray-200 dark:border-gray-700">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          disabled={mutation.isPending}
        >
          Cancelar
        </button>
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={mutation.isPending}
        >
          {mutation.isPending 
            ? (mode === 'edit' ? 'Atualizando...' : 'Criando...') 
            : (mode === 'edit' ? 'Atualizar OS' : 'Criar OS')
          }
        </button>
      </div>
    </form>
  );
}
