import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createCustomer, patchCustomer } from '../../api/customers';
import { useEffect, useState } from 'react';
import { getCompanyByCnpj, getAddressByCep } from '../../api/external';
import { onlyDigits, isCNPJ, maskCnpjCpf, maskCep, maskPhone } from '../../lib/brasil';

const customerSchema = z.object({
  person_type: z.enum(['PF', 'PJ']).default('PF'),
  name: z.string().min(1, 'Nome/Razão Social é obrigatório').max(120, 'Máx. 120 caracteres'),
  trade_name: z.string().max(120, 'Máx. 120 caracteres').optional(),
  cpf_cnpj: z.string().optional().refine(
    (val) => {
      if (!val) return true;
      const numbers = onlyDigits(val);
      return numbers.length === 11 || numbers.length === 14;
    },
    { message: 'CPF deve ter 11 dígitos ou CNPJ deve ter 14 dígitos' }
  ),
  state_registration: z.string().max(20, 'Máx. 20 caracteres').optional(),
  email: z.string().email('Email inválido').optional().or(z.literal('')),
  phone: z.string().optional(),
  phone2: z.string().optional(),
  cep: z.string().optional(),
  street: z.string().max(200, 'Máx. 200 caracteres').optional(),
  number: z.string().max(20, 'Máx. 20 caracteres').optional(),
  address_complement: z.string().max(100, 'Máx. 100 caracteres').optional(),
  neighborhood: z.string().max(100, 'Máx. 100 caracteres').optional(),
  city: z.string().max(100, 'Máx. 100 caracteres').optional(),
  state: z.string().max(2, 'UF deve ter 2 caracteres').optional(),
  notes: z.string().optional(),
  status: z.enum(['active', 'inactive']).default('active'),
});

type CustomerFormData = z.infer<typeof customerSchema>;

interface CustomerFormProps {
  mode: 'create' | 'edit';
  initialData?: Partial<CustomerFormData> & { id: string };
  onSuccess: () => void;
  onCancel: () => void;
}

export function CustomerForm({ mode, initialData, onSuccess, onCancel }: CustomerFormProps) {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'cadastro' | 'endereco' | 'adicional'>('cadastro');
  
  // Estados para automações
  const [isFetchingCnpj, setIsFetchingCnpj] = useState(false);
  const [cnpjError, setCnpjError] = useState<string | null>(null);
  const [isFetchingCep, setIsFetchingCep] = useState(false);
  const [cepError, setCepError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setError,
    setValue,
    watch,
    getValues,
  } = useForm<CustomerFormData>({
    resolver: zodResolver(customerSchema),
    defaultValues: {
      person_type: 'PF',
      status: 'active',
      ...initialData,
    },
  });

  const personType = watch('person_type');
  const cpfCnpj = watch('cpf_cnpj');
  const cep = watch('cep');

  // Atualizar form quando initialData mudar
  useEffect(() => {
    if (mode === 'edit' && initialData) {
      reset({
        person_type: initialData.person_type || 'PF',
        name: initialData.name || '',
        trade_name: initialData.trade_name || '',
        cpf_cnpj: initialData.cpf_cnpj || '',
        state_registration: initialData.state_registration || '',
        email: initialData.email || '',
        phone: initialData.phone || '',
        phone2: initialData.phone2 || '',
        cep: initialData.cep || '',
        street: initialData.street || '',
        number: initialData.number || '',
        address_complement: initialData.address_complement || '',
        neighborhood: initialData.neighborhood || '',
        city: initialData.city || '',
        state: initialData.state || '',
        notes: initialData.notes || '',
        status: initialData.status || 'active',
      });
    }
  }, [mode, initialData, reset]);

  // Automação: Buscar CNPJ (com debounce)
  useEffect(() => {
    if (!cpfCnpj || personType !== 'PJ') {
      setCnpjError(null);
      return;
    }

    const digits = onlyDigits(cpfCnpj);
    if (!isCNPJ(cpfCnpj)) {
      setCnpjError(null);
      return;
    }

    const timer = setTimeout(async () => {
      await fetchCnpjData(digits);
    }, 600);

    return () => clearTimeout(timer);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cpfCnpj, personType]);

  // Automação: Buscar CEP (com debounce)
  useEffect(() => {
    if (!cep) {
      setCepError(null);
      return;
    }

    const digits = onlyDigits(cep);
    
    // Só buscar se tiver 8 dígitos
    if (digits.length !== 8) {
      setCepError(null);
      return;
    }

    // Debounce de 600ms
    const timer = setTimeout(async () => {
      await fetchCepData(digits);
    }, 600);

    return () => clearTimeout(timer);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cep]);

  const fetchCnpjData = async (cnpj: string) => {
    setIsFetchingCnpj(true);
    setCnpjError(null);

    try {
      const data = await getCompanyByCnpj(cnpj);
      const currentValues = getValues();
      
      if (!currentValues.name) setValue('name', data.nome_fantasia || data.razao_social || '', { shouldValidate: true, shouldDirty: false });
      if (!currentValues.trade_name) setValue('trade_name', data.nome_fantasia || '', { shouldValidate: true, shouldDirty: false });
      if (!currentValues.email && data.email) setValue('email', data.email, { shouldValidate: true, shouldDirty: false });
      if (!currentValues.phone && data.ddd_telefone_1) setValue('phone', onlyDigits(data.ddd_telefone_1), { shouldValidate: true, shouldDirty: false });
      if (!currentValues.cep && data.cep) {
        const cleanCep = onlyDigits(data.cep);
        setValue('cep', cleanCep, { shouldValidate: true, shouldDirty: false });
        if (cleanCep.length === 8) setTimeout(() => fetchCepData(cleanCep), 300);
      }
      if (!currentValues.street && data.logradouro) setValue('street', data.logradouro, { shouldValidate: true, shouldDirty: false });
      if (!currentValues.number && data.numero) setValue('number', data.numero, { shouldValidate: true, shouldDirty: false });
      if (!currentValues.neighborhood && data.bairro) setValue('neighborhood', data.bairro, { shouldValidate: true, shouldDirty: false });
      if (!currentValues.city && data.municipio) setValue('city', data.municipio, { shouldValidate: true, shouldDirty: false });
      if (!currentValues.state && data.uf) setValue('state', data.uf, { shouldValidate: true, shouldDirty: false });
    } catch (error: any) {
      setCnpjError(error.message || 'Erro ao consultar CNPJ');
    } finally {
      setIsFetchingCnpj(false);
    }
  };

  // Função para buscar dados do CEP
  const fetchCepData = async (cep: string) => {
    setIsFetchingCep(true);
    setCepError(null);

    try {
      const data = await getAddressByCep(cep);
      
      // Preencher apenas campos vazios
      const currentValues = getValues();
      
      if (!currentValues.street && data.logradouro) {
        setValue('street', data.logradouro, { shouldValidate: true, shouldDirty: false });
      }
      
      if (!currentValues.neighborhood && data.bairro) {
        setValue('neighborhood', data.bairro, { shouldValidate: true, shouldDirty: false });
      }
      
      if (!currentValues.city && data.localidade) {
        setValue('city', data.localidade, { shouldValidate: true, shouldDirty: false });
      }
      
      if (!currentValues.state && data.uf) {
        setValue('state', data.uf, { shouldValidate: true, shouldDirty: false });
      }
    } catch (error: any) {
      setCepError(error.message || 'Erro ao consultar CEP');
    } finally {
      setIsFetchingCep(false);
    }
  };

  const handleCnpjBlur = () => {
    if (personType === 'PJ' && isCNPJ(cpfCnpj)) {
      fetchCnpjData(onlyDigits(cpfCnpj || ''));
    }
  };

  // Handler onBlur para CEP (dispara busca imediatamente)
  const handleCepBlur = () => {
    const digits = onlyDigits(cep || '');
    if (digits.length === 8) {
      fetchCepData(digits);
    }
  };

  const mutation = useMutation({
    mutationFn: (data: CustomerFormData) => {
      const cleanData: any = {};
      Object.entries(data).forEach(([key, value]) => {
        if (value !== undefined && value !== '' && value !== null) {
          if (key === 'cpf_cnpj' || key === 'phone' || key === 'phone2' || key === 'cep') {
            cleanData[key] = onlyDigits(value as string);
          } else {
            cleanData[key] = value;
          }
        }
      });

      if (mode === 'edit' && initialData) {
        return patchCustomer(initialData.id, cleanData);
      }
      return createCustomer(cleanData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      reset();
      onSuccess();
    },
    onError: (error: any) => {
      const status = error.response?.status;
      if (status === 422) {
        const detail = error.response.data?.detail;
        if (Array.isArray(detail)) {
          detail.forEach((err: any) => {
            const field = err.loc?.[1] as keyof CustomerFormData;
            if (field) setError(field, { message: err.msg });
          });
        } else {
          setError('root', { message: detail || 'Erro de validação' });
        }
      } else {
        setError('root', { 
          message: error.response?.data?.detail || `Erro ao ${mode === 'edit' ? 'atualizar' : 'criar'} cliente` 
        });
      }
    },
  });

  return (
    <form onSubmit={handleSubmit((data) => mutation.mutate(data))} className="space-y-6">
      {errors.root && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {errors.root.message}
        </div>
      )}

      {/* Abas */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            type="button"
            onClick={() => setActiveTab('cadastro')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'cadastro'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            📋 Dados Cadastrais
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('endereco')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'endereco'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            📍 Endereço
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('adicional')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'adicional'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            📝 Informações Adicionais
          </button>
        </nav>
      </div>

      {/* Aba: Dados Cadastrais */}
      {activeTab === 'cadastro' && (
        <div className="space-y-4">
          {/* Tipo de Pessoa */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Tipo de Pessoa *</label>
            <div className="flex gap-4">
              <label className="flex items-center">
                <input type="radio" value="PF" {...register('person_type')} className="mr-2" />
                Pessoa Física (CPF)
              </label>
              <label className="flex items-center">
                <input type="radio" value="PJ" {...register('person_type')} className="mr-2" />
                Pessoa Jurídica (CNPJ)
              </label>
            </div>
            {errors.person_type && <p className="mt-1 text-sm text-red-600">{errors.person_type.message}</p>}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Nome/Razão Social */}
            <div className="md:col-span-2">
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                {personType === 'PJ' ? 'Razão Social *' : 'Nome Completo *'}
              </label>
              <input
                id="name"
                type="text"
                {...register('name')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder={personType === 'PJ' ? 'Ex: Tech Solutions LTDA' : 'Ex: João da Silva'}
              />
              {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>}
            </div>

            {/* Nome Fantasia (só PJ) */}
            {personType === 'PJ' && (
              <div className="md:col-span-2">
                <label htmlFor="trade_name" className="block text-sm font-medium text-gray-700 mb-1">
                  Nome Fantasia
                </label>
                <input
                  id="trade_name"
                  type="text"
                  {...register('trade_name')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Ex: TechSol"
                />
                {errors.trade_name && <p className="mt-1 text-sm text-red-600">{errors.trade_name.message}</p>}
              </div>
            )}

            {/* CPF/CNPJ */}
            <div>
              <label htmlFor="cpf_cnpj" className="block text-sm font-medium text-gray-700 mb-1">
                {personType === 'PJ' ? 'CNPJ' : 'CPF'}
              </label>
              <div className="relative">
                <input
                  id="cpf_cnpj"
                  type="text"
                  {...register('cpf_cnpj')}
                  onBlur={handleCnpjBlur}
                  onChange={(e) => setValue('cpf_cnpj', maskCnpjCpf(e.target.value), { shouldValidate: true })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder={personType === 'PJ' ? '12.345.678/0001-00' : '123.456.789-00'}
                />
                {isFetchingCnpj && (
                  <div className="absolute right-2 top-2">
                    <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                  </div>
                )}
              </div>
              {errors.cpf_cnpj && <p className="mt-1 text-sm text-red-600">{errors.cpf_cnpj.message}</p>}
              {cnpjError && !errors.cpf_cnpj && <p className="mt-1 text-sm text-amber-600">{cnpjError}</p>}
              {personType === 'PJ' && isCNPJ(cpfCnpj) && !isFetchingCnpj && !cnpjError && (
                <p className="mt-1 text-sm text-gray-500">💡 Preenchimento automático por CNPJ ativado</p>
              )}
            </div>

            {/* Inscrição Estadual (só PJ) */}
            {personType === 'PJ' && (
              <div>
                <label htmlFor="state_registration" className="block text-sm font-medium text-gray-700 mb-1">
                  Inscrição Estadual (IE)
                </label>
                <input
                  id="state_registration"
                  type="text"
                  {...register('state_registration')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="123456789"
                />
                {errors.state_registration && <p className="mt-1 text-sm text-red-600">{errors.state_registration.message}</p>}
              </div>
            )}

            {/* Email */}
            <div className={personType === 'PF' ? '' : 'md:col-span-2'}>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                id="email"
                type="email"
                {...register('email')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="contato@example.com"
              />
              {errors.email && <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>}
            </div>

            {/* Telefone Principal */}
            <div>
              <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">
                Telefone Principal
              </label>
              <input
                id="phone"
                type="text"
                {...register('phone')}
                onChange={(e) => setValue('phone', maskPhone(e.target.value), { shouldValidate: true })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="(11) 98765-4321"
              />
              {errors.phone && <p className="mt-1 text-sm text-red-600">{errors.phone.message}</p>}
            </div>

            {/* Telefone Alternativo */}
            <div>
              <label htmlFor="phone2" className="block text-sm font-medium text-gray-700 mb-1">
                Telefone Alternativo
              </label>
              <input
                id="phone2"
                type="text"
                {...register('phone2')}
                onChange={(e) => setValue('phone2', maskPhone(e.target.value), { shouldValidate: true })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="(11) 3333-4444"
              />
              {errors.phone2 && <p className="mt-1 text-sm text-red-600">{errors.phone2.message}</p>}
            </div>
          </div>
        </div>
      )}

      {/* Aba: Endereço */}
      {activeTab === 'endereco' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* CEP */}
            <div>
              <label htmlFor="cep" className="block text-sm font-medium text-gray-700 mb-1">
                CEP
              </label>
              <div className="relative">
                <input
                  id="cep"
                  type="text"
                  {...register('cep')}
                  onBlur={handleCepBlur}
                  onChange={(e) => setValue('cep', maskCep(e.target.value), { shouldValidate: true })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="12345-678"
                />
                {isFetchingCep && (
                  <div className="absolute right-2 top-2">
                    <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                  </div>
                )}
              </div>
              {errors.cep && <p className="mt-1 text-sm text-red-600">{errors.cep.message}</p>}
              {cepError && !errors.cep && <p className="mt-1 text-sm text-amber-600">{cepError}</p>}
              {onlyDigits(cep || '').length === 8 && !isFetchingCep && !cepError && (
                <p className="mt-1 text-sm text-gray-500">💡 Preenchimento automático por CEP ativado</p>
              )}
            </div>

            {/* Logradouro */}
            <div className="md:col-span-2">
              <label htmlFor="street" className="block text-sm font-medium text-gray-700 mb-1">
                Logradouro
              </label>
              <input
                id="street"
                type="text"
                {...register('street')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Rua, Avenida, etc."
              />
              {errors.street && <p className="mt-1 text-sm text-red-600">{errors.street.message}</p>}
            </div>

            {/* Número */}
            <div>
              <label htmlFor="number" className="block text-sm font-medium text-gray-700 mb-1">
                Número
              </label>
              <input
                id="number"
                type="text"
                {...register('number')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="123"
              />
              {errors.number && <p className="mt-1 text-sm text-red-600">{errors.number.message}</p>}
            </div>

            {/* Complemento */}
            <div className="md:col-span-2">
              <label htmlFor="address_complement" className="block text-sm font-medium text-gray-700 mb-1">
                Complemento
              </label>
              <input
                id="address_complement"
                type="text"
                {...register('address_complement')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Apto, Sala, Bloco, etc."
              />
              {errors.address_complement && <p className="mt-1 text-sm text-red-600">{errors.address_complement.message}</p>}
            </div>

            {/* Bairro */}
            <div className="md:col-span-2">
              <label htmlFor="neighborhood" className="block text-sm font-medium text-gray-700 mb-1">
                Bairro
              </label>
              <input
                id="neighborhood"
                type="text"
                {...register('neighborhood')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Centro"
              />
              {errors.neighborhood && <p className="mt-1 text-sm text-red-600">{errors.neighborhood.message}</p>}
            </div>

            {/* UF */}
            <div>
              <label htmlFor="state" className="block text-sm font-medium text-gray-700 mb-1">
                UF
              </label>
              <input
                id="state"
                type="text"
                {...register('state')}
                onChange={(e) => setValue('state', e.target.value.toUpperCase(), { shouldValidate: true })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 uppercase"
                placeholder="SP"
                maxLength={2}
              />
              {errors.state && <p className="mt-1 text-sm text-red-600">{errors.state.message}</p>}
            </div>

            {/* Cidade */}
            <div className="md:col-span-3">
              <label htmlFor="city" className="block text-sm font-medium text-gray-700 mb-1">
                Cidade
              </label>
              <input
                id="city"
                type="text"
                {...register('city')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="São Paulo"
              />
              {errors.city && <p className="mt-1 text-sm text-red-600">{errors.city.message}</p>}
            </div>
          </div>
        </div>
      )}

      {/* Aba: Informações Adicionais */}
      {activeTab === 'adicional' && (
        <div className="space-y-4">
          {/* Status */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status *</label>
            <div className="flex gap-4">
              <label className="flex items-center">
                <input type="radio" value="active" {...register('status')} className="mr-2" />
                ✅ Ativo
              </label>
              <label className="flex items-center">
                <input type="radio" value="inactive" {...register('status')} className="mr-2" />
                ⛔ Inativo
              </label>
            </div>
            {errors.status && <p className="mt-1 text-sm text-red-600">{errors.status.message}</p>}
          </div>

          {/* Observações */}
          <div>
            <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-1">
              Observações
            </label>
            <textarea
              id="notes"
              {...register('notes')}
              rows={6}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Informações adicionais sobre o cliente..."
            />
            {errors.notes && <p className="mt-1 text-sm text-red-600">{errors.notes.message}</p>}
          </div>
        </div>
      )}

      {/* Botões de ação */}
      <div className="flex gap-3 pt-4 border-t border-gray-200">
        <button
          type="submit"
          disabled={mutation.isPending}
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {mutation.isPending 
            ? (mode === 'edit' ? 'Salvando...' : 'Criando...')
            : (mode === 'edit' ? 'Salvar Alterações' : 'Criar Cliente')
          }
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={mutation.isPending}
          className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Cancelar
        </button>
      </div>
    </form>
  );
}
