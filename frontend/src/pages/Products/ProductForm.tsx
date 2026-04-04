import { useForm, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createProduct, updateProduct, Product } from '../../api/products';
import { useState, useEffect, useRef } from 'react';

const productSchema = z.object({
  code: z.string().max(50).optional().or(z.literal('')),
  name: z.string().min(1, 'Nome é obrigatório').max(200),
  category: z.string().max(80).optional().or(z.literal('')),
  subcategoria: z.string().max(80).optional().or(z.literal('')),
  unit: z.string().max(20).optional().or(z.literal('')),
  description: z.string().optional().or(z.literal('')),
  
  // Identificação Estendida
  codigo_barras: z.string().max(50).optional().or(z.literal('')),
  marca: z.string().max(100).optional().or(z.literal('')),
  modelo: z.string().max(100).optional().or(z.literal('')),
  
  // Físico
  peso: z.number().min(0).optional().nullable(),
  dimensoes: z.string().max(100).optional().or(z.literal('')),
  
  // Preços
  cost_price: z.number().min(0).default(0),
  sale_price: z.number().min(0).default(0),
  markup: z.number().min(0).max(1000).optional().nullable(),
  margem_lucro: z.number().min(-100).max(1000).optional().nullable(),
  
  // Estoque
  stock_qty: z.number().min(0).default(0),
  stock_min: z.number().min(0).default(0),
  estoque_maximo: z.number().min(0).optional().nullable(),
  controla_estoque: z.boolean().default(true),
  
  // Relacionamentos
  fornecedor_id: z.string().uuid().optional().nullable().or(z.literal('')),
  observacoes: z.string().optional().or(z.literal('')),
  
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
  const [activeTab, setActiveTab] = useState<'geral' | 'fisico' | 'precos' | 'estoque'>('geral');
  const [flashField, setFlashField] = useState<string | null>(null);
  const debounceTimer = useRef<NodeJS.Timeout | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
    control,
    setValue,
    getValues,
  } = useForm<ProductFormData>({
    resolver: zodResolver(productSchema),
    defaultValues: {
      code: initialData?.code || '',
      name: initialData?.name || '',
      category: initialData?.category || '',
      subcategoria: (initialData as any)?.subcategoria || '',
      unit: initialData?.unit || '',
      description: initialData?.description || '',
      codigo_barras: (initialData as any)?.codigo_barras || '',
      marca: (initialData as any)?.marca || '',
      modelo: (initialData as any)?.modelo || '',
      peso: (initialData as any)?.peso || null,
      dimensoes: (initialData as any)?.dimensoes || '',
      cost_price: initialData?.cost_price ?? 0,
      sale_price: initialData?.sale_price ?? 0,
      markup: (initialData as any)?.markup || null,
      margem_lucro: (initialData as any)?.margem_lucro || null,
      stock_qty: initialData?.stock_qty ?? 0,
      stock_min: initialData?.stock_min ?? 0,
      estoque_maximo: (initialData as any)?.estoque_maximo || null,
      controla_estoque: (initialData as any)?.controla_estoque ?? true,
      fornecedor_id: (initialData as any)?.fornecedor_id || '',
      observacoes: (initialData as any)?.observacoes || '',
      active: initialData?.active ?? true,
    },
  });

  // Watch para cálculos automáticos
  const costPrice = useWatch({ control, name: 'cost_price' });
  const salePrice = useWatch({ control, name: 'sale_price' });
  const markup = useWatch({ control, name: 'markup' });
  const controlaEstoque = useWatch({ control, name: 'controla_estoque' });

  // Função para calcular preço de venda baseado no markup
  const calcularPrecoVenda = () => {
    const custo = getValues('cost_price');
    const markupValor = getValues('markup');
    
    if (custo > 0 && markupValor !== null && markupValor !== undefined && markupValor >= 0) {
      const precoVenda = custo * (1 + markupValor / 100);
      const margem = ((precoVenda - custo) / custo) * 100;
      
      setValue('sale_price', Number(precoVenda.toFixed(2)));
      setValue('margem_lucro', Number(margem.toFixed(2)));
      
      // Visual feedback
      setFlashField('sale_price');
      setTimeout(() => setFlashField(null), 500);
    }
  };

  // Função para calcular markup baseado no preço de venda
  const calcularMarkup = () => {
    const custo = getValues('cost_price');
    const venda = getValues('sale_price');
    
    if (custo > 0 && venda > 0) {
      const markupCalc = ((venda - custo) / custo) * 100;
      const margem = markupCalc; // Margem = Markup para este cálculo
      
      setValue('markup', Number(markupCalc.toFixed(2)));
      setValue('margem_lucro', Number(margem.toFixed(2)));
      
      // Visual feedback
      setFlashField('markup');
      setTimeout(() => setFlashField(null), 500);
    }
  };

  // Debounced auto-calculation quando custo ou markup mudam
  useEffect(() => {
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    debounceTimer.current = setTimeout(() => {
      if (costPrice > 0 && markup !== null && markup !== undefined && markup > 0) {
        calcularPrecoVenda();
      }
    }, 300);

    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, [costPrice, markup]);

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
      } else if (status === 409 && detail?.includes('barras')) {
        setError('codigo_barras', { message: 'Este código de barras já está em uso' });
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

      if (status === 409) {
        if (detail?.includes('código de barras')) {
          setError('codigo_barras', { message: 'Este código de barras já está em uso' });
        } else if (detail?.includes('código')) {
          setError('code', { message: 'Este código já está em uso' });
        }
      } else {
        alert(detail || 'Erro ao atualizar produto');
      }
    },
  });

  const onSubmit = (data: ProductFormData) => {
    // Limpar strings vazias e converter para undefined/null
    const cleanedData = {
      ...data,
      code: data.code?.trim() || undefined,
      category: data.category?.trim() || undefined,
      subcategoria: data.subcategoria?.trim() || undefined,
      unit: data.unit?.trim() || undefined,
      description: data.description?.trim() || undefined,
      codigo_barras: data.codigo_barras?.trim() || undefined,
      marca: data.marca?.trim() || undefined,
      modelo: data.modelo?.trim() || undefined,
      dimensoes: data.dimensoes?.trim() || undefined,
      observacoes: data.observacoes?.trim() || undefined,
      fornecedor_id: data.fornecedor_id?.trim() || undefined,
      peso: data.peso || undefined,
      markup: data.markup || undefined,
      margem_lucro: data.margem_lucro || undefined,
      estoque_maximo: data.estoque_maximo || undefined,
    };

    if (mode === 'create') {
      createMutation.mutate(cleanedData as any);
    } else {
      updateMutation.mutate(cleanedData as any);
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
            onClick={() => setActiveTab('fisico')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'fisico'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Físico
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
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Subcategoria
            </label>
            <input
              {...register('subcategoria')}
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Ex: Notebooks"
            />
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
          </div>

          <div>
            <label className="flex items-center space-x-2 mt-7">
              <input
                {...register('active')}
                type="checkbox"
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">Produto Ativo</span>
            </label>
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
          </div>
        </div>
      )}

      {/* Aba Físico */}
      {activeTab === 'fisico' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Código de Barras
            </label>
            <input
              {...register('codigo_barras')}
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="7891234567890"
              maxLength={50}
            />
            {errors.codigo_barras && (
              <p className="mt-1 text-sm text-red-600">{errors.codigo_barras.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Marca
            </label>
            <input
              {...register('marca')}
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Ex: Dell, HP, Samsung"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Modelo
            </label>
            <input
              {...register('modelo')}
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Ex: Inspiron 15-3000"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Peso (kg)
            </label>
            <input
              {...register('peso', { valueAsNumber: true })}
              type="number"
              step="0.001"
              min="0"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="0.000"
            />
            {errors.peso && (
              <p className="mt-1 text-sm text-red-600">{errors.peso.message}</p>
            )}
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Dimensões
            </label>
            <input
              {...register('dimensoes')}
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Ex: 35x25x2 cm"
            />
            <p className="mt-1 text-xs text-gray-500">Formato: Largura x Altura x Profundidade</p>
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Observações
            </label>
            <textarea
              {...register('observacoes')}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Notas gerais sobre o produto..."
            />
          </div>
        </div>
      )}

      {/* Aba Preços */}
      {activeTab === 'precos' && (
        <div className="space-y-4">
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
                Markup (%)
              </label>
              <input
                {...register('markup', { valueAsNumber: true })}
                type="number"
                step="0.01"
                min="0"
                max="1000"
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors ${
                  flashField === 'markup' ? 'border-green-500 bg-green-50' : 'border-gray-300'
                }`}
                placeholder="0.00"
              />
              {errors.markup && (
                <p className="mt-1 text-sm text-red-600">{errors.markup.message}</p>
              )}
              <p className="mt-1 text-xs text-gray-500">% sobre o preço de custo</p>
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
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors ${
                  flashField === 'sale_price' ? 'border-green-500 bg-green-50' : 'border-gray-300'
                }`}
                placeholder="0.00"
              />
              {errors.sale_price && (
                <p className="mt-1 text-sm text-red-600">{errors.sale_price.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Margem de Lucro (%)
              </label>
              <input
                {...register('margem_lucro', { valueAsNumber: true })}
                type="number"
                step="0.01"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-50"
                placeholder="0.00"
                readOnly
              />
              <p className="mt-1 text-xs text-gray-500">Calculado automaticamente</p>
            </div>
          </div>

          {/* Botões de Cálculo */}
          <div className="flex space-x-3 pt-2">
            <button
              type="button"
              onClick={calcularPrecoVenda}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors text-sm"
            >
              📊 Calcular Preço de Venda (por Markup)
            </button>
            <button
              type="button"
              onClick={calcularMarkup}
              className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors text-sm"
            >
              📈 Calcular Markup (por Preço)
            </button>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
            <p className="text-sm text-blue-800">
              💡 <strong>Dica:</strong> Os cálculos são automáticos (debounce 300ms). 
              Digite o custo e markup para calcular o preço de venda automaticamente.
            </p>
          </div>
        </div>
      )}

      {/* Aba Estoque */}
      {activeTab === 'estoque' && (
        <div className="space-y-4">
          <div>
            <label className="flex items-center space-x-2">
              <input
                {...register('controla_estoque')}
                type="checkbox"
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">Controlar Estoque</span>
            </label>
            <p className="mt-1 text-xs text-gray-500">
              Desmarque para produtos de serviço ou sem controle
            </p>
          </div>

          {controlaEstoque && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
                <p className="mt-1 text-xs text-gray-500">Alerta quando abaixo</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Estoque Máximo
                </label>
                <input
                  {...register('estoque_maximo', { valueAsNumber: true })}
                  type="number"
                  step="0.001"
                  min="0"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="0"
                />
                {errors.estoque_maximo && (
                  <p className="mt-1 text-sm text-red-600">{errors.estoque_maximo.message}</p>
                )}
                <p className="mt-1 text-xs text-gray-500">Limite superior</p>
              </div>
            </div>
          )}

          {!controlaEstoque && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
              <p className="text-sm text-yellow-800">
                ⚠️ Controle de estoque desativado. Os campos de estoque estão ocultos.
              </p>
            </div>
          )}
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
