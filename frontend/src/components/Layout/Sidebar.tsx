import { Link, useLocation } from 'react-router-dom';

const menuItems = [
  { path: '/dashboard', label: 'Dashboard', icon: '📊' },
  { path: '/orders', label: 'Pedidos', icon: '📦' },
  { path: '/financial', label: 'Financeiro', icon: '💰' },
  { path: '/products', label: 'Produtos', icon: '🏷️' },
  { path: '/suppliers', label: 'Fornecedores', icon: '🚚' },
  { path: '/customers', label: 'Clientes', icon: '👥' },
  { path: '/service-orders', label: 'Ordens de Serviço', icon: '🔧' },
  { path: '/proposals', label: 'Propostas', icon: '📄' },
  { path: '/settings', label: 'Configurações', icon: '⚙️' },
];

export function Sidebar() {
  const location = useLocation();

  return (
    <aside className="w-64 bg-gray-900 dark:bg-gray-950 text-white h-screen">
      <div className="p-6">
        <h2 className="text-2xl font-bold">ERP JSP</h2>
      </div>
      <nav className="mt-6">
        {menuItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`flex items-center px-6 py-3 text-sm font-medium transition-colors ${
              location.pathname === item.path
                ? 'bg-gray-800 dark:bg-gray-900 text-white border-l-4 border-blue-500'
                : 'text-gray-300 hover:bg-gray-800 dark:hover:bg-gray-900 hover:text-white'
            }`}
          >
            <span className="mr-3 text-lg">{item.icon}</span>
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
