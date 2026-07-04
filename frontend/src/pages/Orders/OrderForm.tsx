import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createOrder, patchOrder } from '../../api/orders';
import { useEffect } from 'react';

const orderSchema = z.object({
  description: z.string().min(1, 'Descrição é obrigatória').max(500, 'Descrição muito longa'),
  total: z.number().positive('Valor deve ser maior que zero'),
});

type OrderFormData = z.infer<typeof orderSchema>;

interface OrderFormProps {
  mode: 'create' | 'edit';
  initialData?: {
    id: string;
    description: string;
    total: number;
  };
  onSuccess: () => void;
  onCancel: () => void;
}

export function OrderForm({ mode, initialData, onSuccess, onCancel }: OrderFormProps) {
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setError,
  } = useForm<OrderFormData>({
    resolver: zodResolver(orderSchema),
    defaultValues: initialData ? {
      description: initialData.description,
      total: initialData.total,
    } : undefined,
  });

  // Atualizar form quando initialData mudar (modo edit)
  useEffect(() => {
    if (mode === 'edit' && initialData) {
      reset({
        description: initialData.description,
        total: initialData.total,
      });
    }
  }, [mode, initialData, reset]);

  const mutation = useMutation({
    mutationFn: (data: OrderFormData) => {
      if (mode === 'edit' && initialData) {
        return patchOrder(initialData.id, data);
      }
      return createOrder(data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      reset();
      onSuccess();
    },
    onError: (error: any) => {
      const status = error.response?.status;
      
      if (status === 422) {
        const detail = error.response.data?.detail;
        if (Array.isArray(detail)) {
          detail.forEach((err: any) => {
            const field = err.loc?.[1] as keyof OrderFormData;
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
        setError('root', { message: 'Pedido não encontrado' });
      } else {
        setError('root', { 
          message: error.response?.data?.detail || `Erro ao ${mode === 'edit' ? 'atualizar' : 'criar'} pedido` 
        });
      }
    },
  });

  const onSubmit = (data: OrderFormData) => {
    mutation.mutate(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {errors.root && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {errors.root.message}
        </div>
      )}

      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
          Descrição *
        </label>
        <input
          id="description"
          type="text"
          {...register('description')}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder="Ex: Pedido de materiais"
        />
        {errors.description && (
          <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="total" className="block text-sm font-medium text-gray-700 mb-1">
          Valor Total (R$) *
        </label>
        <input
          id="total"
          type="number"
          step="0.01"
          {...register('total', { valueAsNumber: true })}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder="0.00"
        />
        {errors.total && (
          <p className="mt-1 text-sm text-red-600">{errors.total.message}</p>
        )}
      </div>

      <div className="flex gap-3 pt-4">
        <button
          type="submit"
          disabled={mutation.isPending}
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {mutation.isPending 
            ? (mode === 'edit' ? 'Salvando...' : 'Criando...')
            : (mode === 'edit' ? 'Salvar Alterações' : 'Criar Pedido')
          }
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
        >
          Cancelar
        </button>
      </div>
    </form>
  );
}
