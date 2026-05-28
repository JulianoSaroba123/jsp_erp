import { useEffect, useState } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  addServiceOrderAttachment,
  deleteServiceOrderAttachment,
  createServiceOrder,
  updateServiceOrder,
} from '../../api/serviceOrders';
import { getCustomers } from '../../api/customers';
import { getProducts } from '../../api/products';

const optionalNumber = z.preprocess(
  (value) => value === '' || Number.isNaN(value) ? undefined : value,
  z.number().min(0).optional()
);

const optionalUuid = z.preprocess(
  (value) => value === '' ? undefined : value,
  z.string().uuid().optional()
);

// Schema expandido com todos os campos
const serviceOrderSchema = z.object({
  customer_id: z.string().uuid('Selecione um cliente'),
  // Campos de tipo de OS
  order_type: z.enum(['comercial', 'operacional']).default('comercial'),
  service_type: z.string().optional(),
  proposal_id: optionalUuid,
  location: z.string().optional(),
  // Dados básicos
  title: z.string().min(3, 'Título muito curto').max(200, 'Título muito longo'),
  description: z.string().optional(),
  requester: z.string().optional(),
  problem_description: z.string().optional(),
  technician: z.string().optional(),
  status: z.enum(['pendente', 'em_execucao', 'finalizada', 'cancelada']).default('pendente'),
  priority: z.enum(['baixa', 'normal', 'alta', 'urgente']).default('normal'),
  opening_date: z.string().optional(),
  expected_date: z.string().optional(),
  scheduled_date: z.string().optional(),
  completed_date: z.string().optional(),
  start_time: z.string().optional(),
  end_time: z.string().optional(),
  initial_km: optionalNumber,
  final_km: optionalNumber,
  total_km: z.string().optional(),
  total_hours: z.string().optional(),
  equipment: z.string().optional(),
  brand_model: z.string().optional(),
  serial_number: z.string().optional(),
  reported_defect: z.string().optional(),
  technical_diagnosis: z.string().optional(),
  solution: z.string().optional(),
  notes: z.string().optional(),
  attachments_notes: z.string().optional(),
  discount_amount: optionalNumber,
  total_amount: optionalNumber,
  warranty_days: optionalNumber,
  payment_condition: z.enum(['a_vista', 'parcelado']).default('a_vista'),
  down_payment: optionalNumber,
  // Arrays para entidades relacionadas
  items: z.array(z.object({
    id: optionalUuid,
    description: z.string().min(1, 'Descrição obrigatória'),
    service_type: z.enum(['hora', 'dia', 'fechado']),
    quantity: z.number().min(0.01),
    unit_price: z.number().min(0),
  })).optional(),
  products: z.array(z.object({
    id: optionalUuid,
    product_id: optionalUuid,
    description: z.string().min(1),
    quantity: z.number().min(0.001),
    unit_price: z.number().min(0),
  })).optional(),
  installments: z.array(z.object({
    id: optionalUuid,
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

type TabType = 'basic' | 'execution' | 'equipment' | 'services' | 'products' | 'payment' | 'attachments';

export function ServiceOrderFormExpanded({ mode, initialData, onSuccess, onCancel }: ServiceOrderFormProps) {
  const [activeTab, setActiveTab] = useState<TabType>('basic');
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [attachments, setAttachments] = useState<any[]>(initialData?.attachments || []);
  const [attachmentFile, setAttachmentFile] = useState<File | null>(null);
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
    reset,
  } = useForm<ServiceOrderFormData>({
    resolver: zodResolver(serviceOrderSchema),
    defaultValues: {
      order_type: 'comercial',
      status: 'pendente',
      priority: 'normal',
      warranty_days: 90,
      discount_amount: 0,
      payment_condition: 'a_vista',
      down_payment: 0,
      total_amount: 0,
      items: [],
      products: [],
      installments: [],
    },
  });

  useEffect(() => {
    if (mode === 'edit' && initialData) {
      console.log('🔍 Carregando OS para edição:', initialData);
      console.log('🔍 customer_id do backend:', initialData.customer_id);
      
      setAttachments(initialData.attachments || []);
      reset({
        customer_id: initialData.customer_id || '',
        order_type: initialData.order_type || 'comercial',
        service_type: initialData.service_type || '',
        proposal_id: initialData.proposal_id || undefined,
        location: initialData.location || '',
        title: initialData.title || '',
        description: initialData.description || '',
        requester: initialData.requester || '',
        problem_description: initialData.problem_description || '',
        technician: initialData.technician || '',
        status: initialData.status || 'pendente',
        priority: initialData.priority || 'normal',
        opening_date: initialData.opening_date || '',
        expected_date: initialData.expected_date || '',
        scheduled_date: initialData.scheduled_date || '',
        completed_date: initialData.completed_date || '',
        start_time: initialData.start_time || '',
        end_time: initialData.end_time || '',
        initial_km: initialData.initial_km ?? undefined,
        final_km: initialData.final_km ?? undefined,
        total_km: initialData.total_km || '',
        total_hours: initialData.total_hours || '',
        equipment: initialData.equipment || '',
        brand_model: initialData.brand_model || '',
        serial_number: initialData.serial_number || '',
        reported_defect: initialData.reported_defect || '',
        technical_diagnosis: initialData.technical_diagnosis || '',
        solution: initialData.solution || '',
        notes: initialData.notes || '',
        attachments_notes: initialData.attachments_notes || '',
        discount_amount: Number(initialData.discount_amount || 0),
        payment_condition: initialData.payment_condition || (initialData.installments?.length ? 'parcelado' : 'a_vista'),
        down_payment: Number(initialData.down_payment || 0),
        warranty_days: Number(initialData.warranty_days ?? 90),
        total_amount: Number(initialData.total_amount || 0),
        items: initialData.items || [],
        products: initialData.products || [],
        installments: initialData.installments || [],
      });
    }
  }, [mode, initialData, reset]);

  // Field arrays para listas dinâmicas
  const { fields: itemsFields, append: appendItem, remove: removeItem } = useFieldArray({
    control,
    name: 'items',
    keyName: 'fieldId',
  });

  const { fields: productsFields, append: appendProduct, remove: removeProduct } = useFieldArray({
    control,
    name: 'products',
    keyName: 'fieldId',
  });

  const { fields: installmentsFields, append: appendInstallment, remove: removeInstallment } = useFieldArray({
    control,
    name: 'installments',
    keyName: 'fieldId',
  });

  // Watch para cálculos automáticos
  const items = watch('items') || [];
  const products = watch('products') || [];
  const installments = watch('installments') || [];
  const orderType = watch('order_type');
  const paymentCondition = watch('payment_condition');
  const downPayment = watch('down_payment') || 0;
  const discountAmount = watch('discount_amount') || 0;
  const initialKm = watch('initial_km');
  const finalKm = watch('final_km');
  const startTime = watch('start_time');
  const endTime = watch('end_time');
  const calculatedKm =
    typeof initialKm === 'number' && typeof finalKm === 'number' && finalKm >= initialKm
      ? finalKm - initialKm
      : 0;
  const calculateHours = (start?: string, end?: string) => {
    if (!start || !end) return '';

    const [startHour, startMinute] = start.split(':').map(Number);
    const [endHour, endMinute] = end.split(':').map(Number);
    if ([startHour, startMinute, endHour, endMinute].some(Number.isNaN)) return '';

    const startTotalMinutes = startHour * 60 + startMinute;
    let endTotalMinutes = endHour * 60 + endMinute;
    if (endTotalMinutes < startTotalMinutes) {
      endTotalMinutes += 24 * 60;
    }

    const diffMinutes = endTotalMinutes - startTotalMinutes;
    const hours = Math.floor(diffMinutes / 60);
    const minutes = diffMinutes % 60;
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
  };
  const calculatedHours = calculateHours(startTime, endTime);

  // Calcular totais
  const serviceAmount = items.reduce((sum, item) => {
    return sum + (item.quantity || 0) * (item.unit_price || 0);
  }, 0);

  const partsAmount = products.reduce((sum, product) => {
    return sum + (product.quantity || 0) * (product.unit_price || 0);
  }, 0);

  const totalAmount = Math.max(serviceAmount + partsAmount - discountAmount, 0);

  // Mutations
  const createMutation = useMutation({
    mutationFn: createServiceOrder,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['service-orders'] });
      setGlobalError(null);
      onSuccess();
    },
    onError: (error: any) => {
      const status = error.response?.status;
      
      if (status === 400 || status === 422) {
        const detail = error.response.data?.detail;
        if (Array.isArray(detail)) {
          const errorMessages = detail.map((err: any) => {
            const field = err.loc?.[1] || err.loc?.join('.');
            return `${field}: ${err.msg}`;
          });
          setGlobalError(`Erro de validação:\n${errorMessages.join('\n')}`);
        } else {
          setGlobalError(detail || 'Erro de validação. Verifique os campos obrigatórios.');
        }
      } else if (status === 403) {
        setGlobalError('Você não tem permissão para criar ordens de serviço');
      } else {
        setGlobalError(error.response?.data?.detail || 'Erro ao criar ordem de serviço');
      }
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => updateServiceOrder(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['service-orders'] });
      queryClient.invalidateQueries({ queryKey: ['service-order', initialData?.id] });
      setGlobalError(null);
      onSuccess();
    },
    onError: (error: any) => {
      const status = error.response?.status;
      
      if (status === 400 || status === 422) {
        const detail = error.response.data?.detail;
        if (Array.isArray(detail)) {
          const errorMessages = detail.map((err: any) => {
            const field = err.loc?.[1] || err.loc?.join('.');
            return `${field}: ${err.msg}`;
          });
          setGlobalError(`Erro de validação:\n${errorMessages.join('\n')}`);
        } else {
          setGlobalError(detail || 'Erro de validação. Verifique os campos obrigatórios.');
        }
      } else if (status === 404) {
        setGlobalError('Ordem de serviço não encontrada');
      } else if (status === 403) {
        setGlobalError('Você não tem permissão para editar esta ordem de serviço');
      } else {
        setGlobalError(error.response?.data?.detail || 'Erro ao atualizar ordem de serviço');
      }
    },
  });

  const onSubmit = (data: ServiceOrderFormData) => {
    console.log('🔍 onSubmit - data completo:', data);
    console.log('🔍 customer_id no form:', data.customer_id);
    
    const { installments, items, products, payment_condition, down_payment, total_amount, ...dataWithoutArrays } = data;
    void total_amount;
    const normalizedData = {
      ...dataWithoutArrays,
      total_km: calculatedKm > 0 ? `${calculatedKm} km` : dataWithoutArrays.total_km,
      total_hours: calculatedHours || dataWithoutArrays.total_hours,
    };
    
    console.log('🔍 normalizedData:', normalizedData);
    console.log('🔍 customer_id no normalizedData:', normalizedData.customer_id);
    
    if (mode === 'create') {
      // No CREATE, enviar com items e products
      const createPayload = {
        ...normalizedData,
        items: items?.map(item => ({
          ...item,
          total_price: item.quantity * item.unit_price,
        })),
        products: products?.map(product => ({
          ...product,
          total_price: product.quantity * product.unit_price,
        })),
        installments: payment_condition === 'parcelado'
          ? installments?.map(installment => ({
              ...installment,
              paid: installment.paid ?? false,
              payment_date: installment.payment_date || undefined,
            }))
          : [],
        payment_condition,
        down_payment: down_payment || 0,
        installment_count: payment_condition === 'parcelado' ? Math.max(installments?.length || 1, 1) : 1,
        service_amount: serviceAmount,
        parts_amount: partsAmount,
        discount_amount: discountAmount,
        total_amount: totalAmount,
      };
      createMutation.mutate(createPayload as any);
    } else if (initialData?.id) {
      // No UPDATE (PATCH), enviar APENAS campos diretos da OS
      // items/products/installments devem ser gerenciados via endpoints separados
      
      // Filtrar campos vazios/undefined para não sobrescrever dados existentes
      const filteredData = Object.fromEntries(
        Object.entries(normalizedData).filter(([, value]) => {
          // Manter apenas valores que não são undefined, null ou string vazia
          if (value === undefined || value === null) return false;
          if (typeof value === 'string' && value.trim() === '') return false;
          return true;
        })
      );
      
      console.log('🔍 filteredData:', filteredData);
      console.log('🔍 customer_id no filteredData:', filteredData.customer_id);
      
      // Determinar se devemos enviar items/products
      // Se há items/products no form E são diferentes dos iniciais, enviar para sincronizar
      const shouldSyncItems = items && items.length > 0;
      const shouldSyncProducts = products && products.length > 0;
      
      const updatePayload: Record<string, any> = {
        ...filteredData,
        // Campos de pagamento (removidos no destructuring mas necessários no update)
        payment_condition,
        down_payment: down_payment || 0,
        installment_count: payment_condition === 'parcelado' ? Math.max(installments?.length || 1, 1) : 1,
        discount_amount: discountAmount,
      };
      
      console.log('🔍 PAYLOAD FINAL:', updatePayload);
      console.log('🔍 customer_id no PAYLOAD FINAL:', updatePayload.customer_id);
      
      // Só enviar totais se estamos sincronizando items/products
      // Caso contrário, deixar o backend recalcular a partir dos existentes
      if (shouldSyncItems) {
        updatePayload.items = items.map(item => ({
          ...item,
          total_price: item.quantity * item.unit_price,
        }));
        updatePayload.service_amount = serviceAmount;
      }
      
      if (shouldSyncProducts) {
        updatePayload.products = products.map(product => ({
          ...product,
          total_price: product.quantity * product.unit_price,
        }));
        updatePayload.parts_amount = partsAmount;
      }
      
      // Se sincronizando qualquer um, recalcular total
      if (shouldSyncItems || shouldSyncProducts) {
        updatePayload.total_amount = totalAmount;
      }
      
      updateMutation.mutate({
        id: initialData.id,
        data: {
          ...updatePayload,
          // Enviar installments como parte do payload
          installments: payment_condition === 'parcelado' ? installments : [],
        },
      });
    }
  };

  const onInvalid = (formErrors: any) => {
    const firstError = Object.values(formErrors)[0] as any;
    setGlobalError(firstError?.message || 'Erro de validação. Verifique os campos obrigatórios e formatos informados.');
  };

  const handleAddAttachment = async () => {
    if (!initialData?.id) {
      setGlobalError('Salve a ordem de serviço antes de adicionar anexos.');
      return;
    }

    if (!attachmentFile) {
      setGlobalError('Selecione um arquivo para anexar.');
      return;
    }

    const fileExtension = attachmentFile.name.split('.').pop()?.toLowerCase();
    const fileType = attachmentFile.type.startsWith('image/')
      ? 'image'
      : fileExtension === 'pdf'
        ? 'pdf'
        : 'document';

    try {
      const saved = await addServiceOrderAttachment(initialData.id, {
        original_filename: attachmentFile.name,
        stored_filename: `${Date.now()}-${attachmentFile.name}`,
        file_type: fileType,
        mime_type: attachmentFile.type || undefined,
        file_size: attachmentFile.size,
        file_path: attachmentFile.name,
      });
      setAttachments((current) => [...current, saved]);
      setAttachmentFile(null);
      setGlobalError(null);
    } catch (error: any) {
      setGlobalError(error.response?.data?.detail || 'Erro ao adicionar anexo.');
    }
  };

  const handleDeleteAttachment = async (attachmentId: string) => {
    try {
      await deleteServiceOrderAttachment(attachmentId);
      setAttachments((current) => current.filter((attachment) => attachment.id !== attachmentId));
    } catch (error: any) {
      setGlobalError(error.response?.data?.detail || 'Erro ao remover anexo.');
    }
  };

  const isLoading = createMutation.isPending || updateMutation.isPending;

  // Tabs configuration
  const tabs = [
    { id: 'basic' as TabType, label: '📋 Dados Básicos', icon: '📋' },
    { id: 'execution' as TabType, label: 'Execucao', icon: 'Execucao' },
    { id: 'equipment' as TabType, label: '🖥️ Equipamento', icon: '🖥️' },
    { id: 'services' as TabType, label: '🔧 Serviços', icon: '🔧', badge: itemsFields.length },
    { id: 'products' as TabType, label: '📦 Produtos/Peças', icon: '📦', badge: productsFields.length },
    { id: 'payment' as TabType, label: '💰 Pagamento', icon: '💰' },
    { id: 'attachments' as TabType, label: '📎 Anexos', icon: '📎' },
  ];

  return (
    <form onSubmit={handleSubmit(onSubmit, onInvalid)} className="space-y-6">
      {/* Global Error Message */}
      {globalError && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded">
          <p className="font-semibold mb-2">⚠️ Erro ao salvar:</p>
          <pre className="text-sm whitespace-pre-wrap">{globalError}</pre>
        </div>
      )}
      
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
                    {...register('order_type')}
                    value="comercial"
                    className="w-4 h-4 text-purple-600"
                  />
                  <div>
                    <div className="font-semibold text-gray-900 dark:text-gray-100">🚨 Comercial / Atendimento</div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">Emergencial • Valores visíveis • Cobrança</div>
                  </div>
                </label>
                <label className="flex items-center space-x-3 p-3 border-2 border-gray-300 dark:border-gray-600 rounded-md cursor-pointer hover:bg-teal-50 dark:hover:bg-teal-900/30 has-[:checked]:border-teal-500 has-[:checked]:bg-teal-100 dark:has-[:checked]:bg-teal-900/50">
                  <input
                    type="radio"
                    {...register('order_type')}
                    value="operacional"
                    className="w-4 h-4 text-teal-600"
                  />
                  <div>
                    <div className="font-semibold text-gray-900 dark:text-gray-100">📋 Operacional / Projeto</div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">Proposta aprovada • Sem valores no relatório</div>
                  </div>
                </label>
              </div>
              {orderType === 'operacional' && (
                <div className="mt-3 p-3 bg-teal-50 dark:bg-teal-900/30 border border-teal-300 dark:border-teal-700 rounded-md">
                  <p className="text-sm text-teal-800 dark:text-teal-200">
                    💡 <strong>OS Operacional:</strong> Serve para acompanhamento de execução. Valores não aparecem no relatório operacional.
                  </p>
                </div>
              )}
              {errors.order_type && (
                <p className="mt-2 text-sm text-red-600 dark:text-red-400">{errors.order_type.message}</p>
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

        {activeTab === 'execution' && (
          <div className="space-y-5">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Execucao e Controle
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Status da OS
                </label>
                <select
                  {...register('status')}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                >
                  <option value="pendente">Pendente</option>
                  <option value="em_execucao">Em execucao</option>
                  <option value="finalizada">Finalizada</option>
                  <option value="cancelada">Cancelada</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Tipo de Servico
                </label>
                <input
                  type="text"
                  {...register('service_type')}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="Ex: instalacao, manutencao, diaria"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Local de Atendimento
                </label>
                <input
                  type="text"
                  {...register('location')}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="Ex: planta, obra, sala tecnica"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Abertura
                </label>
                <input
                  type="date"
                  {...register('opening_date')}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Agendada para
                </label>
                <input
                  type="date"
                  {...register('scheduled_date')}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Prevista
                </label>
                <input
                  type="date"
                  {...register('expected_date')}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Conclusao
                </label>
                <input
                  type="date"
                  {...register('completed_date')}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Inicio
                </label>
                <input
                  type="time"
                  {...register('start_time')}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Fim
                </label>
                <input
                  type="time"
                  {...register('end_time')}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Total de Horas
                </label>
                <div className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100">
                  {calculatedHours || '00:00'}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  KM Total
                </label>
                <div className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100">
                  {calculatedKm > 0 ? `${calculatedKm} km` : '0 km'}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  KM Inicial
                </label>
                <input
                  type="number"
                  {...register('initial_km', { valueAsNumber: true })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  KM Final
                </label>
                <input
                  type="number"
                  {...register('final_km', { valueAsNumber: true })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Observacoes de anexos, fotos e documentos
              </label>
              <textarea
                {...register('attachments_notes')}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="Ex: fotos do painel anexadas, laudo recebido, pendente assinatura"
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
                  <div key={field.fieldId} className="p-4 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-800">
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
                  <div key={field.fieldId} className="p-4 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-800">
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
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Forma de Pagamento
                </label>
                <select
                  {...register('payment_condition')}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                >
                  <option value="a_vista">A vista</option>
                  <option value="parcelado">Parcelado</option>
                </select>
              </div>

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

            {paymentCondition === 'parcelado' && (
              <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700 space-y-4">
                <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                  <label className="block text-sm font-semibold text-yellow-900 dark:text-yellow-100 mb-2">
                    Valor de Entrada (opcional)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    {...register('down_payment', { valueAsNumber: true })}
                    className="w-full md:w-1/3 px-3 py-2 border border-yellow-300 dark:border-yellow-700 rounded-md focus:ring-yellow-500 focus:border-yellow-500 bg-white dark:bg-gray-700 dark:text-white"
                    placeholder="0.00"
                  />
                  <p className="text-xs text-yellow-700 dark:text-yellow-300 mt-1">
                    O valor restante pode ser dividido nas parcelas abaixo.
                  </p>
                </div>

                <div className="flex justify-between items-center">
                  <h4 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Parcelas</h4>
                  <button
                    type="button"
                    onClick={() => {
                      const nextNumber = installmentsFields.length + 1;
                      const dueDate = new Date();
                      dueDate.setMonth(dueDate.getMonth() + nextNumber);
                      const remainingAmount = Math.max(totalAmount - downPayment, 0);
                      const amount = remainingAmount / nextNumber;
                      appendInstallment({
                        installment_number: nextNumber,
                        due_date: dueDate.toISOString().split('T')[0],
                        amount: Number(amount.toFixed(2)),
                      });
                    }}
                    className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors text-sm"
                  >
                    + Adicionar Parcela
                  </button>
                </div>

                {installmentsFields.length === 0 ? (
                  <div className="text-center text-gray-500 dark:text-gray-400 py-6 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg">
                    <p>Nenhuma parcela adicionada</p>
                    <p className="text-sm mt-1">Clique em "Adicionar Parcela" para começar</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {installmentsFields.map((field, index) => (
                      <div key={field.fieldId} className="grid grid-cols-1 md:grid-cols-12 gap-3 items-end border border-gray-200 dark:border-gray-700 rounded-md p-3 bg-gray-50 dark:bg-gray-800">
                        <div className="md:col-span-2">
                          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Parcela
                          </label>
                          <input
                            type="number"
                            {...register(`installments.${index}.installment_number`, { valueAsNumber: true })}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 dark:text-white"
                          />
                        </div>
                        <div className="md:col-span-4">
                          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Vencimento
                          </label>
                          <input
                            type="date"
                            {...register(`installments.${index}.due_date`)}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                          />
                        </div>
                        <div className="md:col-span-5">
                          <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                            Valor (R$)
                          </label>
                          <input
                            type="number"
                            step="0.01"
                            {...register(`installments.${index}.amount`, { valueAsNumber: true })}
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                          />
                        </div>
                        <div className="md:col-span-1">
                          <button
                            type="button"
                            onClick={() => removeInstallment(index)}
                            className="w-full px-2 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
                            title="Remover parcela"
                          >
                            X
                          </button>
                        </div>
                      </div>
                    ))}

                    <div className="space-y-2 pt-3 border-t border-gray-200 dark:border-gray-700">
                      {downPayment > 0 && (
                        <div className="flex justify-between">
                          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Entrada:</span>
                          <span className="font-semibold text-yellow-700 dark:text-yellow-300">
                            R$ {downPayment.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </span>
                        </div>
                      )}
                      <div className="flex justify-between">
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Total das Parcelas:</span>
                        <span className="font-bold text-blue-600 dark:text-blue-400">
                          R$ {installments.reduce((sum, installment) => sum + Number(installment.amount || 0), 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
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

            {!initialData?.id && (
              <div className="p-4 border border-yellow-200 bg-yellow-50 dark:bg-yellow-900/20 dark:border-yellow-800 rounded-md text-sm text-yellow-800 dark:text-yellow-200">
                Salve a ordem de serviço antes de adicionar anexos.
              </div>
            )}

            <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Selecionar arquivo
                </label>
                <input
                  type="file"
                  onChange={(event) => setAttachmentFile(event.target.files?.[0] || null)}
                  disabled={!initialData?.id}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white disabled:opacity-50"
                />
              </div>
              <button
                type="button"
                onClick={handleAddAttachment}
                disabled={!initialData?.id || !attachmentFile}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Adicionar Anexo
              </button>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                O sistema registra o anexo na OS com nome, tipo e tamanho do arquivo.
              </p>
            </div>

            <div className="space-y-3">
              {attachments.length === 0 ? (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400 border border-gray-200 dark:border-gray-700 rounded-lg">
                  Nenhum anexo registrado.
                </div>
              ) : (
                attachments.map((attachment) => (
                  <div key={attachment.id} className="flex items-center justify-between border border-gray-200 dark:border-gray-700 rounded-md p-3 bg-gray-50 dark:bg-gray-800">
                    <div>
                      <p className="font-medium text-gray-900 dark:text-gray-100">{attachment.original_filename}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {attachment.file_type} {attachment.file_size ? `- ${(attachment.file_size / 1024).toFixed(1)} KB` : ''}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleDeleteAttachment(attachment.id)}
                      className="px-3 py-1 text-sm bg-red-600 text-white rounded-md hover:bg-red-700"
                    >
                      Remover
                    </button>
                  </div>
                ))
              )}
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
