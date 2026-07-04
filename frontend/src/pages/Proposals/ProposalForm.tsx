import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useForm, useFieldArray } from 'react-hook-form';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  createProposal,
  updateProposal,
  getProposalById,
  CreateProposalData,
  UpdateProposalData,
  ProposalItem,
  ProposalProduct,
} from '../../api/proposals';
import { getCustomers, Customer } from '../../api/customers';
import { getProducts, Product } from '../../api/products';

type ProposalTabType = 'basic' | 'values' | 'conditions' | 'items' | 'products';

interface ProposalInstallment {
  installment_number: number;
  due_date: string;
  amount: number;
}

interface ProposalFormData extends CreateProposalData {
  items: ProposalItem[];
  products: ProposalProduct[];
  payment_condition?: 'a_vista' | 'parcelado';
  down_payment?: number;
  installments?: ProposalInstallment[];
}

export const ProposalForm: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isEditMode = !!id;

  const [activeTab, setActiveTab] = useState<ProposalTabType>('basic');
  const [totalAmount, setTotalAmount] = useState(0);

  // Fetch customers for dropdown
  const { data: customersData } = useQuery({
    queryKey: ['customers'],
    queryFn: () => getCustomers(),
  });
  const customers = Array.isArray(customersData) ? customersData : customersData?.items || [];

  // Fetch products for dropdown
  const { data: productsData } = useQuery({
    queryKey: ['products'],
    queryFn: () => getProducts(),
  });
  const products = Array.isArray(productsData) ? productsData : productsData?.items || [];

  // Fetch proposal data if editing
  const { data: proposal, isLoading } = useQuery({
    queryKey: ['proposal', id],
    queryFn: () => getProposalById(id!),
    enabled: isEditMode,
  });

  // Form setup
  const {
    register,
    control,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<ProposalFormData>({
    defaultValues: {
      status: 'rascunho',
      items: [{ description: '', service_type: 'hora', quantity: 1, unit_price: 0, total_price: 0 }],
      products: [],
    },
  });

  // Field arrays for items and products
  const {
    fields: itemFields,
    append: appendItem,
    remove: removeItem,
  } = useFieldArray({
    control,
    name: 'items',
  });

  const {
    fields: productFields,
    append: appendProduct,
    remove: removeProduct,
  } = useFieldArray({
    control,
    name: 'products',
  });

  const {
    fields: installmentFields,
    append: appendInstallment,
    remove: removeInstallment,
  } = useFieldArray({
    control,
    name: 'installments',
  });

  // Tabs configuration (after field arrays are declared)
  const tabs = [
    { id: 'basic' as ProposalTabType, label: 'Dados Básicos', icon: '📋' },
    { id: 'values' as ProposalTabType, label: 'Valores', icon: '💰' },
    { id: 'conditions' as ProposalTabType, label: 'Condições', icon: '📝' },
    { id: 'items' as ProposalTabType, label: 'Itens', icon: '🔧', badge: itemFields.length },
    { id: 'products' as ProposalTabType, label: 'Produtos', icon: '📦', badge: productFields.length },
  ];

  // Watch form values for calculations
  const watchServiceAmount = watch('service_amount');
  const watchPartsAmount = watch('parts_amount');
  const watchDiscountAmount = watch('discount_amount');
  const watchItems = watch('items');
  const watchProducts = watch('products');

  // Load proposal data when editing
  useEffect(() => {
    if (proposal && isEditMode) {
      Object.keys(proposal).forEach((key) => {
        if (key !== 'items' && key !== 'products') {
          setValue(key as any, proposal[key as keyof typeof proposal]);
        }
      });
      
      if (proposal.items && proposal.items.length > 0) {
        setValue('items', proposal.items);
      }
      
      if (proposal.products && proposal.products.length > 0) {
        setValue('products', proposal.products);
      }
    }
  }, [proposal, isEditMode, setValue]);

  // Calculate item total
  const calculateItemTotal = (quantity: number, unitPrice: number) => {
    return quantity * unitPrice;
  };

  // Calculate product total
  const calculateProductTotal = (quantity: number, unitPrice: number) => {
    return quantity * unitPrice;
  };

  // Calculate total amount
  useEffect(() => {
    const serviceAmount = parseFloat(watchServiceAmount?.toString() || '0');
    const partsAmount = parseFloat(watchPartsAmount?.toString() || '0');
    const discountAmount = parseFloat(watchDiscountAmount?.toString() || '0');
    
    const total = serviceAmount + partsAmount - discountAmount;
    setTotalAmount(total > 0 ? total : 0);
  }, [watchServiceAmount, watchPartsAmount, watchDiscountAmount]);

  // Update item total when quantity or unit price changes
  useEffect(() => {
    watchItems?.forEach((item, index) => {
      const total = calculateItemTotal(item.quantity || 0, item.unit_price || 0);
      if (item.total_price !== total) {
        setValue(`items.${index}.total_price`, total);
      }
    });
  }, [watchItems, setValue]);

  // Update product total when quantity or unit price changes
  useEffect(() => {
    watchProducts?.forEach((product, index) => {
      const total = calculateProductTotal(product.quantity || 0, product.unit_price || 0);
      if (product.total_price !== total) {
        setValue(`products.${index}.total_price`, total);
      }
    });
  }, [watchProducts, setValue]);

  // Create mutation
  const createMutation = useMutation({
    mutationFn: createProposal,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposals'] });
      alert('✅ Proposta criada com sucesso!');
      navigate('/proposals');
    },
    onError: (error: any) => {
      console.error('Erro ao criar proposta:', error);
      alert(`❌ Erro ao criar proposta: ${error.response?.data?.detail || error.message}`);
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (data: UpdateProposalData) => updateProposal(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposals'] });
      queryClient.invalidateQueries({ queryKey: ['proposal', id] });
      alert('✅ Proposta atualizada com sucesso!');
      navigate('/proposals');
    },
    onError: (error: any) => {
      console.error('Erro ao atualizar proposta:', error);
      alert(`❌ Erro ao atualizar proposta: ${error.response?.data?.detail || error.message}`);
    },
  });

  // Form submission
  const onSubmit = (data: ProposalFormData) => {
    // Clean up data
    const submitData: CreateProposalData = {
      ...data,
      service_amount: parseFloat(data.service_amount?.toString() || '0'),
      parts_amount: parseFloat(data.parts_amount?.toString() || '0'),
      discount_amount: parseFloat(data.discount_amount?.toString() || '0'),
      items: data.items.map((item) => ({
        ...item,
        quantity: parseFloat(item.quantity?.toString() || '0'),
        unit_price: parseFloat(item.unit_price?.toString() || '0'),
        total_price: parseFloat(item.total_price?.toString() || '0'),
      })),
      products: data.products.map((product) => ({
        ...product,
        quantity: parseFloat(product.quantity?.toString() || '0'),
        unit_price: parseFloat(product.unit_price?.toString() || '0'),
        total_price: parseFloat(product.total_price?.toString() || '0'),
      })),
    };

    if (isEditMode) {
      updateMutation.mutate(submitData);
    } else {
      createMutation.mutate(submitData);
    }
  };

  if (isEditMode && isLoading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-gray-600">Carregando proposta...</div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
          {isEditMode ? '✏️ Editar Proposta' : '➕ Nova Proposta'}
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          {isEditMode
            ? 'Atualize as informações da proposta'
            : 'Preencha os dados para criar uma nova proposta comercial'}
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-700 mb-6">
        <nav className="-mb-px flex space-x-2 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`
                whitespace-nowrap py-3 px-4 border-b-2 font-medium text-sm transition-colors
                ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
                }
              `}
            >
              {tab.icon} {tab.label}
              {tab.badge !== undefined && tab.badge > 0 && (
                <span className="ml-2 bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300 py-0.5 px-2 rounded-full text-xs">
                  {tab.badge}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Informações Básicas */}
        {activeTab === 'basic' && (
          <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">📋 Informações Básicas</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Customer */}
            <div>
              <label htmlFor="customer_id" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Cliente *
              </label>
              <select
                id="customer_id"
                {...register('customer_id', { required: 'Cliente é obrigatório' })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="">Selecione um cliente</option>
                {customers.map((customer: Customer) => (
                  <option key={customer.id} value={customer.id}>
                    {customer.name}
                  </option>
                ))}
              </select>
              {errors.customer_id && (
                <p className="text-red-600 dark:text-red-400 text-sm mt-1">{errors.customer_id.message}</p>
              )}
            </div>

            {/* Status */}
            <div>
              <label htmlFor="status" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Status
              </label>
              <select
                id="status"
                {...register('status')}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="rascunho">🔒 Rascunho</option>
                <option value="enviada">📤 Enviada</option>
                <option value="aprovada">✅ Aprovada</option>
                <option value="rejeitada">❌ Rejeitada</option>
                <option value="cancelada">🚫 Cancelada</option>
              </select>
            </div>

            {/* Title */}
            <div className="md:col-span-2">
              <label htmlFor="title" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Título *
              </label>
              <input
                id="title"
                type="text"
                {...register('title', { required: 'Título é obrigatório' })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="Ex: Desenvolvimento de Sistema Web"
              />
              {errors.title && <p className="text-red-600 dark:text-red-400 text-sm mt-1">{errors.title.message}</p>}
            </div>

            {/* Description */}
            <div className="md:col-span-2">
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Descrição
              </label>
              <textarea
                id="description"
                {...register('description')}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="Descreva os detalhes da proposta..."
              />
            </div>

            {/* Observations */}
            <div className="md:col-span-2">
              <label htmlFor="observations" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Observações
              </label>
              <textarea
                id="observations"
                {...register('observations')}
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="Informações adicionais..."
              />
            </div>
          </div>
        </div>
        )}

        {/* Valores */}
        {activeTab === 'values' && (
          <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">💰 Valores</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="service_amount" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Valor de Serviços (R$)
              </label>
              <input
                id="service_amount"
                type="number"
                step="0.01"
                {...register('service_amount')}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="0.00"
              />
            </div>

            <div>
              <label htmlFor="parts_amount" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Valor de Peças/Produtos (R$)
              </label>
              <input
                id="parts_amount"
                type="number"
                step="0.01"
                {...register('parts_amount')}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="0.00"
              />
            </div>

            <div>
              <label htmlFor="discount_amount" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Desconto (R$)
              </label>
              <input
                id="discount_amount"
                type="number"
                step="0.01"
                {...register('discount_amount')}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="0.00"
              />
            </div>

            <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg border border-blue-200 dark:border-blue-800">
              <label className="block text-sm font-medium text-blue-900 dark:text-blue-100 mb-1">
                Total da Proposta
              </label>
              <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                R$ {totalAmount.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
            </div>
          </div>
        </div>
        )}

        {/* Condições */}
        {activeTab === 'conditions' && (
          <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">📋 Condições</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label htmlFor="payment_condition" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Condição de Pagamento
              </label>
              <select
                id="payment_condition"
                {...register('payment_condition')}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="a_vista">À Vista</option>
                <option value="parcelado">Parcelado</option>
              </select>
            </div>

            <div>
              <label htmlFor="delivery_days" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Prazo de Entrega
              </label>
              <input
                id="delivery_days"
                type="text"
                {...register('delivery_days')}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="Ex: 30 dias"
              />
            </div>

            <div>
              <label htmlFor="warranty_days" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Garantia
              </label>
              <input
                id="warranty_days"
                type="text"
                {...register('warranty_days')}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="Ex: 90 dias"
              />
            </div>

            <div>
              <label htmlFor="issue_date" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Data de Emissão
              </label>
              <input
                id="issue_date"
                type="date"
                {...register('issue_date')}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              />
            </div>

            <div>
              <label htmlFor="validity_date" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Validade
              </label>
              <input
                id="validity_date"
                type="date"
                {...register('validity_date')}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              />
            </div>
          </div>

          {/* Installments Section - Show only when "Parcelado" is selected */}
          {watch('payment_condition') === 'parcelado' && (
            <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
              {/* Down Payment / Entrada */}
              <div className="mb-6 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                <label htmlFor="down_payment" className="block text-sm font-semibold text-yellow-900 dark:text-yellow-100 mb-2">
                  💰 Valor de Entrada (Opcional)
                </label>
                <input
                  id="down_payment"
                  type="number"
                  step="0.01"
                  {...register('down_payment', { valueAsNumber: true })}
                  className="w-full md:w-1/3 px-3 py-2 border border-yellow-300 dark:border-yellow-700 rounded-md focus:ring-yellow-500 focus:border-yellow-500 bg-white dark:bg-gray-700 dark:text-white"
                  placeholder="0.00"
                />
                <p className="text-xs text-yellow-700 dark:text-yellow-300 mt-1">
                  Informe o valor pago como entrada. O restante será dividido nas parcelas.
                </p>
              </div>

              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">💳 Parcelas</h3>
                <button
                  type="button"
                  onClick={() => {
                    const nextNumber = installmentFields.length + 1;
                    const today = new Date();
                    today.setMonth(today.getMonth() + nextNumber);
                    const downPayment = watch('down_payment') || 0;
                    const remainingAmount = totalAmount - downPayment;
                    const averageAmount = remainingAmount / (installmentFields.length + 1);
                    appendInstallment({
                      installment_number: nextNumber,
                      due_date: today.toISOString().split('T')[0],
                      amount: parseFloat(averageAmount.toFixed(2)),
                    });
                  }}
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors text-sm"
                >
                  ➕ Adicionar Parcela
                </button>
              </div>

              {installmentFields.length === 0 ? (
                <div className="text-center text-gray-500 dark:text-gray-400 py-6 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg">
                  <p>Nenhuma parcela adicionada</p>
                  <p className="text-sm mt-1">Clique em "Adicionar Parcela" para começar</p>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="grid grid-cols-12 gap-3 text-sm font-semibold text-gray-700 dark:text-gray-300 px-2">
                    <div className="col-span-2">Parcela</div>
                    <div className="col-span-4">Vencimento</div>
                    <div className="col-span-5">Valor (R$)</div>
                    <div className="col-span-1"></div>
                  </div>
                  {installmentFields.map((field, index) => (
                    <div key={field.id} className="grid grid-cols-12 gap-3 items-center border border-gray-200 dark:border-gray-700 rounded-md p-3 bg-gray-50 dark:bg-gray-800">
                      <div className="col-span-2">
                        <input
                          type="number"
                          {...register(`installments.${index}.installment_number` as const)}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 dark:text-white"
                          readOnly
                        />
                      </div>
                      <div className="col-span-4">
                        <input
                          type="date"
                          {...register(`installments.${index}.due_date` as const)}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                        />
                      </div>
                      <div className="col-span-5">
                        <input
                          type="number"
                          step="0.01"
                          {...register(`installments.${index}.amount` as const)}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                        />
                      </div>
                      <div className="col-span-1">
                        <button
                          type="button"
                          onClick={() => removeInstallment(index)}
                          className="w-full px-2 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
                          title="Remover parcela"
                        >
                          🗑️
                        </button>
                      </div>
                    </div>
                  ))}
                  
                  <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                    <div className="space-y-2">
                      {(watch('down_payment') || 0) > 0 && (
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                            💰 Entrada:
                          </span>
                          <span className="text-lg font-semibold text-yellow-600 dark:text-yellow-400">
                            R$ {(watch('down_payment') || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </span>
                        </div>
                      )}
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          💳 Total das Parcelas:
                        </span>
                        <span className="text-lg font-bold text-blue-600 dark:text-blue-400">
                          R$ {installmentFields.reduce((sum, _, i) => {
                            const amount = watch(`installments.${i}.amount` as const) || 0;
                            return sum + parseFloat(amount.toString());
                          }, 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </span>
                      </div>
                      <div className="flex justify-between items-center pt-2 border-t border-gray-300 dark:border-gray-600">
                        <span className="text-base font-semibold text-gray-900 dark:text-gray-100">
                          📊 Total da Proposta:
                        </span>
                        <span className="text-xl font-bold text-gray-900 dark:text-gray-100">
                          R$ {totalAmount.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
        )}

        {/* Itens de Serviço */}
        {activeTab === 'items' && (
          <div className="space-y-4">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">🔧 Itens de Serviço</h3>
            <button
              type="button"
              onClick={() =>
                appendItem({
                  description: '',
                  service_type: 'hora',
                  quantity: 1,
                  unit_price: 0,
                  total_price: 0,
                })
              }
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              ➕ Adicionar Item
            </button>
          </div>

          <div className="space-y-4">
            {itemFields.map((field, index) => (
              <div key={field.id} className="border-2 border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <div className="grid grid-cols-1 md:grid-cols-12 gap-3">
                  <div className="md:col-span-4">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Descrição
                    </label>
                    <input
                      type="text"
                      {...register(`items.${index}.description` as const)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                      placeholder="Ex: Desenvolvimento Backend"
                    />
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Tipo
                    </label>
                    <select
                      {...register(`items.${index}.service_type` as const)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                    >
                      <option value="hora">Hora</option>
                      <option value="dia">Dia</option>
                      <option value="fechado">Fechado</option>
                    </select>
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Quantidade
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      {...register(`items.${index}.quantity` as const)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                    />
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Preço Unit. (R$)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      {...register(`items.${index}.unit_price` as const)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                    />
                  </div>

                  <div className="md:col-span-1">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Total
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      {...register(`items.${index}.total_price` as const)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-gray-200 dark:bg-gray-600 dark:text-white"
                      readOnly
                    />
                  </div>

                  <div className="md:col-span-1 flex items-end">
                    <button
                      type="button"
                      onClick={() => removeItem(index)}
                      className="w-full px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
                      title="Remover item"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              </div>
            ))}

            {itemFields.length === 0 && (
              <div className="text-center text-gray-500 dark:text-gray-400 py-8 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg">
                <p>Nenhum item adicionado</p>
                <p className="text-sm mt-1">Clique em "Adicionar Item" para começar</p>
              </div>
            )}
          </div>
        </div>
        )}

        {/* Produtos */}
        {activeTab === 'products' && (
          <div className="space-y-4">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">📦 Produtos</h3>
            <button
              type="button"
              onClick={() =>
                appendProduct({
                  product_id: undefined,
                  description: '',
                  quantity: 1,
                  unit_price: 0,
                  total_price: 0,
                })
              }
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors text-sm"
            >
              ➕ Adicionar Produto
            </button>
          </div>

          <div className="space-y-4">
            {productFields.map((field, index) => (
              <div key={field.id} className="border-2 border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <div className="grid grid-cols-1 md:grid-cols-12 gap-3">
                  <div className="md:col-span-3">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Produto (Opcional)
                    </label>
                    <select
                      {...register(`products.${index}.product_id` as const)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                    >
                      <option value="">Nenhum (descrição manual)</option>
                      {products.map((product: Product) => (
                        <option key={product.id} value={product.id}>
                          {product.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="md:col-span-4">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Descrição
                    </label>
                    <input
                      type="text"
                      {...register(`products.${index}.description` as const)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                      placeholder="Ex: Licença de software"
                    />
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Quantidade
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      {...register(`products.${index}.quantity` as const)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                    />
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Preço Unit. (R$)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      {...register(`products.${index}.unit_price` as const)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                    />
                  </div>

                  <div className="md:col-span-1 flex items-end">
                    <button
                      type="button"
                      onClick={() => removeProduct(index)}
                      className="w-full px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
                      title="Remover produto"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              </div>
            ))}

            {productFields.length === 0 && (
              <div className="text-center text-gray-500 dark:text-gray-400 py-8 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg">
                <p>Nenhum produto adicionado</p>
                <p className="text-sm mt-1">Clique em "Adicionar Produto" para começar</p>
              </div>
            )}
          </div>
        </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-4">
          <button
            type="button"
            onClick={() => navigate('/proposals')}
            className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={createMutation.isPending || updateMutation.isPending}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {createMutation.isPending || updateMutation.isPending
              ? '⏳ Salvando...'
              : isEditMode
              ? '💾 Atualizar Proposta'
              : '✅ Criar Proposta'}
          </button>
        </div>
      </form>
    </div>
  );
};
