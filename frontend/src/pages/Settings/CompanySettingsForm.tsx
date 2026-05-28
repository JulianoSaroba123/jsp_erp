import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Settings } from '../../api/settings';
import { getAddressByCep, getCompanyByCnpj } from '../../api/external';
import { onlyDigits, maskCnpjCpf, maskCep, maskPhone } from '../../lib/brasil';

const companySchema = z.object({
  company_name: z.string().min(2, 'Nome da empresa é obrigatório (mín. 2 caracteres)'),
  trade_name: z.string().optional(),
  cnpj: z.string().optional().refine(
    (val) => !val || onlyDigits(val).length === 14,
    { message: 'CNPJ deve ter 14 dígitos' }
  ),
  email: z.string().email('Email inválido').optional().or(z.literal('')),
  phone: z.string().optional(),
  cep: z.string().optional(),
  street: z.string().optional(),
  number: z.string().optional(),
  neighborhood: z.string().optional(),
  city: z.string().optional(),
  state: z.string().max(2, 'UF deve ter 2 caracteres').optional(),
  logo_url: z.string().optional(),
});

type CompanyFormData = z.infer<typeof companySchema>;

interface CompanySettingsFormProps {
  settings: Settings;
  onSave: (data: Partial<Settings>) => void;
  isSaving: boolean;
  canEdit: boolean;
}

export function CompanySettingsForm({ settings, onSave, isSaving, canEdit }: CompanySettingsFormProps) {
  const [isFetchingCep, setIsFetchingCep] = useState(false);
  const [cepError, setCepError] = useState<string | null>(null);
  const [isFetchingCnpj, setIsFetchingCnpj] = useState(false);
  const [cnpjError, setCnpjError] = useState<string | null>(null);
  const [logoPreview, setLogoPreview] = useState<string | null>(settings.logo_url || null);
  const [logoFile, setLogoFile] = useState<File | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
    getValues,
  } = useForm<CompanyFormData>({
    resolver: zodResolver(companySchema),
    defaultValues: {
      company_name: settings.company_name || '',
      trade_name: settings.trade_name || '',
      cnpj: settings.cnpj || '',
      email: settings.email || '',
      phone: settings.phone || '',
      cep: settings.cep || '',
      street: settings.street || '',
      number: settings.number || '',
      neighborhood: settings.neighborhood || '',
      city: settings.city || '',
      state: settings.state || '',
      logo_url: settings.logo_url || '',
    },
  });

  const cep = watch('cep');
  const cnpj = watch('cnpj');

  // Automação CEP com debounce
  useEffect(() => {
    if (!cep) {
      setCepError(null);
      return;
    }

    const digits = onlyDigits(cep);
    if (digits.length !== 8) {
      setCepError(null);
      return;
    }

    const timer = setTimeout(async () => {
      await fetchCepData(digits);
    }, 600);

    return () => clearTimeout(timer);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cep]);

  // Automação CNPJ com debounce
  useEffect(() => {
    if (!cnpj) {
      setCnpjError(null);
      return;
    }

    const digits = onlyDigits(cnpj);
    if (digits.length !== 14) {
      setCnpjError(null);
      return;
    }

    const timer = setTimeout(async () => {
      await fetchCnpjData(digits);
    }, 600);

    return () => clearTimeout(timer);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cnpj]);

  const fetchCepData = async (cep: string) => {
    setIsFetchingCep(true);
    setCepError(null);

    try {
      const data = await getAddressByCep(cep);
      const currentValues = getValues();
      
      if (!currentValues.street && data.logradouro) setValue('street', data.logradouro, { shouldValidate: true, shouldDirty: false });
      if (!currentValues.neighborhood && data.bairro) setValue('neighborhood', data.bairro, { shouldValidate: true, shouldDirty: false });
      if (!currentValues.city && data.localidade) setValue('city', data.localidade, { shouldValidate: true, shouldDirty: false });
      if (!currentValues.state && data.uf) setValue('state', data.uf, { shouldValidate: true, shouldDirty: false });
    } catch (error: any) {
      setCepError(error.message || 'Erro ao consultar CEP');
    } finally {
      setIsFetchingCep(false);
    }
  };

  const fetchCnpjData = async (cnpj: string) => {
    setIsFetchingCnpj(true);
    setCnpjError(null);

    try {
      const data = await getCompanyByCnpj(cnpj);
      const currentValues = getValues();
      
      // Auto-fill apenas campos vazios
      if (!currentValues.company_name && data.razao_social) {
        setValue('company_name', data.razao_social, { shouldValidate: true, shouldDirty: false });
      }
      if (!currentValues.trade_name && (data.nome_fantasia || data.razao_social)) {
        setValue('trade_name', data.nome_fantasia || data.razao_social, { shouldValidate: true, shouldDirty: false });
      }
      if (!currentValues.email && data.email) {
        setValue('email', data.email, { shouldValidate: true, shouldDirty: false });
      }
      if (!currentValues.phone && data.ddd_telefone_1) {
        const phone = data.ddd_telefone_1.replace(/\D/g, '');
        setValue('phone', phone, { shouldValidate: true, shouldDirty: false });
      }
      if (!currentValues.cep && data.cep) {
        const cep = data.cep.replace(/\D/g, '');
        setValue('cep', cep, { shouldValidate: true, shouldDirty: false });
      }
      if (!currentValues.street && data.logradouro) {
        setValue('street', data.logradouro, { shouldValidate: true, shouldDirty: false });
      }
      if (!currentValues.number && data.numero) {
        setValue('number', data.numero, { shouldValidate: true, shouldDirty: false });
      }
      if (!currentValues.neighborhood && data.bairro) {
        setValue('neighborhood', data.bairro, { shouldValidate: true, shouldDirty: false });
      }
      if (!currentValues.city && data.municipio) {
        setValue('city', data.municipio, { shouldValidate: true, shouldDirty: false });
      }
      if (!currentValues.state && data.uf) {
        setValue('state', data.uf, { shouldValidate: true, shouldDirty: false });
      }
    } catch (error: any) {
      setCnpjError(error.message || 'Erro ao consultar CNPJ');
    } finally {
      setIsFetchingCnpj(false);
    }
  };

  const handleCepBlur = () => {
    const digits = onlyDigits(cep || '');
    if (digits.length === 8) fetchCepData(digits);
  };

  const handleLogoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validar tipo e tamanho
    if (!file.type.startsWith('image/')) {
      alert('Por favor, selecione uma imagem válida');
      return;
    }

    if (file.size > 2 * 1024 * 1024) {
      alert('Imagem muito grande. Máximo: 2MB');
      return;
    }

    setLogoFile(file);
    
    // Preview
    const reader = new FileReader();
    reader.onload = () => {
      setLogoPreview(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleRemoveLogo = () => {
    setLogoFile(null);
    setLogoPreview(null);
    setValue('logo_url', '');
  };

  const onSubmit = (data: CompanyFormData) => {
    console.log('🔵 [CompanyForm] onSubmit chamado:', data);
    
    // Limpar máscaras
    const cleanData: Partial<Settings> = {
      ...data,
      cnpj: data.cnpj ? onlyDigits(data.cnpj) : undefined,
      phone: data.phone ? onlyDigits(data.phone) : undefined,
      cep: data.cep ? onlyDigits(data.cep) : undefined,
    };

    // Se houver novo logo, incluir no payload
    if (logoFile) {
      console.log('📷 [CompanyForm] Incluindo logo no payload');
      (cleanData as any)._logoFile = logoFile;
    }

    console.log('✅ [CompanyForm] Chamando onSave com:', cleanData);
    onSave(cleanData);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Logo */}
      <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Logo da Empresa</h3>
        
        <div className="flex items-start gap-6">
          {/* Preview */}
          <div className="flex-shrink-0">
            {logoPreview ? (
              <div className="relative w-32 h-32 border-2 border-gray-300 rounded-lg overflow-hidden bg-white">
                <img src={logoPreview} alt="Logo" className="w-full h-full object-contain" />
                {canEdit && (
                  <button
                    type="button"
                    onClick={handleRemoveLogo}
                    aria-label="Remover logo"
                    className="absolute top-1 right-1 bg-red-500 text-white rounded-full p-1 hover:bg-red-600"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>
            ) : (
              <div className="w-32 h-32 border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center bg-gray-100">
                <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
            )}
          </div>

          {/* Upload */}
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Enviar Logo
            </label>
            <input
              type="file"
              accept="image/*"
              onChange={handleLogoChange}
              disabled={!canEdit}
              aria-label="Escolher arquivo de logo"
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 disabled:opacity-50"
            />
            <p className="mt-1 text-xs text-gray-500">
              Formatos aceitos: JPG, PNG, GIF. Máximo: 2MB.
            </p>
          </div>
        </div>
      </div>

      {/* Dados da Empresa */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Razão Social */}
        <div className="md:col-span-2">
          <label htmlFor="company_name" className="block text-sm font-medium text-gray-700 mb-1">
            Razão Social *
          </label>
          <input
            id="company_name"
            type="text"
            {...register('company_name')}
            disabled={!canEdit}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            placeholder="Ex: Tech Solutions LTDA"
          />
          {errors.company_name && <p className="mt-1 text-sm text-red-600">{errors.company_name.message}</p>}
        </div>

        {/* Nome Fantasia */}
        <div className="md:col-span-2">
          <label htmlFor="trade_name" className="block text-sm font-medium text-gray-700 mb-1">
            Nome Fantasia
          </label>
          <input
            id="trade_name"
            type="text"
            {...register('trade_name')}
            disabled={!canEdit}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            placeholder="Ex: TechSol"
          />
          {errors.trade_name && <p className="mt-1 text-sm text-red-600">{errors.trade_name.message}</p>}
        </div>

        {/* CNPJ */}
        <div>
          <label htmlFor="cnpj" className="block text-sm font-medium text-gray-700 mb-1">
            CNPJ
          </label>
          <div className="relative">
            <input
              id="cnpj"
              type="text"
              {...register('cnpj')}
              onChange={(e) => setValue('cnpj', maskCnpjCpf(e.target.value), { shouldValidate: true })}
              disabled={!canEdit}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              placeholder="12.345.678/0001-00"
            />
            {isFetchingCnpj && (
              <div className="absolute right-2 top-2">
                <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full"></div>
              </div>
            )}
          </div>
          {errors.cnpj && <p className="mt-1 text-sm text-red-600">{errors.cnpj.message}</p>}
          {cnpjError && !errors.cnpj && (
            <p className="mt-1 text-sm text-blue-600">
              ℹ️ {cnpjError}
            </p>
          )}
          {onlyDigits(cnpj || '').length === 14 && !isFetchingCnpj && !cnpjError && (
            <p className="mt-1 text-sm text-gray-500">💡 Preenchimento automático ativado</p>
          )}
        </div>

        {/* Email */}
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
            Email
          </label>
          <input
            id="email"
            type="email"
            {...register('email')}
            disabled={!canEdit}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            placeholder="contato@empresa.com"
          />
          {errors.email && <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>}
        </div>

        {/* Telefone */}
        <div className="md:col-span-2">
          <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">
            Telefone
          </label>
          <input
            id="phone"
            type="text"
            {...register('phone')}
            onChange={(e) => setValue('phone', maskPhone(e.target.value), { shouldValidate: true })}
            disabled={!canEdit}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            placeholder="(11) 3333-4444"
          />
          {errors.phone && <p className="mt-1 text-sm text-red-600">{errors.phone.message}</p>}
        </div>
      </div>

      {/* Endereço */}
      <div className="border-t border-gray-200 pt-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Endereço</h3>
        
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
                disabled={!canEdit}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
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
              <p className="mt-1 text-sm text-gray-500">💡 Preenchimento automático ativado</p>
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
              disabled={!canEdit}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
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
              disabled={!canEdit}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              placeholder="123"
            />
            {errors.number && <p className="mt-1 text-sm text-red-600">{errors.number.message}</p>}
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
              disabled={!canEdit}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              placeholder="Centro"
            />
            {errors.neighborhood && <p className="mt-1 text-sm text-red-600">{errors.neighborhood.message}</p>}
          </div>

          {/* Cidade */}
          <div className="md:col-span-2">
            <label htmlFor="city" className="block text-sm font-medium text-gray-700 mb-1">
              Cidade
            </label>
            <input
              id="city"
              type="text"
              {...register('city')}
              disabled={!canEdit}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
              placeholder="São Paulo"
            />
            {errors.city && <p className="mt-1 text-sm text-red-600">{errors.city.message}</p>}
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
              disabled={!canEdit}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 uppercase disabled:bg-gray-100 disabled:cursor-not-allowed"
              placeholder="SP"
              maxLength={2}
            />
            {errors.state && <p className="mt-1 text-sm text-red-600">{errors.state.message}</p>}
          </div>
        </div>
      </div>

      {/* Botão Salvar */}
      {canEdit && (
        <div className="flex justify-end pt-4 border-t border-gray-200">
          <button
            type="submit"
            disabled={isSaving}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSaving ? 'Salvando...' : 'Salvar Configurações'}
          </button>
        </div>
      )}
    </form>
  );
}
