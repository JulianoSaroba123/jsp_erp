/**
 * SupplierForm.tsx
 * Formulário completo de Fornecedor com 8 seções
 * Suporta PJ/PF com campos dinâmicos, máscaras e APIs externas
 */

import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { suppliersAPI, CreateSupplierData, UpdateSupplierData } from '../../api/suppliers';
import { getCompanyByCnpj, getAddressByCep } from '../../api/external';

export default function SupplierForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isEditing = !!id;
  
  console.log('🔍 SupplierForm montado:', { id, isEditing, url: window.location.pathname });

  // ==================== STATE ====================
  
  const [activeTab, setActiveTab] = useState<'dados-principais' | 'documentos-contato' | 'endereco' | 'comercial-bancario' | 'observacoes'>('dados-principais');
  const [tipo, setTipo] = useState<'PF' | 'PJ'>('PJ');
  const [loadingCNPJ, setLoadingCNPJ] = useState(false);
  const [loadingCEP, setLoadingCEP] = useState(false);

  const [formData, setFormData] = useState<CreateSupplierData>({
    nome: '',
    tipo: 'PJ',
    cnpj_cpf: '',
    pais: 'Brasil',
    ativo: true
  });

  // ==================== FETCH SUPPLIER (Edit Mode) ==================== 
  
  const { data: supplier, isLoading } = useQuery({
    queryKey: ['supplier', id],
    queryFn: () => suppliersAPI.getById(id!),
    enabled: isEditing
  });

  // Preenche form quando carregar supplier
  useEffect(() => {
    if (supplier) {
      setFormData(supplier as CreateSupplierData);
      setTipo(supplier.tipo);
    }
  }, [supplier]);

  // ==================== BUSCA AUTOMÁTICA COM DEBOUNCE ====================
  
  // Busca automática de CNPJ (600ms debounce)
  useEffect(() => {
    const cnpj = formData.cnpj_cpf;
    
    // Só buscar em modo criação ou se CNPJ mudou
    if (!cnpj || tipo !== 'PJ') return;
    
    const cnpjLimpo = cnpj.replace(/\D/g, '');
    
    // Só buscar se tiver 14 dígitos (CNPJ completo)
    if (cnpjLimpo.length !== 14) return;
    
    const timer = setTimeout(async () => {
      console.log('🔍 Busca automática de CNPJ:', cnpjLimpo);
      await fetchCNPJData(cnpjLimpo);
    }, 600);
    
    return () => clearTimeout(timer);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formData.cnpj_cpf, tipo]);

  // Busca automática de CEP (600ms debounce)
  useEffect(() => {
    const cep = formData.cep;
    
    if (!cep) return;
    
    const cepLimpo = cep.replace(/\D/g, '');
    
    // Só buscar se tiver 8 dígitos (CEP completo)
    if (cepLimpo.length !== 8) return;
    
    const timer = setTimeout(async () => {
      console.log('🔍 Busca automática de CEP:', cepLimpo);
      await fetchCEPData(cepLimpo);
    }, 600);
    
    return () => clearTimeout(timer);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formData.cep]);

  // ==================== MUTATIONS ====================
  
  const createMutation = useMutation({
    mutationFn: suppliersAPI.create,
    onSuccess: () => {
      alert('✅ Fornecedor criado com sucesso!');
      queryClient.invalidateQueries({ queryKey: ['suppliers'] });
      navigate('/suppliers');
    },
    onError: (error: any) => {
      console.error('❌ Erro ao CRIAR fornecedor:', {
        error: error.response?.data,
        status: error.response?.status,
        url: error.config?.url,
        method: error.config?.method
      });
      console.error('🔍 ERRO COMPLETO:', JSON.stringify(error.response?.data, null, 2));
      
      let message = 'Erro ao criar fornecedor';
      
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        // Se detail é array (erros de validação Pydantic)
        if (Array.isArray(detail)) {
          const errors = detail.map((err: any) => {
            const field = err.loc?.[1] || err.loc?.[0] || 'campo';
            return `• ${field}: ${err.msg}`;
          }).join('\n');
          message = `Erros de validação:\n${errors}`;
        } else if (typeof detail === 'string') {
          message = detail;
        }
      }
      
      alert(`❌ ${message}`);
    }
  });

  const updateMutation = useMutation({
    mutationFn: (data: UpdateSupplierData) => suppliersAPI.update(id!, data),
    onSuccess: () => {
      alert('✅ Fornecedor atualizado com sucesso!');
      queryClient.invalidateQueries({ queryKey: ['suppliers'] });
      queryClient.invalidateQueries({ queryKey: ['supplier', id] });
      navigate('/suppliers');
    },
    onError: (error: any) => {
      console.error(`❌ Erro ao ATUALIZAR fornecedor ID ${id}:`, {
        error: error.response?.data,
        status: error.response?.status,
        url: error.config?.url,
        method: error.config?.method
      });
      let message = 'Erro ao atualizar fornecedor';
      
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        // Se detail é array (erros de validação Pydantic)
        if (Array.isArray(detail)) {
          const errors = detail.map((err: any) => {
            const field = err.loc?.[1] || err.loc?.[0] || 'campo';
            return `• ${field}: ${err.msg}`;
          }).join('\n');
          message = `Erros de validação:\n${errors}`;
        } else if (typeof detail === 'string') {
          message = detail;
        }
      }
      
      alert(`❌ ${message}`);
    }
  });

  // ==================== HANDLERS ====================
  
  const handleChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleTipoChange = (newTipo: 'PF' | 'PJ') => {
    setTipo(newTipo);
    handleChange('tipo', newTipo);
    
    // Limpa campos específicos quando mudar tipo
    if (newTipo === 'PF') {
      handleChange('nome_fantasia', '');
      handleChange('inscricao_estadual', '');
      handleChange('data_fundacao', '');
      handleChange('porte_empresa', '');
    } else {
      handleChange('data_nascimento', '');
      handleChange('genero', '');
      handleChange('estado_civil', '');
      handleChange('profissao', '');
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validações básicas
    const camposFaltando: string[] = [];
    
    if (!formData.nome) camposFaltando.push('Nome/Razão Social');
    if (!formData.cnpj_cpf) camposFaltando.push(tipo === 'PJ' ? 'CNPJ' : 'CPF');
    
    if (camposFaltando.length > 0) {
      alert(`❌ Campos obrigatórios faltando:\n• ${camposFaltando.join('\n• ')}`);
      
      // Focar no primeiro campo vazio
      if (!formData.nome) {
        setActiveTab('dados-principais');
        setTimeout(() => document.getElementById('nome')?.focus(), 100);
      } else if (!formData.cnpj_cpf) {
        setActiveTab('documentos-contato');
        setTimeout(() => document.getElementById('cnpj_cpf')?.focus(), 100);
      }
      return;
    }
    
    // Limpar dados: converter strings vazias para undefined
    const cleanData = Object.entries(formData).reduce((acc, [key, value]) => {
      // Se for string vazia, não incluir no payload (backend aceita undefined/null)
      if (value === '' || value === null) {
        return acc;
      }
      return { ...acc, [key]: value };
    }, {} as Partial<CreateSupplierData | UpdateSupplierData>);
    
    // Verificar autenticação
    const token = localStorage.getItem('access_token');
    console.log('🔐 Token existe?', token ? `Sim (${token.substring(0, 20)}...)` : 'NÃO - PRECISA FAZER LOGIN!');
    
    console.log(`📤 ${isEditing ? 'Atualizando' : 'Criando'} fornecedor:`, {
      id: isEditing ? id : 'novo',
      mode: isEditing ? 'EDIT' : 'CREATE',
      data: cleanData
    });
    
    if (isEditing) {
      updateMutation.mutate(cleanData as UpdateSupplierData);
    } else {
      createMutation.mutate(cleanData as CreateSupplierData);
    }
  };

  // ==================== MÁSCARAS ====================
  
  const mascaraCNPJ = (value: string): string => {
    const digits = value.replace(/\D/g, '').slice(0, 14);
    if (digits.length <= 11) {
      // CPF: 000.000.000-00
      return digits
        .replace(/(\d{3})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
    } else {
      // CNPJ: 00.000.000/0000-00
      return digits
        .replace(/(\d{2})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d)/, '$1/$2')
        .replace(/(\d{4})(\d{1,2})$/, '$1-$2');
    }
  };

  const mascaraCEP = (value: string): string => {
    const digits = value.replace(/\D/g, '').slice(0, 8);
    return digits.replace(/(\d{5})(\d)/, '$1-$2');
  };

  const mascaraTelefone = (value: string): string => {
    const digits = value.replace(/\D/g, '').slice(0, 11);
    if (digits.length <= 10) {
      return digits.replace(/(\d{2})(\d)/, '($1) $2').replace(/(\d{4})(\d)/, '$1-$2');
    } else {
      return digits.replace(/(\d{2})(\d)/, '($1) $2').replace(/(\d{5})(\d)/, '$1-$2');
    }
  };

  // ==================== FUNÇÕES DE BUSCA ====================
  
  // Busca dados do CNPJ na BrasilAPI
  const fetchCNPJData = async (cnpjLimpo: string) => {
    // Não buscar se já estiver carregando ou se não houver campos vazios para preencher
    if (loadingCNPJ) return;
    
    setLoadingCNPJ(true);
    try {
      const data = await getCompanyByCnpj(cnpjLimpo);
      
      console.log('📋 Dados BrasilAPI COMPLETOS recebidos:', {
        razao_social: data.razao_social,
        nome_fantasia: data.nome_fantasia,
        email: data.email,
        telefone1: data.ddd_telefone_1,
        telefone2: data.ddd_telefone_2,
        cep: data.cep,
        endereco: data.logradouro,
        numero: data.numero,
        complemento: data.complemento,
        bairro: data.bairro,
        cidade: data.municipio,
        uf: data.uf,
        porte: data.porte,
        situacao: data.situacao_cadastral,
        descricao_situacao: data.descricao_situacao_cadastral,
        data_inicio: data.data_inicio_atividade
      });
      
      // Auto-fill campos - preserva dados já preenchidos
      const updates: Partial<CreateSupplierData> = {};
      
      if (!formData.nome && (data.nome_fantasia || data.razao_social)) {
        updates.nome = data.nome_fantasia || data.razao_social;
        console.log('✅ Preenchendo nome:', data.nome_fantasia || data.razao_social);
      }
      if (!formData.nome_fantasia && (data.nome_fantasia || data.razao_social)) {
        updates.nome_fantasia = data.nome_fantasia || data.razao_social;
        console.log('✅ Preenchendo nome_fantasia:', data.nome_fantasia || data.razao_social);
      }
      if (!formData.email && data.email) {
        updates.email = data.email;
        console.log('✅ Preenchendo email:', data.email);
      } else if (!data.email) {
        console.log('⚠️ BrasilAPI não retornou email para este CNPJ');
      }
      
      if (!formData.telefone && data.ddd_telefone_1) {
        updates.telefone = data.ddd_telefone_1.replace(/\D/g, '');
        console.log('✅ Preenchendo telefone:', data.ddd_telefone_1);
      } else if (!data.ddd_telefone_1) {
        console.log('⚠️ BrasilAPI não retornou telefone para este CNPJ');
      }
      
      if (!formData.cep && data.cep) {
        updates.cep = data.cep.replace(/\D/g, '');
        console.log('✅ Preenchendo CEP:', data.cep);
      }
      if (!formData.endereco && data.logradouro) {
        updates.endereco = data.logradouro;
        console.log('✅ Preenchendo endereço:', data.logradouro);
      }
      if (!formData.numero && data.numero) {
        updates.numero = data.numero;
        console.log('✅ Preenchendo número:', data.numero);
      }
      if (!formData.complemento && data.complemento) {
        updates.complemento = data.complemento;
        console.log('✅ Preenchendo complemento:', data.complemento);
      }
      if (!formData.bairro && data.bairro) {
        updates.bairro = data.bairro;
        console.log('✅ Preenchendo bairro:', data.bairro);
      }
      if (!formData.cidade && data.municipio) {
        updates.cidade = data.municipio;
        console.log('✅ Preenchendo cidade:', data.municipio);
      }
      if (!formData.estado && data.uf) {
        updates.estado = data.uf;
        console.log('✅ Preenchendo estado:', data.uf);
      }
      if (!formData.porte_empresa && data.porte) {
        updates.porte_empresa = data.porte;
        console.log('✅ Preenchendo porte:', data.porte);
      }
      if (!formData.data_fundacao && data.data_inicio_atividade) {
        updates.data_fundacao = data.data_inicio_atividade;
        console.log('✅ Preenchendo data_fundacao:', data.data_inicio_atividade);
      }
      
      updates.pais = 'Brasil';
      updates.status = data.situacao_cadastral === '2' ? 'Ativo' : 'Inativo';
      
      setFormData(prev => ({ ...prev, ...updates }));
      
      console.log('✅ Total de campos preenchidos:', Object.keys(updates).length);
      console.log('📦 Updates aplicados:', updates);
    } catch (error: any) {
      console.error('❌ Erro ao buscar CNPJ:', error.message);
      console.error('🔍 Erro completo:', error);
    } finally {
      setLoadingCNPJ(false);
    }
  };

  // Busca dados do CEP no ViaCEP
  const fetchCEPData = async (cepLimpo: string) => {
    if (loadingCEP) return;
    
    setLoadingCEP(true);
    try {
      const data = await getAddressByCep(cepLimpo);
      
      console.log('📍 Dados ViaCEP recebidos:', data);
      
      // Auto-fill apenas campos vazios
      const updates: Partial<CreateSupplierData> = {};
      
      if (!formData.endereco && data.logradouro) updates.endereco = data.logradouro;
      if (!formData.bairro && data.bairro) updates.bairro = data.bairro;
      if (!formData.cidade && data.localidade) updates.cidade = data.localidade;
      if (!formData.estado && data.uf) updates.estado = data.uf;
      
      setFormData(prev => ({ ...prev, ...updates }));
      
      console.log('✅ Endereço preenchido:', Object.keys(updates).length, 'campos');
    } catch (error: any) {
      console.error('❌ Erro ao buscar CEP:', error.message);
    } finally {
      setLoadingCEP(false);
    }
  };

  // ==================== CONSULTAR CNPJ (Botão Manual) ====================
  
  const handleConsultarCNPJ = async () => {
    const cnpjLimpo = formData.cnpj_cpf?.replace(/\D/g, '') || '';
    
    if (cnpjLimpo.length !== 14) {
      alert('⚠️ CNPJ deve ter 14 dígitos');
      return;
    }
    
    setLoadingCNPJ(true);
    try {
      const data = await getCompanyByCnpj(cnpjLimpo);
      
      // Forçar atualização de todos os campos (mesmo os já preenchidos)
      const updates: Partial<CreateSupplierData> = {
        nome: data.nome_fantasia || data.razao_social,
        nome_fantasia: data.nome_fantasia || data.razao_social,
        email: data.email || formData.email,
        telefone: data.ddd_telefone_1?.replace(/\D/g, '') || formData.telefone,
        cep: data.cep?.replace(/\D/g, '') || formData.cep,
        endereco: data.logradouro,
        numero: data.numero || formData.numero,
        complemento: data.complemento || formData.complemento,
        bairro: data.bairro,
        cidade: data.municipio,
        estado: data.uf,
        pais: 'Brasil',
        porte_empresa: data.porte || formData.porte_empresa,
        status: data.situacao_cadastral === '2' ? 'Ativo' : 'Inativo',
        data_fundacao: data.data_inicio_atividade || formData.data_fundacao,
      };
      
      setFormData(prev => ({ ...prev, ...updates }));
      
      // Mensagem detalhada
      const msg = [
        '✅ Dados da empresa carregados!',
        `Situação: ${data.descricao_situacao_cadastral}`,
        data.porte ? `Porte: ${data.porte}` : '',
        data.cnae_fiscal_descricao ? `Atividade: ${data.cnae_fiscal_descricao.substring(0, 50)}...` : ''
      ].filter(Boolean).join('\n');
      
      alert(msg);
    } catch (error: any) {
      const message = error.message || 'Erro ao consultar CNPJ';
      alert(`❌ ${message}`);
    } finally {
      setLoadingCNPJ(false);
    }
  };

  // ==================== CONSULTAR CEP (ViaCEP) ====================
  
  const handleConsultarCEP = async () => {
    const cepLimpo = formData.cep?.replace(/\D/g, '') || '';
    
    if (cepLimpo.length !== 8) {
      alert('⚠️ CEP deve ter 8 dígitos');
      return;
    }
    
    setLoadingCEP(true);
    try {
      // Usa API externa diretamente (ViaCEP)
      const data = await getAddressByCep(cepLimpo);
      
      // Auto-fill endereço
      const updates: Partial<CreateSupplierData> = {
        endereco: data.logradouro || formData.endereco,
        bairro: data.bairro || formData.bairro,
        cidade: data.localidade || formData.cidade,
        estado: data.uf || formData.estado
      };
      
      setFormData(prev => ({ ...prev, ...updates }));
      
      alert('✅ Endereço carregado! Preencha o número.');
      
      // Foca no campo número
      setTimeout(() => {
        document.getElementById('numero')?.focus();
      }, 100);
    } catch (error: any) {
      const message = error.message || 'CEP não encontrado';
      alert(`❌ ${message}`);
    } finally {
      setLoadingCEP(false);
    }
  };

  // ==================== RENDER ====================
  
  if (isEditing && isLoading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">
          {isEditing ? '✏️ Editar Fornecedor' : '➕ Novo Fornecedor'}
        </h1>
        <p className="text-gray-600 mt-1">
          {isEditing ? `Editando: ${formData.nome}` : 'Cadastre um novo fornecedor (Pessoa Física ou Jurídica)'}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        
        {/* Navegação de Abas */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              type="button"
              onClick={() => setActiveTab('dados-principais')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'dados-principais'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              📋 Dados Principais
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('documentos-contato')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'documentos-contato'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              📄 Documentos & Contato
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
              onClick={() => setActiveTab('comercial-bancario')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'comercial-bancario'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              💰 Comercial & Bancário
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('observacoes')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'observacoes'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              📝 Observações
            </button>
          </nav>
        </div>
        
        {/* ==================== ABA 1: DADOS PRINCIPAIS ==================== */}
        {activeTab === 'dados-principais' && (
        <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
            📋 Dados Principais
          </h2>
          
          <div className="grid grid-cols-12 gap-4">
            
            {/* Tipo (PF/PJ) - Toggle */}
            <div className="col-span-12 md:col-span-3">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tipo <span className="text-red-500">*</span>
              </label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => handleTipoChange('PJ')}
                  className={`flex-1 py-2 px-4 rounded-lg font-medium transition-all ${
                    tipo === 'PJ'
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  🏢 PJ
                </button>
                <button
                  type="button"
                  onClick={() => handleTipoChange('PF')}
                  className={`flex-1 py-2 px-4 rounded-lg font-medium transition-all ${
                    tipo === 'PF'
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  👤 PF
                </button>
              </div>
            </div>

            {/* Nome / Razão Social */}
            <div className="col-span-12 md:col-span-9">
              <label htmlFor="nome" className="block text-sm font-medium text-gray-700 mb-1">
                {tipo === 'PJ' ? 'Razão Social' : 'Nome Completo'} <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="nome"
                value={formData.nome || ''}
                onChange={(e) => handleChange('nome', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder={tipo === 'PJ' ? 'Razão social da empresa' : 'Nome completo da pessoa'}
                required
                maxLength={150}
              />
            </div>

            {/* Nome Fantasia (apenas PJ) */}
            {tipo === 'PJ' && (
              <div className="col-span-12 md:col-span-6">
                <label htmlFor="nome_fantasia" className="block text-sm font-medium text-gray-700 mb-1">
                  Nome Fantasia
                </label>
                <input
                  type="text"
                  id="nome_fantasia"
                  value={formData.nome_fantasia || ''}
                  onChange={(e) => handleChange('nome_fantasia', e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Nome fantasia da empresa"
                  maxLength={150}
                />
              </div>
            )}

            {/* Classificação */}
            <div className="col-span-12 md:col-span-6">
              <label htmlFor="classificacao" className="block text-sm font-medium text-gray-700 mb-1">
                Classificação
              </label>
              <select
                id="classificacao"
                value={formData.classificacao || ''}
                onChange={(e) => handleChange('classificacao', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Selecione...</option>
                <option value="Classe A - Premium">🟢 Classe A - Premium</option>
                <option value="Classe B - Bom">🟡 Classe B - Bom</option>
                <option value="Classe C - Regular">🟠 Classe C - Regular</option>
                <option value="Classe D - Atenção">🔴 Classe D - Atenção</option>
              </select>
            </div>

            {/* Categoria */}
            <div className="col-span-12 md:col-span-6">
              <label htmlFor="categoria" className="block text-sm font-medium text-gray-700 mb-1">
                Categoria
              </label>
              <select
                id="categoria"
                value={formData.categoria || ''}
                onChange={(e) => handleChange('categoria', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Selecione...</option>
                <option value="Equipamentos">Equipamentos</option>
                <option value="Serviços">Serviços</option>
                <option value="Matéria-prima">Matéria-prima</option>
                <option value="Software">Software</option>
                <option value="Consultoria">Consultoria</option>
                <option value="Outros">Outros</option>
              </select>
            </div>

            {/* Origem */}
            <div className="col-span-12 md:col-span-6">
              <label htmlFor="origem" className="block text-sm font-medium text-gray-700 mb-1">
                Como nos conheceu
              </label>
              <select
                id="origem"
                value={formData.origem || ''}
                onChange={(e) => handleChange('origem', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Selecione...</option>
                <option value="Indicação">Indicação</option>
                <option value="Site/Google">Site/Google</option>
                <option value="Redes Sociais">Redes Sociais</option>
                <option value="Feira/Evento">Feira/Evento</option>
                <option value="Outros">Outros</option>
              </select>
            </div>
          </div>
        </div>
        )}

        {/* ==================== ABA 2: DOCUMENTOS & CONTATO ==================== */}
        {activeTab === 'documentos-contato' && (
        <>
        {/* SEÇÃO 2: DOCUMENTOS */}
        <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
            📄 Documentos
          </h2>
          
          <div className="grid grid-cols-12 gap-4">
            
            {/* CPF/CNPJ com botão consultar */}
            <div className="col-span-12 md:col-span-4">
              <label htmlFor="cnpj_cpf" className="block text-sm font-medium text-gray-700 mb-1">
                {tipo === 'PJ' ? 'CNPJ' : 'CPF'} <span className="text-red-500">*</span>
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  id="cnpj_cpf"
                  value={formData.cnpj_cpf ? mascaraCNPJ(formData.cnpj_cpf) : ''}
                  onChange={(e) => handleChange('cnpj_cpf', e.target.value.replace(/\D/g, ''))}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder={tipo === 'PJ' ? '00.000.000/0000-00' : '000.000.000-00'}
                  required
                  maxLength={18}
                />
                {tipo === 'PJ' && (
                  <button
                    type="button"
                    onClick={handleConsultarCNPJ}
                    disabled={loadingCNPJ}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Consultar CNPJ na ReceitaWS"
                  >
                    {loadingCNPJ ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    ) : (
                      '🔍'
                    )}
                  </button>
                )}
              </div>
              {tipo === 'PJ' && (
                <p className="text-xs text-gray-500 mt-1">
                  {loadingCNPJ ? (
                    <span className="text-blue-600">⏳ Buscando dados na Receita Federal...</span>
                  ) : (
                    <>🔍 Busca automática ao digitar CNPJ completo (ou clique no botão)</>
                  )}
                </p>
              )}
            </div>

            {/* RG/IE */}
            <div className="col-span-12 md:col-span-4">
              <label htmlFor="rg_ie" className="block text-sm font-medium text-gray-700 mb-1">
                {tipo === 'PJ' ? 'Inscrição Estadual' : 'RG'}
              </label>
              <input
                type="text"
                id="rg_ie"
                value={formData.rg_ie || ''}
                onChange={(e) => handleChange('rg_ie', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder={tipo === 'PJ' ? 'Inscrição Estadual' : 'RG'}
                maxLength={20}
              />
            </div>

            {/* Inscrição Municipal */}
            <div className="col-span-12 md:col-span-4">
              <label htmlFor="inscricao_municipal" className="block text-sm font-medium text-gray-700 mb-1">
                Inscrição Municipal
              </label>
              <input
                type="text"
                id="inscricao_municipal"
                value={formData.inscricao_municipal || ''}
                onChange={(e) => handleChange('inscricao_municipal', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Inscrição Municipal"
                maxLength={20}
              />
            </div>

          </div>
        </div>

        {/* ==================== SEÇÃO 3: CONTATO ==================== */}
        <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
            📧 Contato
          </h2>
          
          <div className="grid grid-cols-12 gap-4">
            
            {/* Email Principal */}
            <div className="col-span-12 md:col-span-6">
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Email Principal
              </label>
              <input
                type="email"
                id="email"
                value={formData.email || ''}
                onChange={(e) => handleChange('email', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="contato@empresa.com.br"
                maxLength={150}
              />
            </div>

            {/* Email Financeiro */}
            <div className="col-span-12 md:col-span-6">
              <label htmlFor="email_financeiro" className="block text-sm font-medium text-gray-700 mb-1">
                Email Financeiro
              </label>
              <input
                type="email"
                id="email_financeiro"
                value={formData.email_financeiro || ''}
                onChange={(e) => handleChange('email_financeiro', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="financeiro@empresa.com.br"
                maxLength={150}
              />
            </div>

            {/* Telefone */}
            <div className="col-span-12 md:col-span-4">
              <label htmlFor="telefone" className="block text-sm font-medium text-gray-700 mb-1">
                Telefone
              </label>
              <input
                type="tel"
                id="telefone"
                value={formData.telefone ? mascaraTelefone(formData.telefone) : ''}
                onChange={(e) => handleChange('telefone', e.target.value.replace(/\D/g, ''))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="(11) 1234-5678"
                maxLength={15}
              />
            </div>

            {/* Celular */}
            <div className="col-span-12 md:col-span-4">
              <label htmlFor="celular" className="block text-sm font-medium text-gray-700 mb-1">
                Celular
              </label>
              <input
                type="tel"
                id="celular"
                value={formData.celular ? mascaraTelefone(formData.celular) : ''}
                onChange={(e) => handleChange('celular', e.target.value.replace(/\D/g, ''))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="(11) 99999-9999"
                maxLength={15}
              />
            </div>

            {/* WhatsApp */}
            <div className="col-span-12 md:col-span-4">
              <label htmlFor="whatsapp" className="block text-sm font-medium text-gray-700 mb-1">
                WhatsApp
              </label>
              <input
                type="tel"
                id="whatsapp"
                value={formData.whatsapp ? mascaraTelefone(formData.whatsapp) : ''}
                onChange={(e) => handleChange('whatsapp', e.target.value.replace(/\D/g, ''))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="(11) 99999-9999"
                maxLength={15}
              />
            </div>

            {/* Website */}
            <div className="col-span-12">
              <label htmlFor="website" className="block text-sm font-medium text-gray-700 mb-1">
                Website
              </label>
              <input
                type="url"
                id="website"
                value={formData.website || ''}
                onChange={(e) => handleChange('website', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="https://www.empresa.com.br"
                maxLength={200}
              />
            </div>

          </div>
        </div>

        {/* ==================== SEÇÃO 4: CONTATO RESPONSÁVEL ==================== */}
        <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
            👔 Contato Responsável
          </h2>
          
          <div className="grid grid-cols-12 gap-4">
            
            <div className="col-span-12 md:col-span-6">
              <label htmlFor="contato_nome" className="block text-sm font-medium text-gray-700 mb-1">
                Nome do Responsável
              </label>
              <input
                type="text"
                id="contato_nome"
                value={formData.contato_nome || ''}
                onChange={(e) => handleChange('contato_nome', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Nome do contato"
                maxLength={100}
              />
            </div>

            <div className="col-span-12 md:col-span-6">
              <label htmlFor="contato_cargo" className="block text-sm font-medium text-gray-700 mb-1">
                Cargo
              </label>
              <input
                type="text"
                id="contato_cargo"
                value={formData.contato_cargo || ''}
                onChange={(e) => handleChange('contato_cargo', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Ex: Gerente, Diretor"
                maxLength={100}
              />
            </div>

            <div className="col-span-12 md:col-span-6">
              <label htmlFor="contato_email" className="block text-sm font-medium text-gray-700 mb-1">
                Email do Contato
              </label>
              <input
                type="email"
                id="contato_email"
                value={formData.contato_email || ''}
                onChange={(e) => handleChange('contato_email', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="contato@empresa.com.br"
                maxLength={150}
              />
            </div>

            <div className="col-span-12 md:col-span-6">
              <label htmlFor="contato_telefone" className="block text-sm font-medium text-gray-700 mb-1">
                Telefone do Contato
              </label>
              <input
                type="tel"
                id="contato_telefone"
                value={formData.contato_telefone ? mascaraTelefone(formData.contato_telefone) : ''}
                onChange={(e) => handleChange('contato_telefone', e.target.value.replace(/\D/g, ''))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="(11) 99999-9999"
                maxLength={15}
              />
            </div>

          </div>
        </div>
        </>
        )}

        {/* ==================== ABA 3: ENDEREÇO ==================== */}
        {activeTab === 'endereco' && (
        <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
            📍 Endereço
          </h2>
          
          <div className="grid grid-cols-12 gap-4">
            
            {/* CEP com botão consultar */}
            <div className="col-span-12 md:col-span-3">
              <label htmlFor="cep" className="block text-sm font-medium text-gray-700 mb-1">
                CEP
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  id="cep"
                  value={formData.cep ? mascaraCEP(formData.cep) : ''}
                  onChange={(e) => handleChange('cep', e.target.value.replace(/\D/g, ''))}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="00000-000"
                  maxLength={9}
                />
                <button
                  type="button"
                  onClick={handleConsultarCEP}
                  disabled={loadingCEP}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Consultar CEP no ViaCEP"
                >
                  {loadingCEP ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  ) : (
                    '🔍'
                  )}
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                {loadingCEP ? (
                  <span className="text-blue-600">⏳ Buscando endereço...</span>
                ) : (
                  <>📍 Busca automática ao digitar CEP completo (ou clique no botão)</>
                )}
              </p>
            </div>

            {/* Endereço */}
            <div className="col-span-12 md:col-span-6">
              <label htmlFor="endereco" className="block text-sm font-medium text-gray-700 mb-1">
                Endereço
              </label>
              <input
                type="text"
                id="endereco"
                value={formData.endereco || ''}
                onChange={(e) => handleChange('endereco', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Rua, Avenida, etc."
                maxLength={200}
              />
            </div>

            {/* Número */}
            <div className="col-span-12 md:col-span-3">
              <label htmlFor="numero" className="block text-sm font-medium text-gray-700 mb-1">
                Número
              </label>
              <input
                type="text"
                id="numero"
                value={formData.numero || ''}
                onChange={(e) => handleChange('numero', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="123"
                maxLength={20}
              />
            </div>

            {/* Complemento */}
            <div className="col-span-12 md:col-span-4">
              <label htmlFor="complemento" className="block text-sm font-medium text-gray-700 mb-1">
                Complemento
              </label>
              <input
                type="text"
                id="complemento"
                value={formData.complemento || ''}
                onChange={(e) => handleChange('complemento', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Apt, Sala, etc."
                maxLength={100}
              />
            </div>

            {/* Bairro */}
            <div className="col-span-12 md:col-span-4">
              <label htmlFor="bairro" className="block text-sm font-medium text-gray-700 mb-1">
                Bairro
              </label>
              <input
                type="text"
                id="bairro"
                value={formData.bairro || ''}
                onChange={(e) => handleChange('bairro', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Nome do bairro"
                maxLength={100}
              />
            </div>

            {/* Cidade */}
            <div className="col-span-12 md:col-span-3">
              <label htmlFor="cidade" className="block text-sm font-medium text-gray-700 mb-1">
                Cidade
              </label>
              <input
                type="text"
                id="cidade"
                value={formData.cidade || ''}
                onChange={(e) => handleChange('cidade', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Nome da cidade"
                maxLength={100}
              />
            </div>

            {/* Estado (UF) */}
            <div className="col-span-12 md:col-span-1">
              <label htmlFor="estado" className="block text-sm font-medium text-gray-700 mb-1">
                UF
              </label>
              <input
                type="text"
                id="estado"
                value={formData.estado || ''}
                onChange={(e) => handleChange('estado', e.target.value.toUpperCase())}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 uppercase"
                placeholder="SP"
                maxLength={2}
              />
            </div>

          </div>
        </div>
        )}

        {/* ==================== ABA 4: COMERCIAL & BANCÁRIO ==================== */}
        {activeTab === 'comercial-bancario' && (
        <>
        {/* SEÇÃO 6: COMERCIAL/FINANCEIRO */}
        <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
            💼 Informações Comerciais e Financeiras
          </h2>
          
          <div className="grid grid-cols-12 gap-4">
            
            {/* Condições Pagamento */}
            <div className="col-span-12 md:col-span-6">
              <label htmlFor="condicoes_pagamento" className="block text-sm font-medium text-gray-700 mb-1">
                Condições de Pagamento
              </label>
              <input
                type="text"
                id="condicoes_pagamento"
                value={formData.condicoes_pagamento || ''}
                onChange={(e) => handleChange('condicoes_pagamento', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Ex: 30/60 dias"
                maxLength={100}
              />
            </div>

            {/* Prazo Entrega */}
            <div className="col-span-12 md:col-span-6">
              <label htmlFor="prazo_entrega" className="block text-sm font-medium text-gray-700 mb-1">
                Prazo de Entrega
              </label>
              <input
                type="text"
                id="prazo_entrega"
                value={formData.prazo_entrega || ''}
                onChange={(e) => handleChange('prazo_entrega', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Ex: 5-10 dias úteis"
                maxLength={50}
              />
            </div>

            {/* Limite Crédito */}
            <div className="col-span-12 md:col-span-4">
              <label htmlFor="limite_credito" className="block text-sm font-medium text-gray-700 mb-1">
                Limite de Crédito (R$)
              </label>
              <input
                type="number"
                id="limite_credito"
                value={formData.limite_credito || ''}
                onChange={(e) => handleChange('limite_credito', parseFloat(e.target.value) || undefined)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="0.00"
                min="0"
                step="0.01"
              />
            </div>

            {/* Prazo Pagamento Padrão */}
            <div className="col-span-12 md:col-span-4">
              <label htmlFor="prazo_pagamento_padrao" className="block text-sm font-medium text-gray-700 mb-1">
                Prazo Pagamento (dias)
              </label>
              <input
                type="number"
                id="prazo_pagamento_padrao"
                value={formData.prazo_pagamento_padrao || ''}
                onChange={(e) => handleChange('prazo_pagamento_padrao', parseInt(e.target.value) || undefined)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="30"
                min="0"
              />
            </div>

            {/* Desconto Padrão */}
            <div className="col-span-12 md:col-span-4">
              <label htmlFor="desconto_padrao" className="block text-sm font-medium text-gray-700 mb-1">
                Desconto Padrão (%)
              </label>
              <input
                type="number"
                id="desconto_padrao"
                value={formData.desconto_padrao || ''}
                onChange={(e) => handleChange('desconto_padrao', parseFloat(e.target.value) || undefined)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="0.00"
                min="0"
                max="100"
                step="0.01"
              />
            </div>

          </div>
        </div>

        {/* ==================== SEÇÃO 7: DADOS BANCÁRIOS ==================== */}
        <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
            🏦 Dados Bancários
          </h2>
          
          <div className="grid grid-cols-12 gap-4">
            
            <div className="col-span-12 md:col-span-6">
              <label htmlFor="banco_principal" className="block text-sm font-medium text-gray-700 mb-1">
                Banco Principal
              </label>
              <input
                type="text"
                id="banco_principal"
                value={formData.banco_principal || ''}
                onChange={(e) => handleChange('banco_principal', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Nome do banco"
                maxLength={100}
              />
            </div>

            <div className="col-span-12 md:col-span-3">
              <label htmlFor="agencia" className="block text-sm font-medium text-gray-700 mb-1">
                Agência
              </label>
              <input
                type="text"
                id="agencia"
                value={formData.agencia || ''}
                onChange={(e) => handleChange('agencia', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="0000"
                maxLength={20}
              />
            </div>

            <div className="col-span-12 md:col-span-3">
              <label htmlFor="conta" className="block text-sm font-medium text-gray-700 mb-1">
                Conta
              </label>
              <input
                type="text"
                id="conta"
                value={formData.conta || ''}
                onChange={(e) => handleChange('conta', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="00000-0"
                maxLength={30}
              />
            </div>

            <div className="col-span-12">
              <label htmlFor="pix" className="block text-sm font-medium text-gray-700 mb-1">
                Chave PIX
              </label>
              <input
                type="text"
                id="pix"
                value={formData.pix || ''}
                onChange={(e) => handleChange('pix', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="CPF/CNPJ, Email, Telefone ou Chave Aleatória"
                maxLength={100}
              />
            </div>

          </div>
        </div>
        </>
        )}

        {/* ==================== ABA 5: OBSERVAÇÕES ==================== */}
        {activeTab === 'observacoes' && (
        <div className="bg-white shadow-sm rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">
            📝 Observações
          </h2>
          
          <div className="space-y-4">
            
            <div>
              <label htmlFor="observacoes" className="block text-sm font-medium text-gray-700 mb-1">
                Observações Gerais
              </label>
              <textarea
                id="observacoes"
                value={formData.observacoes || ''}
                onChange={(e) => handleChange('observacoes', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Observações sobre o fornecedor..."
                rows={3}
                maxLength={500}
              />
            </div>

            <div>
              <label htmlFor="observacoes_internas" className="block text-sm font-medium text-gray-700 mb-1">
                Observações Internas
              </label>
              <textarea
                id="observacoes_internas"
                value={formData.observacoes_internas || ''}
                onChange={(e) => handleChange('observacoes_internas', e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-yellow-50"
                placeholder="Observações internas (não visíveis ao fornecedor)"
                rows={2}
                maxLength={500}
              />
            </div>

          </div>
        </div>
        )}
        
        {/* Botões de Ação */}
        <div className="flex justify-between items-center">
          <button
            type="button"
            onClick={() => navigate('/suppliers')}
            className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
          >
            ← Voltar
          </button>
          
          <button
            type="submit"
            disabled={createMutation.isPending || updateMutation.isPending}
            className="px-8 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {(createMutation.isPending || updateMutation.isPending) && (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            )}
            💾 {isEditing ? 'Atualizar' : 'Salvar'} Fornecedor
          </button>
        </div>

      </form>
    </div>
  );
}
