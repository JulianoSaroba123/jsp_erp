import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getProducts, deleteProduct, Product } from '../api/products';
import { ProductForm } from './Products/ProductForm';
import { usePermissions } from '../auth/usePermissions';
import { LoadingState, ErrorState, EmptyState } from '../components/ui/State';
import { formatCurrencyBRL } from '../lib/format';

export function Products() {
  const [page, setPage] = useState(1);
  const [formMode, setFormMode] = useState<'create' | 'edit' | null>(null);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [subcategoriaFilter, setSubcategoriaFilter] = useState<string>('');
  const [marcaFilter, setMarcaFilter] = useState<string>('');
  const [activeFilter, setActiveFilter] = useState<boolean | undefined>(undefined);
  const pageSize = 10;
  const queryClient = useQueryClient();
  const { canCreate, canUpdate, canDelete } = usePermissions();

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['products', page, searchQuery, categoryFilter, subcategoriaFilter, marcaFilter, activeFilter],
    queryFn: () => getProducts({ 
      page, 
      page_size: pageSize,
      q: searchQuery || undefined,
      category: categoryFilter || undefined,
      active: activeFilter,
    }),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteProduct,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
    onError: (error: any) => {
      const status = error.response?.status;
      if (status === 404) {
        alert('Produto não encontrado ou já foi excluído');
      } else if (status === 403) {
        alert('Você não tem permissão para excluir este produto');
      } else {
        alert(error.response?.data?.detail || 'Erro ao excluir produto');
      }
    },
  });

  const handleDelete = (productId: string, productName: string) => {
    const confirmed = window.confirm(
      `Tem certeza que deseja excluir o produto "${productName}"?\n\nEsta ação não pode ser desfeita.`
    );
    if (confirmed) {
      deleteMutation.mutate(productId);
    }
  };

  const handleEdit = (product: Product) => {
    setEditingProduct(product);
    setFormMode('edit');
  };

  const handleCloseForm = () => {
    setFormMode(null);
    setEditingProduct(null);
  };

  const handleOpenCreate = () => {
    setEditingProduct(null);
    setFormMode('create');
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
    setPage(1); // Reset para primeira página ao buscar
  };

  if (isLoading) {
    return <LoadingState description="Carregando produtos..." />;
  }

  if (isError) {
    return (
      <ErrorState 
        title="Erro ao carregar produtos"
        description={error instanceof Error ? error.message : 'Não foi possível carregar. Tente novamente.'}
      />
    );
  }

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Produtos</h1>
        {canCreate('products') && (
          <button 
            onClick={handleOpenCreate}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            + Novo Produto
          </button>
        )}
      </div>

      {/* Barra de busca e filtros */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Buscar (nome ou código)
            </label>
            <input
              type="text"
              value={searchQuery}
              onChange={handleSearchChange}
              placeholder="Digite para buscar..."
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Categoria
            </label>
            <input
              type="text"
              value={categoryFilter}
              onChange={(e) => { setCategoryFilter(e.target.value); setPage(1); }}
              placeholder="Filtrar por categoria..."
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Subcategoria
            </label>
            <input
              type="text"
              value={subcategoriaFilter}
              onChange={(e) => { setSubcategoriaFilter(e.target.value); setPage(1); }}
              placeholder="Filtrar subcategoria..."
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Marca
            </label>
            <input
              type="text"
              value={marcaFilter}
              onChange={(e) => { setMarcaFilter(e.target.value); setPage(1); }}
              placeholder="Filtrar por marca..."
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Status
            </label>
            <select
              aria-label="Filtro de status"
              value={activeFilter === undefined ? '' : activeFilter ? 'true' : 'false'}
              onChange={(e) => {
                const val = e.target.value;
                setActiveFilter(val === '' ? undefined : val === 'true');
                setPage(1);
              }}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            >
              <option value="">Todos</option>
              <option value="true">Ativos</option>
              <option value="false">Inativos</option>
            </select>
          </div>
        </div>
      </div>

      {/* Formulário de criação/edição */}
      {formMode && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            {formMode === 'create' ? 'Criar Novo Produto' : 'Editar Produto'}
          </h2>
          <ProductForm 
            mode={formMode}
            initialData={editingProduct || undefined}
            onSuccess={handleCloseForm} 
            onCancel={handleCloseForm}
          />
        </div>
      )}

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        {data && data.items.length === 0 ? (
          <EmptyState 
            title="Nenhum produto encontrado"
            description={searchQuery || categoryFilter || subcategoriaFilter || marcaFilter ? 'Tente ajustar os filtros de busca' : 'Comece criando seu primeiro produto'}
            actionLabel={canCreate('products') && !searchQuery && !categoryFilter && !subcategoriaFilter && !marcaFilter ? '+ Novo Produto' : undefined}
            onAction={canCreate('products') && !searchQuery && !categoryFilter && !subcategoriaFilter && !marcaFilter ? handleOpenCreate : undefined}
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Código
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Nome / Marca
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Categoria
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Custo
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Venda
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Markup
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Estoque
                    </th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Ações
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {data?.items.map((product) => {
                    const situacaoEstoque = product.controla_estoque 
                      ? (product.stock_qty <= product.stock_min ? 'baixo' : 'normal')
                      : 'sem_controle';
                    
                    return (
                    <tr key={product.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-700 dark:text-gray-300">{product.code || '-'}</div>
                        {product.codigo_barras && (
                          <div className="text-xs text-gray-500 dark:text-gray-400" title="Código de Barras">📊 {product.codigo_barras}</div>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm font-medium text-gray-900 dark:text-gray-100">{product.name}</div>
                        {product.marca && (
                          <div className="text-xs text-gray-500 dark:text-gray-400">{product.marca}{product.modelo ? ` - ${product.modelo}` : ''}</div>
                        )}
                        {product.unit && (
                          <div className="text-xs text-gray-500 dark:text-gray-400">Un: {product.unit}</div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-700 dark:text-gray-300">{product.category || '-'}</div>
                        {product.subcategoria && (
                          <div className="text-xs text-gray-500 dark:text-gray-400">{product.subcategoria}</div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <div className="text-sm text-gray-700 dark:text-gray-300">{formatCurrencyBRL(product.cost_price)}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <div className="text-sm font-medium text-gray-900 dark:text-gray-100">{formatCurrencyBRL(product.sale_price)}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        {product.markup ? (
                          <div className="text-sm text-blue-600 dark:text-blue-400 font-medium">{product.markup.toFixed(1)}%</div>
                        ) : (
                          <div className="text-sm text-gray-400 dark:text-gray-500">-</div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        {product.controla_estoque ? (
                          <>
                            <div className={`text-sm font-medium ${
                              situacaoEstoque === 'baixo' 
                                ? 'text-red-600 dark:text-red-400' 
                                : 'text-gray-900 dark:text-gray-100'
                            }`}>
                              {product.stock_qty}
                            </div>
                            <div className="text-xs text-gray-500 dark:text-gray-400">Mín: {product.stock_min}</div>
                            {product.estoque_maximo && (
                              <div className="text-xs text-gray-500 dark:text-gray-400">Máx: {product.estoque_maximo}</div>
                            )}
                          </>
                        ) : (
                          <div className="text-xs text-gray-400 dark:text-gray-500">Sem controle</div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          product.active 
                            ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300' 
                            : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                        }`}>
                          {product.active ? 'Ativo' : 'Inativo'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                        {canUpdate('products') && (
                          <button
                            onClick={() => handleEdit(product)}
                            className="text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-300 transition-colors"
                          >
                            Editar
                          </button>
                        )}
                        {canDelete('products') && (
                          <button
                            onClick={() => handleDelete(product.id, product.name)}
                            disabled={deleteMutation.isPending}
                            className="text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300 disabled:opacity-50 transition-colors"
                          >
                            Excluir
                          </button>
                        )}
                      </td>
                    </tr>
                  )})}
                </tbody>
              </table>
            </div>

            {/* Paginação */}
            {totalPages > 1 && (
              <div className="bg-white dark:bg-gray-800 px-4 py-3 flex items-center justify-between border-t border-gray-200 dark:border-gray-700 sm:px-6">
                <div className="flex-1 flex justify-between sm:hidden">
                  <button
                    onClick={() => setPage(page - 1)}
                    disabled={page === 1}
                    className="relative inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Anterior
                  </button>
                  <button
                    onClick={() => setPage(page + 1)}
                    disabled={page >= totalPages}
                    className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Próximo
                  </button>
                </div>
                <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      Mostrando{' '}
                      <span className="font-medium">{(page - 1) * pageSize + 1}</span>
                      {' '}até{' '}
                      <span className="font-medium">
                        {Math.min(page * pageSize, data?.total || 0)}
                      </span>
                      {' '}de{' '}
                      <span className="font-medium">{data?.total || 0}</span>
                      {' '}resultados
                    </p>
                  </div>
                  <div>
                    <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                      <button
                        onClick={() => setPage(page - 1)}
                        disabled={page === 1}
                        className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm font-medium text-gray-500 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Anterior
                      </button>
                      <span className="relative inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm font-medium text-gray-700 dark:text-gray-300">
                        Página {page} de {totalPages}
                      </span>
                      <button
                        onClick={() => setPage(page + 1)}
                        disabled={page >= totalPages}
                        className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm font-medium text-gray-500 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Próximo
                      </button>
                    </nav>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
