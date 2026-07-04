import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { getOrders } from '../api/orders';
import { getDRE } from '../api/reports';
import { formatCurrencyBRL, formatDateBR, formatDateISO } from '../lib/format';

export function Dashboard() {
  // Data para período (último mês)
  const today = new Date();
  const lastMonth = new Date(today);
  lastMonth.setMonth(today.getMonth() - 1);
  
  const dateFrom = formatDateISO(lastMonth);
  const dateTo = formatDateISO(today);

  // Buscar total de pedidos
  const { data: ordersData } = useQuery({
    queryKey: ['orders-summary'],
    queryFn: () => getOrders({ page: 1, page_size: 1 }),
  });

  // Buscar DRE do último mês
  const { data: dreData, isLoading: dreLoading, isError: dreError } = useQuery({
    queryKey: ['dre', dateFrom, dateTo],
    queryFn: () => getDRE({ date_from: dateFrom, date_to: dateTo }),
  });

  const totalOrders = ordersData?.total || 0;
  const totalRevenue = dreData?.revenues_paid || 0;
  const totalExpenses = dreData?.expenses_paid || 0;
  const netResult = dreData?.net_result_paid || 0;

  return (
    <div>
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Dashboard</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Período: {formatDateBR(dateFrom)} - {formatDateBR(dateTo)}
        </p>
      </div>

      {dreError && (
        <div className="mb-6 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4">
          <p className="text-sm text-yellow-800 dark:text-yellow-300">
            ⚠️ Não foi possível carregar dados financeiros. Alguns KPIs podem estar indisponíveis.
          </p>
        </div>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Total de Pedidos */}
        <div className="bg-white dark:bg-gray-700 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0 bg-blue-500 rounded-md p-3">
              <span className="text-white text-2xl">📦</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-300">Total de Pedidos</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">{totalOrders}</p>
            </div>
          </div>
        </div>

        {/* Receitas */}
        <div className="bg-white dark:bg-gray-700 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0 bg-green-500 rounded-md p-3">
              <span className="text-white text-2xl">💰</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-300">Receitas (Pagas)</p>
              {dreLoading ? (
                <p className="text-lg text-gray-400">Carregando...</p>
              ) : (
                <p className="text-2xl font-semibold text-green-600 dark:text-green-400">{formatCurrencyBRL(totalRevenue)}</p>
              )}
            </div>
          </div>
        </div>

        {/* Despesas */}
        <div className="bg-white dark:bg-gray-700 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0 bg-red-500 rounded-md p-3">
              <span className="text-white text-2xl">📉</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-300">Despesas (Pagas)</p>
              {dreLoading ? (
                <p className="text-lg text-gray-400">Carregando...</p>
              ) : (
                <p className="text-2xl font-semibold text-red-600 dark:text-red-400">{formatCurrencyBRL(totalExpenses)}</p>
              )}
            </div>
          </div>
        </div>

        {/* Resultado Líquido */}
        <div className="bg-white dark:bg-gray-700 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className={`flex-shrink-0 ${netResult >= 0 ? 'bg-purple-500' : 'bg-orange-500'} rounded-md p-3`}>
              <span className="text-white text-2xl">{netResult >= 0 ? '📈' : '⚠️'}</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Resultado Líquido</p>
              {dreLoading ? (
                <p className="text-lg text-gray-400">Carregando...</p>
              ) : (
                <p className={`text-2xl font-semibold ${netResult >= 0 ? 'text-purple-600' : 'text-orange-600'}`}>
                  {formatCurrencyBRL(netResult)}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Atalhos Rápidos */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Acesso Rápido</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <Link
            to="/orders"
            className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <span className="text-3xl mr-3">📦</span>
            <div>
              <p className="font-medium text-gray-900">Pedidos</p>
              <p className="text-sm text-gray-500">Gerenciar pedidos</p>
            </div>
          </Link>

          <Link
            to="/financial"
            className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <span className="text-3xl mr-3">💰</span>
            <div>
              <p className="font-medium text-gray-900">Financeiro</p>
              <p className="text-sm text-gray-500">Lançamentos financeiros</p>
            </div>
          </Link>

          <div className="flex items-center p-4 border border-gray-200 rounded-lg bg-gray-50 opacity-50">
            <span className="text-3xl mr-3">📊</span>
            <div>
              <p className="font-medium text-gray-900">Relatórios</p>
              <p className="text-sm text-gray-500">Em breve</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

