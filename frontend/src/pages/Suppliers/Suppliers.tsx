/**
 * Suppliers.tsx
 * Listagem de fornecedores com filtros avançados
 */

import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { suppliersAPI, SupplierFilters } from '../../api/suppliers';

export default function Suppliers() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // ==================== STATE ====================
  
  const [filters, setFilters] = useState<SupplierFilters>({
    search: '',
    tipo: undefined,
    categoria: undefined,
    classificacao: undefined,
    ativo: true
  });

  // ==================== DATA FETCHING ====================
  
  const { data: suppliers = [], isLoading, error } = useQuery({
    queryKey: ['suppliers', filters],
    queryFn: () => suppliersAPI.list(filters)
  });

  const { data: stats } = useQuery({
    queryKey: ['suppliers-stats'],
    queryFn: suppliersAPI.getStats
  });

  // ==================== MUTATIONS ====================
  
  const deleteMutation = useMutation({
    mutationFn: suppliersAPI.delete,
    onSuccess: () => {
      alert('✅ Fornecedor excluído com sucesso!');
      queryClient.invalidateQueries({ queryKey: ['suppliers'] });
      queryClient.invalidateQueries({ queryKey: ['suppliers-stats'] });
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Erro ao excluir fornecedor';
      alert(`❌ ${message}`);
    }
  });

  // ==================== HANDLERS ====================
  
  const handleFilterChange = (field: keyof SupplierFilters, value: any) => {
    setFilters(prev => ({ ...prev, [field]: value }));
  };

  const handleDelete = (id: string, nome: string) => {
    if (window.confirm(`Tem certeza que deseja excluir o fornecedor "${nome}"?`)) {
      deleteMutation.mutate(id);
    }
  };

  const getBadgeColor = (tipo: 'PF' | 'PJ') => {
    return tipo === 'PJ' 
      ? 'bg-orange-100 text-orange-800 border border-orange-300'
      : 'bg-blue-100 text-blue-800 border border-blue-300';
  };

  const getClassificacaoBadge = (classificacao?: string) => {
    if (!classificacao) return null;
    
    let color = 'bg-gray-100 text-gray-800';
    let emoji = '';
    
    if (classificacao.includes('A')) {
      color = 'bg-green-100 text-green-800';
      emoji = '🟢';
    } else if (classificacao.includes('B')) {
      color = 'bg-yellow-100 text-yellow-800';
      emoji = '🟡';
    } else if (classificacao.includes('C')) {
      color = 'bg-orange-100 text-orange-800';
      emoji = '🟠';
    } else if (classificacao.includes('D')) {
      color = 'bg-red-100 text-red-800';
      emoji = '🔴';
    }
    
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded ${color}`}>
        {emoji} {classificacao.split('-')[0].trim()}
      </span>
    );
  };

  // ==================== RENDER ====================
  
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">❌ Erro ao carregar fornecedores</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      
      {/* Header */}
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">🚚 Fornecedores</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Gerencie seus fornecedores de produtos e serviços
          </p>
        </div>
        <Link
          to="/suppliers/new"
          className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-md"
        >
          ➕ Novo Fornecedor
        </Link>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-gradient-to-br from-cyan-500 to-cyan-600 rounded-lg p-5 text-white shadow-lg">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-cyan-100 text-sm font-medium">Total de Fornecedores</p>
                <p className="text-4xl font-bold mt-2">{stats.total}</p>
              </div>
              <span className="text-5xl opacity-20">🚚</span>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-lg p-5 text-white shadow-lg">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-orange-100 text-sm font-medium">Pessoas Jurídicas</p>
                <p className="text-4xl font-bold mt-2">{stats.por_tipo.PJ}</p>
              </div>
              <span className="text-5xl opacity-20">🏢</span>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg p-5 text-white shadow-lg">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-blue-100 text-sm font-medium">Pessoas Físicas</p>
                <p className="text-4xl font-bold mt-2">{stats.por_tipo.PF}</p>
              </div>
              <span className="text-5xl opacity-20">👤</span>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg border border-gray-200 dark:border-gray-700 p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          
          {/* Search */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Buscar</label>
            <input
              type="text"
              value={filters.search || ''}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              placeholder="Nome, documento ou email..."
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            />
          </div>

          {/* Tipo */}
          <div>
            <label htmlFor="filter-tipo" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Tipo
            </label>
            <select
              id="filter-tipo"
              value={filters.tipo || ''}
              onChange={(e) => handleFilterChange('tipo', e.target.value || undefined)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            >
              <option value="">Todos</option>
              <option value="PJ">🏢 Pessoa Jurídica</option>
              <option value="PF">👤 Pessoa Física</option>
            </select>
          </div>

          {/* Categoria */}
          <div>
            <label htmlFor="filter-categoria" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Categoria
            </label>
            <select
              id="filter-categoria"
              value={filters.categoria || ''}
              onChange={(e) => handleFilterChange('categoria', e.target.value || undefined)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            >
              <option value="">Todas</option>
              <option value="Equipamentos">Equipamentos</option>
              <option value="Serviços">Serviços</option>
              <option value="Matéria-prima">Matéria-prima</option>
              <option value="Software">Software</option>
              <option value="Consultoria">Consultoria</option>
              <option value="Outros">Outros</option>
            </select>
          </div>

          {/* Classificação */}
          <div>
            <label htmlFor="filter-classificacao" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Classificação
            </label>
            <select
              id="filter-classificacao"
              value={filters.classificacao || ''}
              onChange={(e) => handleFilterChange('classificacao', e.target.value || undefined)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            >
              <option value="">Todas</option>
              <option value="Classe A - Premium">🟢 Classe A</option>
              <option value="Classe B - Bom">🟡 Classe B</option>
              <option value="Classe C - Regular">🟠 Classe C</option>
              <option value="Classe D - Atenção">🔴 Classe D</option>
            </select>
          </div>

        </div>
      </div>

      {/* Table */}
      <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : suppliers.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🚚</div>
            <p className="text-gray-500 dark:text-gray-400 text-lg">Nenhum fornecedor encontrado</p>
            <Link
              to="/suppliers/new"
              className="inline-flex items-center gap-2 mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              ➕ Cadastrar Primeiro Fornecedor
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Documento
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Nome / Fantasia
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Tipo
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Categoria
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Classificação
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Cidade/UF
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Telefone
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Ações
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {suppliers.map((supplier) => (
                  <tr key={supplier.id} className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                    
                    {/* Documento */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <code className="text-sm text-gray-900 dark:text-gray-100 font-mono">
                        {supplier.documento_formatado}
                      </code>
                    </td>

                    {/* Nome / Fantasia */}
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {supplier.nome_display}
                      </div>
                      {supplier.email && (
                        <div className="text-sm text-gray-500 dark:text-gray-400">{supplier.email}</div>
                      )}
                    </td>

                    {/* Tipo */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-3 py-1 text-xs font-medium rounded-full ${getBadgeColor(supplier.tipo)}`}>
                        {supplier.tipo === 'PJ' ? '🏢 PJ' : '👤 PF'}
                      </span>
                    </td>

                    {/* Categoria */}
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                      {supplier.categoria || '-'}
                    </td>

                    {/* Classificação */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getClassificacaoBadge(supplier.classificacao)}
                    </td>

                    {/* Cidade/UF */}
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                      {supplier.cidade && supplier.estado 
                        ? `${supplier.cidade}/${supplier.estado}`
                        : supplier.cidade || supplier.estado || '-'
                      }
                    </td>

                    {/* Telefone */}
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                      {supplier.telefone_formatado || supplier.celular_formatado || '-'}
                    </td>

                    {/* Ações */}
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => navigate(`/suppliers/${supplier.id}`)}
                          className="text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-300 px-3 py-1 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded transition-colors"
                          title="Editar"
                        >
                          ✏️ Editar
                        </button>
                        <button
                          onClick={() => handleDelete(supplier.id, supplier.nome_display)}
                          className="text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300 px-3 py-1 hover:bg-red-50 dark:hover:bg-red-900/30 rounded transition-colors"
                          title="Excluir"
                          disabled={deleteMutation.isPending}
                        >
                          🗑️ Excluir
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

      </div>

      {/* Footer Info */}
      {suppliers.length > 0 && (
        <div className="mt-4 text-sm text-gray-600 dark:text-gray-400 text-center">
          Exibindo {suppliers.length} fornecedor(es)
        </div>
      )}

    </div>
  );
}
