import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createFinancialEntry, type CreateFinancialData } from '../../api/financial';

// Schema de validação com Zod
const financialSchema = z.object({
  kind: z.enum(['revenue', 'expense'], {
    errorMap: () => ({ message: 'Selecione Receita ou Despesa' }),
  }),
  amount: z.number({
    required_error: 'Valor é obrigatório',
    invalid_type_error: 'Valor deve ser um número',
  }).positive('Valor deve ser maior que zero'),
  description: z.string()
    .min(1, 'Descrição é obrigatória')
    .max(500, 'Descrição deve ter no máximo 500 caracteres'),
  occurred_at: z.string().optional(),
});

type FinancialFormData = z.infer<typeof financialSchema>;

interface FinancialFormProps {
  onSuccess: () => void;
}

export function FinancialForm({ onSuccess }: FinancialFormProps) {
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
  } = useForm<FinancialFormData>({
    resolver: zodResolver(financialSchema),
    defaultValues: {
      kind: 'revenue',
      amount: 0,
      description: '',
    },
  });

  const createMutation = useMutation({
    mutationFn: createFinancialEntry,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['financial'] });
      onSuccess();
    },
    onError: (error: any) => {
      const status = error.response?.status;
      
      if (status === 422) {
        // Erros de validação por campo
        const details = error.response?.data?.detail;
        if (Array.isArray(details)) {
          details.forEach((err: any) => {
            const field = err.loc?.[1];
            if (field && ['kind', 'amount', 'description', 'occurred_at'].includes(field)) {
              setError(field as keyof FinancialFormData, {
                type: 'manual',
                message: err.msg,
              });
            }
          });
        } else {
          alert('Erro de validação: ' + (error.response?.data?.detail || 'Dados inválidos'));
        }
      } else if (status === 403) {
        alert('Você não tem permissão para criar lançamentos financeiros');
      } else if (status === 400) {
        alert('Dados inválidos: ' + (error.response?.data?.detail || ''));
      } else {
        alert('Erro ao criar lançamento: ' + (error.response?.data?.detail || 'Erro desconhecido'));
      }
    },
  });

  const onSubmit = (data: FinancialFormData) => {
    // Preparar payload
    const payload: CreateFinancialData = {
      kind: data.kind,
      amount: data.amount,
      description: data.description,
    };

    // Se occurred_at foi preenchido, adicionar ao payload (ISO datetime)
    if (data.occurred_at) {
      payload.occurred_at = new Date(data.occurred_at).toISOString();
    }

    createMutation.mutate(payload);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {/* Tipo (Receita ou Despesa) */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Tipo <span className="text-red-500">*</span>
        </label>
        <select
          {...register('kind')}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="revenue">💰 Receita</option>
          <option value="expense">📉 Despesa</option>
        </select>
        {errors.kind && (
          <p className="mt-1 text-sm text-red-600">{errors.kind.message}</p>
        )}
      </div>

      {/* Valor */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Valor (R$) <span className="text-red-500">*</span>
        </label>
        <input
          type="number"
          step="0.01"
          {...register('amount', { valueAsNumber: true })}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="Ex: 150.50"
        />
        {errors.amount && (
          <p className="mt-1 text-sm text-red-600">{errors.amount.message}</p>
        )}
      </div>

      {/* Descrição */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Descrição <span className="text-red-500">*</span>
        </label>
        <textarea
          {...register('description')}
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="Ex: Pagamento de fornecedor XYZ"
        />
        {errors.description && (
          <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
        )}
      </div>

      {/* Data de Ocorrência (opcional) */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Data de Ocorrência (opcional)
        </label>
        <input
          type="datetime-local"
          {...register('occurred_at')}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <p className="mt-1 text-xs text-gray-500">
          Se não informado, será registrado com a data/hora atual
        </p>
        {errors.occurred_at && (
          <p className="mt-1 text-sm text-red-600">{errors.occurred_at.message}</p>
        )}
      </div>

      {/* Botões */}
      <div className="flex gap-3 pt-4">
        <button
          type="submit"
          disabled={createMutation.isPending}
          className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {createMutation.isPending ? 'Criando...' : 'Criar Lançamento'}
        </button>
      </div>
    </form>
  );
}
