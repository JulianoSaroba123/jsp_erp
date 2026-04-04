import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createProduct, updateProduct, Product } from '../../api/products';
import { useState } from 'react';

const productSchema = z.object({
  code: z.string().max(50, 'Código deve ter no máximo 50 caracteres').optional().or(z.literal('')),
  name: z.string().min(1, 'Nome é obrigatório').max(200, 'Nome deve ter no máximo 200 caracteres'),
  category: z.string().max(80, 'Categoria deve ter no máximo 80 caracteres').optional().or(z.literal('')),
  unit: z.string().max(20, 'Unidade deve ter no máximo 20 caracteres').optional().or(z.literal('')),
  description: z.string().optional().or(z.literal('')),
  cost_price: z.number().min(0, 'Preço de custo não pode ser negativo').default(0),
  sale_price: z.number().min(0, 'Preço de venda não pode ser negativo').default(0),
  stock_qty: z.number().min(0, 'Estoque não pode ser negativo').default(0),
  stock_min: z.number().min(0, 'Estoque mínimo não pode ser negativo').default(0),
  active: z.boolean().default(true),
});

type ProductFormData = z.infer<typeof productSchema>;

interface ProductFormProps {
  mode: 'create' | 'edit';
  initialData?: Product;
  onSuccess: () => void;
  onCancel: () => void;
}

export function ProductForm({ mode, initialData, onSuccess, onCancel }: ProductFormProps) {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'geral' | 'precos' | 'estoque'>('geral');

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
  } = useForm<ProductFormData>({
    resolver: zodResolver(productSchema),
    defaultValues: {
      code: initialData?.code || '',
      name: initialData?.name || '',
      category: initialData?.category || '',
      unit: initialData?.unit || '',
      description: initialData?.description || '',
      cost_price: initialData?.cost_price ?? 0,
      sale_price: initialData?.sale_price ?? 0,
      stock_qty: initialData?.stock_qty ?? 0,
      stock_min: initialData?.stock_min ?? 0,
      active: initialData?.active ?? true,
    },
  });

  const createMutation = useMutation({
    mutationFn: createProduct,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      onSuccess();
    },
    onError: (error: any) => {
      const status = error.response?.status;
      const detail = error.response?.data?.detail;

      if (status === 409 && detail?.includes('código')) {
        setError('code', { message: 'Este código já está em uso' });
      } else if (status === 422) {
        alert('Dados inválidos. Verifique os campos e tente novamente.');
      } else {
        alert(detail || 'Erro ao criar produto');
      }
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: ProductFormData) => {
      if (!initialData?.id) throw new Error('ID não fornecido');
      return updateProduct(initialData.id, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      onSuccess();
    },
    onError: (error: any) => {
      const status = error.response?.status;
      const detail = error.response?.data?.detail;

      if (status === 409 && detail?.includes('código')) {
        setError('code', { message: 'Este código já está em uso' });
      } else if (status === 404) {
        alert('Produto não encontrado');
      } else if (status === 422) {
        alert('Dados inválidos. Verifique os campos e tente novamente.');
      } else {
        alert(detail || 'Erro ao atualizar produto');
      }
    },
  });

  const onSubmit = (data: ProductFormData) => {
    // Limpar strings vazias para null
    const cleanedData = {
      ...data,
      code: data.code?.trim() || undefined,
      category: data.category?.trim() || undefined,
      unit: data.unit?.trim() || undefined,
      description: data.description?.trim() || undefined,
    };

    if (mode === 'create') {
      createMutation.mutate(cleanedData);
    } else {
      updateMutation.mutate(cleanedData);
    }
  };

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            type="button"
            onClick={() => setActiveTab('geral')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'geral'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Geral
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('precos')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'precos'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Preços
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('estoque')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'estoque'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Estoque
          </button>
        </nav>
      </div>

      {/* Aba Geral */}
      {activeTab === 'geral' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Código <span className="text-gray-400">(opcional)</span>
            </label>
            <input
              {...register('code')}
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Ex: PROD001"
            />
            {errors.code && (
              <p className="mt-1 text-sm text-red-600">{errors.code.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nome <span className="text-red-500">*</span>
            </label>
            <input
              {...register('name')}
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Ex: Notebook Dell Inspiron"
            />
            {errors.name && (
              <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Categoria
            </label>
            <input
              {...register('category')}
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Ex: Informática"
            />
            {errors.category && (
              <p className="mt-1 text-sm text-red-600">{errors.category.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Unidade
            </label>
            <input
              {...register('unit')}
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Ex: un, kg, m, cx"
            />
            {errors.unit && (
              <p className="mt-1 text-sm text-red-600">{errors.unit.message}</p>
            )}
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Descrição
            </label>
            <textarea
              {...register('description')}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Detalhes adicionais do produto..."
            />
            {errors.description && (
              <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
            )}
          </div>

          <div>
            <label className="flex items-center space-x-2">
              <input
                {...register('active')}
                type="checkbox"
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">Produto Ativo</span>
            </label>
          </div>
        </div>
      )}

      {/* Aba Preços */}
      {activeTab === 'precos' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Preço de Custo (R$)
            </label>
            <input
              {...register('cost_price', { valueAsNumber: true })}
              type="number"
              step="0.01"
              min="0"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="0.00"
            />
            {errors.cost_price && (
              <p className="mt-1 text-sm text-red-600">{errors.cost_price.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Preço de Venda (R$)
            </label>
            <input
              {...register('sale_price', { valueAsNumber: true })}
              type="number"
              step="0.01"
              min="0"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="0.00"
            />
            {errors.sale_price && (
              <p className="mt-1 text-sm text-red-600">{errors.sale_price.message}</p>
            )}
          </div>
        </div>
      )}

      {/* Aba Estoque */}
      {activeTab === 'estoque' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Quantidade em Estoque
            </label>
            <input
              {...register('stock_qty', { valueAsNumber: true })}
              type="number"
              step="0.001"
              min="0"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="0"
            />
            {errors.stock_qty && (
              <p className="mt-1 text-sm text-red-600">{errors.stock_qty.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Estoque Mínimo
            </label>
            <input
              {...register('stock_min', { valueAsNumber: true })}
              type="number"
              step="0.001"
              min="0"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="0"
            />
            {errors.stock_min && (
              <p className="mt-1 text-sm text-red-600">{errors.stock_min.message}</p>
            )}
            <p className="mt-1 text-xs text-gray-500">
              Alerta quando o estoque estiver abaixo deste valor
            </p>
          </div>
        </div>
      )}

      {/* Botões de ação */}
      <div className="flex justify-end space-x-3 pt-4 border-t">
        <button
          type="button"
          onClick={onCancel}
          disabled={isPending}
          className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors"
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={isPending}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {isPending ? 'Salvando...' : mode === 'create' ? 'Criar Produto' : 'Salvar Alterações'}
        </button>
      </div>
    </form>
  );
}
