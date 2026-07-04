import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../../api/client';
import { FinancialEntry } from '../../api/financial';

// Schema de validação com Zod
const financialEditSchema = z.object({
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
  status: z.enum(['pending', 'paid', 'canceled']).optional(),
  
  // Campos profissionais Phase 1
  category: z.string().max(100).optional(),
  subcategory: z.string().max(100).optional(),
  due_date: z.string().optional(),
  payment_date: z.string().optional(),
  document_number: z.string().max(50).optional(),
  document_type: z.string().max(50).optional(),
  payment_method: z.string().max(50).optional(),
  notes: z.string().optional(),
});

type FinancialEditFormData = z.infer<typeof financialEditSchema>;

interface FinancialEditFormProps {
  entry: FinancialEntry;
  onSuccess: () => void;
  onCancel: () => void;
}

// Função para converter data ISO para input date
function formatDateForInput(isoDate: string | null | undefined): string {
  if (!isoDate) return '';
  try {
    const date = new Date(isoDate);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  } catch {
    return '';
  }
}

export function FinancialEditForm({ entry, onSuccess, onCancel }: FinancialEditFormProps) {
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
  } = useForm<FinancialEditFormData>({
    resolver: zodResolver(financialEditSchema),
    defaultValues: {
      kind: entry.kind,
      amount: entry.amount,
      description: entry.description,
      occurred_at: formatDateForInput(entry.occurred_at),
      status: entry.status,
      category: entry.category || '',
      subcategory: entry.subcategory || '',
      due_date: formatDateForInput(entry.due_date),
      payment_date: formatDateForInput(entry.payment_date),
      document_number: entry.document_number || '',
      document_type: entry.document_type || '',
      payment_method: entry.payment_method || '',
      notes: entry.notes || '',
    },
  });

  const updateMutation = useMutation({
    mutationFn: async (data: any) => {
      const response = await apiClient.patch(`/financial/entries/${entry.id}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['financial'] });
      onSuccess();
    },
    onError: (error: any) => {
      const status = error.response?.status;
      
      if (status === 422) {
        const details = error.response?.data?.detail;
        if (Array.isArray(details)) {
          details.forEach((err: any) => {
            const field = err.loc?.[1];
            if (field && Object.keys(financialEditSchema.shape).includes(field)) {
              setError(field as any, {
                type: 'manual',
                message: err.msg,
              });
            }
          });
        } else {
          alert('Erro de validação: ' + (error.response?.data?.detail || 'Dados inválidos'));
        }
      } else if (status === 403) {
        alert('Você não tem permissão para editar lançamentos financeiros');
      } else if (status === 400) {
        alert('Dados inválidos: ' + (error.response?.data?.detail || ''));
      } else {
        alert('Erro ao atualizar lançamento: ' + (error.response?.data?.detail || 'Erro desconhecido'));
      }
    },
  });

  const onSubmit = (data: FinancialEditFormData) => {
    const payload: any = {
      kind: data.kind,
      amount: data.amount,
      description: data.description,
      status: data.status,
    };

    if (data.occurred_at) {
      payload.occurred_at = new Date(data.occurred_at).toISOString();
    }

    // Campos profissionais
    if (data.category) payload.category = data.category;
    if (data.subcategory) payload.subcategory = data.subcategory;
    if (data.due_date) payload.due_date = new Date(data.due_date).toISOString();
    if (data.payment_date) payload.payment_date = new Date(data.payment_date).toISOString();
    if (data.document_number) payload.document_number = data.document_number;
    if (data.document_type) payload.document_type = data.document_type;
    if (data.payment_method) payload.payment_method = data.payment_method;
    if (data.notes) payload.notes = data.notes;

    updateMutation.mutate(payload);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 max-h-[70vh] overflow-y-auto px-1">
      {/* ========== DADOS BÁSICOS ========== */}
      <div className="bg-gray-50 p-4 rounded-lg space-y-4">
        <h3 className="font-semibold text-gray-700 text-sm mb-2">📋 Dados Básicos</h3>
        
        <div className="grid grid-cols-2 gap-3">
          {/* Tipo */}
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

          {/* Status */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Status <span className="text-red-500">*</span>
            </label>
            <select
              {...register('status')}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="pending">⏳ Pendente</option>
              <option value="paid">✓ Pago</option>
              <option value="canceled">✕ Cancelado</option>
            </select>
            {errors.status && (
              <p className="mt-1 text-sm text-red-600">{errors.status.message}</p>
            )}
          </div>
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
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Ex: Pagamento de fornecedor XYZ"
          />
          {errors.description && (
            <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
          )}
        </div>
      </div>

      {/* ========== CATEGORIZAÇÃO ========== */}
      <div className="bg-gray-50 p-4 rounded-lg space-y-4">
        <h3 className="font-semibold text-gray-700 text-sm mb-2">🏷️ Categorização</h3>
        
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Categoria
            </label>
            <input
              type="text"
              {...register('category')}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Ex: Vendas, Fornecedores"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Subcategoria
            </label>
            <input
              type="text"
              {...register('subcategory')}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Ex: Produtos, Serviços"
            />
          </div>
        </div>
      </div>

      {/* ========== DATAS ========== */}
      <div className="bg-gray-50 p-4 rounded-lg space-y-4">
        <h3 className="font-semibold text-gray-700 text-sm mb-2">📅 Datas</h3>
        
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Vencimento
            </label>
            <input
              type="date"
              {...register('due_date')}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Pagamento
            </label>
            <input
              type="date"
              {...register('payment_date')}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Ocorrência
            </label>
            <input
              type="date"
              {...register('occurred_at')}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
      </div>

      {/* ========== DOCUMENTO ========== */}
      <div className="bg-gray-50 p-4 rounded-lg space-y-4">
        <h3 className="font-semibold text-gray-700 text-sm mb-2">📄 Documento</h3>
        
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Número
            </label>
            <input
              type="text"
              {...register('document_number')}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Ex: NF-12345"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tipo
            </label>
            <select
              {...register('document_type')}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Selecione...</option>
              <option value="NF-e">NF-e</option>
              <option value="Boleto">Boleto</option>
              <option value="Recibo">Recibo</option>
              <option value="Nota Fiscal">Nota Fiscal</option>
              <option value="Outros">Outros</option>
            </select>
          </div>
        </div>
      </div>

      {/* ========== PAGAMENTO ========== */}
      <div className="bg-gray-50 p-4 rounded-lg space-y-4">
        <h3 className="font-semibold text-gray-700 text-sm mb-2">💳 Forma de Pagamento</h3>
        
        <div>
          <select
            {...register('payment_method')}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">Selecione...</option>
            <option value="pix">PIX</option>
            <option value="dinheiro">Dinheiro</option>
            <option value="cartao_credito">Cartão de Crédito</option>
            <option value="cartao_debito">Cartão de Débito</option>
            <option value="boleto">Boleto</option>
            <option value="transferencia">Transferência Bancária</option>
            <option value="cheque">Cheque</option>
          </select>
        </div>
      </div>

      {/* ========== OBSERVAÇÕES ========== */}
      <div className="bg-gray-50 p-4 rounded-lg space-y-4">
        <h3 className="font-semibold text-gray-700 text-sm mb-2">📝 Observações</h3>
        
        <div>
          <textarea
            {...register('notes')}
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Observações adicionais..."
          />
        </div>
      </div>

      {/* Botões */}
      <div className="flex gap-3 pt-4 sticky bottom-0 bg-white pb-2">
        <button
          type="button"
          onClick={onCancel}
          className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 px-4 py-2 rounded-lg font-medium transition-colors"
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={updateMutation.isPending}
          className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {updateMutation.isPending ? 'Salvando...' : 'Salvar Alterações'}
        </button>
      </div>
    </form>
  );
}
