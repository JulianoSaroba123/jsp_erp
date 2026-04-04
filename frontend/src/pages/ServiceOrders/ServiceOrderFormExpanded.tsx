import { useState } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createServiceOrder, updateServiceOrder } from '../../api/serviceOrders';
import { getCustomers } from '../../api/customers';
import { getProducts } from '../../api/products';

// Schema expandido com todos os campos
const serviceOrderSchema = z.object({
  customer_id: z.string().uuid('Selecione um cliente'),
  // Campos de tipo de OS
  tipo_ordem: z.enum(['atendimento', 'projeto']).default('atendimento'),
  exibir_valores: z.boolean().optional(),
  proposta_id: z.string().uuid().optional(),
  percentual_concluido: z.number().min(0).max(100).default(0),
  etapa_atual: z.string().optional(),
  // Dados básicos
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
  technical_diagnosis: z.string().optional(),
  solution: z.string().optional(),
  notes: z.string().optional(),
  warranty_days: z.number().min(0).optional(),
  payment_condition: z.enum(['a_vista', 'parcelado']).default('a_vista'),
  discount_amount: z.number().min(0).optional(),
  // Arrays para entidades relacionadas
  items: z.array(z.object({
    description: z.string().min(1, 'Descrição obrigatória'),
    service_type: z.enum(['hora', 'dia', 'fechado']),
    quantity: z.number().min(0.01),
    unit_price: z.number().min(0),
  })).optional(),
  products: z.array(z.object({
    product_id: z.string().uuid().optional(),
    description: z.string().min(1),
    quantity: z.number().min(0.001),
    unit_price: z.number().min(0),
  })).optional(),
  installments: z.array(z.object({
    installment_number: z.number().min(1),
    due_date: z.string(),
    amount: z.number().min(0.01),
    paid: z.boolean().optional(),
    payment_date: z.string().optional(),
  })).optional(),
});

type ServiceOrderFormData = z.infer<typeof serviceOrderSchema>;

interface ServiceOrderFormProps {
  mode: 'create' | 'edit';
  initialData?: any;
  onSuccess: () => void;
  onCancel: () => void;
}

type TabType = 'basic' | 'equipment' | 'services' | 'products' | 'payment' | 'attachments';

export function ServiceOrderFormExpanded({ mode, initialData, onSuccess, onCancel }: ServiceOrderFormProps) {
  const [activeTab, setActiveTab] = useState<TabType>('basic');
  const queryClient = useQueryClient();

  // Carregar clientes
  const { data: customersData } = useQuery({
    queryKey: ['customers', 1, 100],
    queryFn: () => getCustomers({ page: 1, page_size: 100 }),
  });

  // Carregar produtos
  const { data: productsData } = useQuery({
    queryKey: ['products', 1, 200],
    queryFn: () => getProducts({ page: 1, page_size: 200 }),
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    setValue,
    control,
  } = useForm<ServiceOrderFormData>({
    resolver: zodResolver(serviceOrderSchema),
    defaultValues: {
      tipo_ordem: 'atendimento',
      exibir_valores: true,
      percentual_concluido: 0,
      priority: 'normal',
      payment_condition: 'a_vista',
      warranty_days: 90,
      discount_amount: 0,
      items: [],
      products: [],
      installments: [],
    },
  });

  // Field arrays para listas dinâmicas
  const { fields: itemsFields, append: appendItem, remove: removeItem } = useFieldArray({
    control,
    name: 'items',
  });

  const { fields: productsFields, append: appendProduct, remove: removeProduct } = useFieldArray({
    control,
    name: 'products',
  });

  const { fields: installmentsFields, append: appendInstallment, remove: removeInstallment } = useFieldArray({
    control,
    name: 'installments',
  });

  // Watch para cálculos automáticos
  const items = watch('items') || [];
  const products = watch('products') || [];
  const discountAmount = watch('discount_amount') || 0;
  const tipoOrdem = watch('tipo_ordem');

  // Calcular totais
  const serviceAmount = items.reduce((sum, item) => {
    return sum + (item.quantity || 0) * (item.unit_price || 0);
  }, 0);

  const partsAmount = products.reduce((sum, product) => {
    return sum + (product.quantity || 0) * (product.unit_price || 0);
  }, 0);

  const totalAmount = serviceAmount + partsAmount - discountAmount;

  // Mutations
  const createMutation = useMutation({
    mutationFn: createServiceOrder,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['service-orders'] });
      onSuccess();
    },
    onError: (error: any) => {
      const status = error.response?.status;
      if (status === 422) {
        alert('Erro de validação. Verifique os campos obrigatórios.');
      } else if (status === 403) {
        alert('Você não tem permissão para criar ordens de serviço');
      } else {
        alert(error.response?.data?.detail || 'Erro ao criar ordem de serviço');
      }
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => updateServiceOrder(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['service-orders'] });
      queryClient.invalidateQueries({ queryKey: ['service-order', initialData?.id] });
      onSuccess();
    },
    onError: (error: any) => {
      const status = error.response?.status;
      if (status === 404) {
        alert('Ordem de serviço não encontrada');
      } else if (status === 403) {
        alert('Você não tem permissão para editar esta ordem de serviço');
      } else {
        alert(error.response?.data?.detail || 'Erro ao atualizar ordem de serviço');
      }
    },
  });

  const onSubmit = (data: ServiceOrderFormData) => {
    const payload = {
      ...data,
      // Adicionar total_price aos items
      items: data.items?.map(item => ({
        ...item,
        total_price: item.quantity * item.unit_price,
      })),
      // Adicionar total_price aos products
      products: data.products?.map(product => ({
        ...product,
        total_price: product.quantity * product.unit_price,
      })),
      // Adicionar paid aos installments
      installments: data.installments?.map(installment => ({
        ...installment,
        paid: installment.paid ?? false,
        payment_date: installment.payment_date || undefined,
      })),
      service_amount: serviceAmount,
      parts_amount: partsAmount,
      total_amount: totalAmount,
    };

    if (mode === 'create') {
      createMutation.mutate(payload);
    } else if (initialData?.id) {
      updateMutation.mutate({ id: initialData.id, data: payload });
    }
  };

  const isLoading = createMutation.isPending || updateMutation.isPending;

  // Tabs configuration
  const tabs = [
    { id: 'basic' as TabType, label: '📋 Dados Básicos', icon: '📋' },
    { id: 'equipment' as TabType, label: '🖥️ Equipamento', icon: '🖥️' },
    { id: 'services' as TabType, label: '🔧 Serviços', icon: '🔧', badge: itemsFields.length },
    { id: 'products' as TabType, label: '📦 Produtos/Peças', icon: '📦', badge: productsFields.length },
    { id: 'payment' as TabType, label: '💰 Pagamento', icon: '💰' },
    { id: 'attachments' as TabType, label: '📎 Anexos', icon: '📎' },
  ];

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Tabs Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-2 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`
                whitespace-nowrap py-3 px-4 border-b-2 font-medium text-sm transition-colors
                ${activeTab === tab.id
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
                }
              `}
            >
              {tab.icon} {tab.label.replace(tab.icon + ' ', '')}
              {tab.badge !== undefined && tab.badge > 0 && (
                <span className="ml-2 bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300 py-0.5 px-2 rounded-full text-xs">
                  {tab.badge}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="py-4">
        {/* Aba 1: Dados Básicos */}
        {activeTab === 'basic' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
              📋 Informações Básicas
            </h3>
            
            {/* TIPO DE ORDEM DE SERVIÇO - DESTAQUE */}
            <div className="p-4 bg-gradient-to-r from-purple-50 to-teal-50 dark:from-purple-900/20 dark:to-teal-900/20 border-2 border-purple-200 dark:border-purple-800 rounded-lg">
              <label className="block text-sm font-bold text-gray-900 dark:text-gray-100 mb-2">
                🎯 Tipo de Ordem de Serviço *
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <label className="flex items-center space-x-3 p-3 border-2 border-gray-300 dark:border-gray-600 rounded-md cursor-pointer hover:bg-purple-50 dark:hover:bg-purple-900/30 has-[:checked]:border-purple-500 has-[:checked]:bg-purple-100 dark:has-[:checked]:bg-purple-900/50">
                  <input
                    type="radio"
                    {...register('tipo_ordem')}
                    value="atendimento"
                    className="w-4 h-4 text-purple-600"
                  />
                  <div>
                    <div className="font-semibold text-gray-900 dark:text-gray-100">🚨 Atendimento / Chamado</div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">Emergencial • Valores visíveis • Cobrança</div>
                  </div>
                </label>
                <label className="flex items-center space-x-3 p-3 border-2 border-gray-300 dark:border-gray-600 rounded-md cursor-pointer hover:bg-teal-50 dark:hover:bg-teal-900/30 has-[:checked]:border-teal-500 has-[:checked]:bg-teal-100 dark:has-[:checked]:bg-teal-900/50">
                  <input
                    type="radio"
                    {...register('tipo_ordem')}
                    value="projeto"
                    className="w-4 h-4 text-teal-600"
                  />
                  <div>
                    <div className="font-semibold text-gray-900 dark:text-gray-100">📋 Projeto / Serviço Fechado</div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">Proposta aprovada • Sem valores no relatório</div>
                  </div>
                </label>
              </div>
              {tipoOrdem === 'projeto' && (
                <div className="mt-3 p-3 bg-teal-50 dark:bg-teal-900/30 border border-teal-300 dark:border-teal-700 rounded-md">
                  <p className="text-sm text-teal-800 dark:text-teal-200">
                    💡 <strong>OS de Projeto:</strong> Serve para acompanhamento de execução. Valores não aparecem no relatório operacional.
                  </p>
                </div>
              )}
              {errors.tipo_ordem && (
                <p className="mt-2 text-sm text-red-600 dark:text-red-400">{errors.tipo_ordem.message}</p>
              )}
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Cliente */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Cliente *
                </label>
                <select
                  {...register('customer_id')}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                >
                  <option value="">Selecione um cliente</option>
                  {customersData?.items.map((customer) => (
                    <option key={customer.id} value={customer.id}>
                      {customer.name} {customer.cpf_cnpj ? `- ${customer.cpf_cnpj}` : ''}
                    </option>
                  ))}
                </select>
                {errors.customer_id && (
                  <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.customer_id.message}</p>
                )}
              </div>

              {/* Prioridade */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Prioridade
                </label>
                <select
                  {...register('priority')}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                >
                  <option value="baixa">Baixa</option>
                  <option value="normal">Normal</option>
                  <option value="alta">Alta</option>
                  <option value="urgente">Urgente</option>
                </select>
              </div>
            </div>

            {/* Título */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Título *
              </label>
              <input
                type="text"
                {...register('title')}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="Ex: Manutenção preventiva"
              />
              {errors.title && (
                <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.title.message}</p>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Solicitante */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Solicitante
                </label>
                <input
                  type="text"
                  {...register('requester')}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="Nome do solicitante"
                />
              </div>

              {/* Técnico */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Técnico Responsável
                </label>
                <input
                  type="text"
                  {...register('technician')}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="Nome do técnico"
                />
              </div>
            </div>

            {/* Data Prevista */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Data Prevista de Conclusão
              </label>
              <input
                type="date"
                {...register('expected_date')}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              />
            </div>

            {/* CAMPOS ESPECÍFICOS DE OS DE PROJETO */}
            {tipoOrdem === 'projeto' && (
              <div className="p-4 bg-teal-50 dark:bg-teal-900/20 border-2 border-teal-300 dark:border-teal-700 rounded-lg space-y-4">
                <h4 className="font-semibold text-teal-900 dark:text-teal-100 flex items-center gap-2">
                  📊 Andamento do Projeto
                </h4>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Percentual Concluído */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Percentual Concluído (%)
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      {...register('percentual_concluido', { valueAsNumber: true })}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-teal-500 focus:border-teal-500 dark:bg-gray-700 dark:text-white"
                      placeholder="0"
                    />
                  </div>
                  
                  {/* Etapa Atual */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Etapa Atual
                    </label>
                    <input
                      type="text"
                      {...register('etapa_atual')}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-teal-500 focus:border-teal-500 dark:bg-gray-700 dark:text-white"
                      placeholder="Ex: Instalação de cabos"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Descrição */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Descrição Geral
              </label>
              <textarea
                {...register('description')}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="Descrição detalhada do serviço..."
              />
            </div>

            {/* Problema Relatado */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Problema Relatado pelo Cliente
              </label>
              <textarea
                {...register('problem_description')}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="O que o cliente relatou..."
              />
            </div>
          </div>
        )}

        {/* Aba 2: Equipamento */}
        {activeTab === 'equipment' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
              🖥️ Informações do Equipamento
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Equipamento */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Equipamento
                </label>
                <input
                  type="text"
                  {...register('equipment')}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="Ex: Notebook Dell"
                />
              </div>

              {/* Marca/Modelo */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Marca/Modelo
                </label>
                <input
                  type="text"
                  {...register('brand_model')}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="Ex: Dell Inspiron 15"
                />
              </div>
            </div>

            {/* Número de Série */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Número de Série / Patrimônio
              </label>
              <input
                type="text"
                {...register('serial_number')}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="Ex: SN123456789"
              />
            </div>

            {/* Defeito Relatado */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Defeito Relatado
              </label>
              <textarea
                {...register('reported_defect')}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="Sintomas e problemas apresentados..."
              />
            </div>

            {/* Diagnóstico Técnico */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Diagnóstico Técnico
              </label>
              <textarea
                {...register('technical_diagnosis')}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="Diagnóstico realizado pelo técnico..."
              />
            </div>

            {/* Solução Aplicada */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Solução Aplicada
              </label>
              <textarea
                {...register('solution')}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="Como o problema foi resolvido..."
              />
            </div>

            {/* Observações */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Observações Adicionais
              </label>
              <textarea
                {...register('notes')}
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="Notas, avisos, condições especiais..."
              />
            </div>
          </div>
        )}

        {/* Aba 3: Serviços */}
        {activeTab === 'services' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                🔧 Serviços Executados
              </h3>
              <button
                type="button"
                onClick={() => appendItem({ description: '', service_type: 'hora', quantity: 1, unit_price: 0 })}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm"
              >
                + Adicionar Serviço
              </button>
            </div>

            {itemsFields.length === 0 ? (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg">
                <p>Nenhum serviço adicionado</p>
                <p className="text-sm mt-1">Clique em "Adicionar Serviço" para começar</p>
              </div>
            ) : (
              <div className="space-y-3">
                {itemsFields.map((field, index) => (
                  <div key={field.id} className="p-4 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-800">
                    <div className="flex justify-between items-start mb-3">
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Serviço #{index + 1}</span>
                      <button
                        type="button"
                        onClick={() => removeItem(index)}
                        className="text-red-600 hover:text-red-800 dark:text-red-400 text-sm"
                      >
                        🗑️ Remover
                      </button>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                      <div className="md:col-span-2">
                        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Descrição *
                        </label>
                        <input
                          type="text"
                          {...register(`items.${index}.description`)}
                          className="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                          placeholder="Ex: Formatação e instalação de sistema"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Tipo
                        </label>
                        <select
                          {...register(`items.${index}.service_type`)}
                          className="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                        >
                          <option value="hora">Por Hora</option>
                          <option value="dia">Por Dia</option>
                          <option value="fechado">Valor Fechado</option>
                        </select>
                      </div>
                      
                      <div>
                        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Quantidade
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          {...register(`items.${index}.quantity`, { valueAsNumber: true })}
                          className="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Valor Unitário (R$)
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          {...register(`items.${index}.unit_price`, { valueAsNumber: true })}
                          className="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Total
                        </label>
                        <div className="px-2 py-1.5 text-sm bg-gray-200 dark:bg-gray-600 rounded-md text-gray-900 dark:text-gray-100 font-medium">
                          R$ {((watch(`items.${index}.quantity`) || 0) * (watch(`items.${index}.unit_price`) || 0)).toFixed(2)}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Total de Serviços */}
            <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
              <div className="flex justify-between items-center">
                <span className="font-semibold text-gray-900 dark:text-gray-100">Total de Serviços:</span>
                <span className="text-xl font-bold text-blue-600 dark:text-blue-400">
                  R$ {serviceAmount.toFixed(2)}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Aba 4: Produtos/Peças */}
        {activeTab === 'products' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                📦 Produtos e Peças Utilizadas
              </h3>
              <button
                type="button"
                onClick={() => appendProduct({ description: '', quantity: 1, unit_price: 0 })}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm"
              >
                + Adicionar Produto
              </button>
            </div>

            {productsFields.length === 0 ? (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg">
                <p>Nenhum produto adicionado</p>
                <p className="text-sm mt-1">Clique em "Adicionar Produto" para começar</p>
              </div>
            ) : (
              <div className="space-y-3">
                {productsFields.map((field, index) => (
                  <div key={field.id} className="p-4 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-800">
                    <div className="flex justify-between items-start mb-3">
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Produto #{index + 1}</span>
                      <button
                        type="button"
                        onClick={() => removeProduct(index)}
                        className="text-red-600 hover:text-red-800 dark:text-red-400 text-sm"
                      >
                        🗑️ Remover
                      </button>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                      <div className="md:col-span-2">
                        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Produto *
                        </label>
                        <select
                          {...register(`products.${index}.product_id`)}
                          onChange={(e) => {
                            const product = productsData?.items.find(p => p.id === e.target.value);
                            if (product) {
                              setValue(`products.${index}.description`, product.name);
                              setValue(`products.${index}.unit_price`, product.sale_price);
                            }
                          }}
                          className="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                        >
                          <option value="">Selecione ou digite abaixo</option>
                          {productsData?.items.map((product) => (
                            <option key={product.id} value={product.id}>
                              {product.name} - R$ {product.sale_price.toFixed(2)}
                            </option>
                          ))}
                        </select>
                      </div>
                      
                      <div className="md:col-span-2">
                        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Descrição *
                        </label>
                        <input
                          type="text"
                          {...register(`products.${index}.description`)}
                          className="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                          placeholder="Ex: Cabo HDMI 2m"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Quantidade
                        </label>
                        <input
                          type="number"
                          step="0.001"
                          {...register(`products.${index}.quantity`, { valueAsNumber: true })}
                          className="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Valor Unitário (R$)
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          {...register(`products.${index}.unit_price`, { valueAsNumber: true })}
                          className="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Total
                        </label>
                        <div className="px-2 py-1.5 text-sm bg-gray-200 dark:bg-gray-600 rounded-md text-gray-900 dark:text-gray-100 font-medium">
                          R$ {((watch(`products.${index}.quantity`) || 0) * (watch(`products.${index}.unit_price`) || 0)).toFixed(2)}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Total de Produtos */}
            <div className="mt-4 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
              <div className="flex justify-between items-center">
                <span className="font-semibold text-gray-900 dark:text-gray-100">Total de Produtos/Peças:</span>
                <span className="text-xl font-bold text-green-600 dark:text-green-400">
                  R$ {partsAmount.toFixed(2)}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Aba 5: Pagamento */}
        {activeTab === 'payment' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
              💰 Condições de Pagamento
            </h3>

            {/* Resumo Financeiro */}
            <div className="p-4 bg-gray-100 dark:bg-gray-800 rounded-lg space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-700 dark:text-gray-300">Serviços:</span>
                <span className="font-medium">R$ {serviceAmount.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-700 dark:text-gray-300">Produtos/Peças:</span>
                <span className="font-medium">R$ {partsAmount.toFixed(2)}</span>
              </div>
              <div className="flex justify-between pt-2 border-t border-gray-300 dark:border-gray-600">
                <span className="text-gray-700 dark:text-gray-300">Subtotal:</span>
                <span className="font-medium">R$ {(serviceAmount + partsAmount).toFixed(2)}</span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Desconto */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Desconto (R$)
                </label>
                <input
                  type="number"
                  step="0.01"
                  {...register('discount_amount', { valueAsNumber: true })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>

              {/* Garantia */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Garantia (dias)
                </label>
                <input
                  type="number"
                  {...register('warranty_days', { valueAsNumber: true })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>
            </div>

            {/* Condição de Pagamento */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Condição de Pagamento
              </label>
              <select
                {...register('payment_condition')}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="a_vista">À Vista</option>
                <option value="parcelado">Parcelado</option>
              </select>
            </div>

            {/* Parcelas (se parcelado) */}
            {watch('payment_condition') === 'parcelado' && (
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <h4 className="font-medium text-gray-900 dark:text-gray-100">Parcelas</h4>
                  <button
                    type="button"
                    onClick={() => {
                      const nextNumber = installmentsFields.length + 1;
                      const today = new Date();
                      today.setMonth(today.getMonth() + nextNumber);
                      appendInstallment({
                        installment_number: nextNumber,
                        due_date: today.toISOString().split('T')[0],
                        amount: totalAmount / (installmentsFields.length + 1),
                      });
                    }}
                    className="px-3 py-1 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
                  >
                    + Adicionar Parcela
                  </button>
                </div>

                {installmentsFields.map((field, index) => (
                  <div key={field.id} className="flex gap-3 items-start">
                    <div className="flex-1 grid grid-cols-3 gap-3">
                      <div>
                        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Número
                        </label>
                        <input
                          type="number"
                          {...register(`installments.${index}.installment_number`, { valueAsNumber: true })}
                          className="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                          readOnly
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Vencimento
                        </label>
                        <input
                          type="date"
                          {...register(`installments.${index}.due_date`)}
                          className="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Valor (R$)
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          {...register(`installments.${index}.amount`, { valueAsNumber: true })}
                          className="w-full px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                        />
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeInstallment(index)}
                      className="mt-6 text-red-600 hover:text-red-800 dark:text-red-400"
                    >
                      🗑️
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* Total Final */}
            <div className="mt-6 p-6 bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/30 rounded-lg border-2 border-blue-300 dark:border-blue-700">
              <div className="flex justify-between items-center">
                <span className="text-xl font-bold text-gray-900 dark:text-gray-100">VALOR TOTAL:</span>
                <span className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                  R$ {totalAmount.toFixed(2)}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Aba 6: Anexos */}
        {activeTab === 'attachments' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
              📎 Anexos e Documentos
            </h3>

            <div className="text-center py-12 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg">
              <div className="text-6xl mb-4">📁</div>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Funcionalidade de upload de arquivos
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-500">
                Em desenvolvimento: Fotos do equipamento, orçamentos, laudos técnicos
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Botões de Ação */}
      <div className="flex justify-end gap-3 pt-6 border-t border-gray-200 dark:border-gray-700">
        <button
          type="button"
          onClick={onCancel}
          disabled={isLoading}
          className="px-6 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={isLoading}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Salvando...' : mode === 'create' ? 'Criar Ordem de Serviço' : 'Atualizar Ordem de Serviço'}
        </button>
      </div>
    </form>
  );
}
