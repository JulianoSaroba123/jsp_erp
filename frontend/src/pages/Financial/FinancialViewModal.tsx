import { FinancialEntry } from '../../api/financial';
import { formatCurrencyBRL, formatDateBR } from '../../lib/format';

interface FinancialViewModalProps {
  entry: FinancialEntry;
  onClose: () => void;
}

export function FinancialViewModal({ entry, onClose }: FinancialViewModalProps) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-6 flex justify-between items-center">
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
            Detalhes do Lançamento
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 text-2xl"
          >
            ✕
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* ========== INFORMAÇÕES PRINCIPAIS ========== */}
          <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg">
            <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-4">📋 Informações Principais</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-500 dark:text-gray-400">Tipo</label>
                <p className="font-medium text-gray-900 dark:text-gray-100 mt-1">
                  {entry.kind === 'revenue' ? (
                    <span className="inline-flex items-center px-3 py-1 rounded-full bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300">
                      💰 Receita
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-3 py-1 rounded-full bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300">
                      📉 Despesa
                    </span>
                  )}
                </p>
              </div>

              <div>
                <label className="text-xs text-gray-500 dark:text-gray-400">Status</label>
                <p className="font-medium text-gray-900 dark:text-gray-100 mt-1">
                  {entry.status === 'paid' && (
                    <span className="inline-flex items-center px-3 py-1 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300">
                      ✓ Pago
                    </span>
                  )}
                  {entry.status === 'pending' && (
                    <span className="inline-flex items-center px-3 py-1 rounded-full bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300">
                      ⏳ Pendente
                    </span>
                  )}
                  {entry.status === 'canceled' && (
                    <span className="inline-flex items-center px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300">
                      ✕ Cancelado
                    </span>
                  )}
                </p>
              </div>

              <div>
                <label className="text-xs text-gray-500 dark:text-gray-400">Valor</label>
                <p className={`font-bold text-lg mt-1 ${entry.kind === 'revenue' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                  {formatCurrencyBRL(entry.amount)}
                </p>
              </div>

              <div>
                <label className="text-xs text-gray-500 dark:text-gray-400">Data de Ocorrência</label>
                <p className="font-medium text-gray-900 dark:text-gray-100 mt-1">
                  {formatDateBR(entry.occurred_at)}
                </p>
              </div>
            </div>

            <div className="mt-4">
              <label className="text-xs text-gray-500 dark:text-gray-400">Descrição</label>
              <p className="font-medium text-gray-900 dark:text-gray-100 mt-1">
                {entry.description}
              </p>
            </div>
          </div>

          {/* ========== CATEGORIZAÇÃO ========== */}
          {(entry.category || entry.subcategory) && (
            <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg">
              <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-4">🏷️ Categorização</h3>
              <div className="grid grid-cols-2 gap-4">
                {entry.category && (
                  <div>
                    <label className="text-xs text-gray-500 dark:text-gray-400">Categoria</label>
                    <p className="font-medium text-gray-900 dark:text-gray-100 mt-1">{entry.category}</p>
                  </div>
                )}
                {entry.subcategory && (
                  <div>
                    <label className="text-xs text-gray-500 dark:text-gray-400">Subcategoria</label>
                    <p className="font-medium text-gray-900 dark:text-gray-100 mt-1">{entry.subcategory}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ========== DATAS ADICIONAIS ========== */}
          {(entry.due_date || entry.payment_date) && (
            <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg">
              <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-4">📅 Datas Adicionais</h3>
              <div className="grid grid-cols-2 gap-4">
                {entry.due_date && (
                  <div>
                    <label className="text-xs text-gray-500 dark:text-gray-400">Vencimento</label>
                    <p className="font-medium text-gray-900 dark:text-gray-100 mt-1">{formatDateBR(entry.due_date)}</p>
                  </div>
                )}
                {entry.payment_date && (
                  <div>
                    <label className="text-xs text-gray-500 dark:text-gray-400">Pagamento</label>
                    <p className="font-medium text-gray-900 dark:text-gray-100 mt-1">{formatDateBR(entry.payment_date)}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ========== DOCUMENTO ========== */}
          {(entry.document_number || entry.document_type) && (
            <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg">
              <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-4">📄 Documento</h3>
              <div className="grid grid-cols-2 gap-4">
                {entry.document_number && (
                  <div>
                    <label className="text-xs text-gray-500 dark:text-gray-400">Número</label>
                    <p className="font-medium text-gray-900 dark:text-gray-100 mt-1">{entry.document_number}</p>
                  </div>
                )}
                {entry.document_type && (
                  <div>
                    <label className="text-xs text-gray-500 dark:text-gray-400">Tipo</label>
                    <p className="font-medium text-gray-900 dark:text-gray-100 mt-1">{entry.document_type}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ========== PAGAMENTO ========== */}
          {entry.payment_method && (
            <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg">
              <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-4">💳 Pagamento</h3>
              <div>
                <label className="text-xs text-gray-500 dark:text-gray-400">Forma de Pagamento</label>
                <p className="font-medium text-gray-900 dark:text-gray-100 mt-1 capitalize">
                  {entry.payment_method.replace('_', ' ')}
                </p>
              </div>
            </div>
          )}

          {/* ========== VALORES CALCULADOS ========== */}
          {(entry.original_amount || entry.interest || entry.discount || entry.penalty) && (
            <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg">
              <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-4">💰 Valores Calculados</h3>
              <div className="grid grid-cols-2 gap-4">
                {entry.original_amount && (
                  <div>
                    <label className="text-xs text-gray-500 dark:text-gray-400">Valor Original</label>
                    <p className="font-medium text-gray-900 dark:text-gray-100 mt-1">{formatCurrencyBRL(entry.original_amount)}</p>
                  </div>
                )}
                {entry.interest && (
                  <div>
                    <label className="text-xs text-gray-500 dark:text-gray-400">Juros</label>
                    <p className="font-medium text-red-600 dark:text-red-400 mt-1">+ {formatCurrencyBRL(entry.interest)}</p>
                  </div>
                )}
                {entry.discount && (
                  <div>
                    <label className="text-xs text-gray-500 dark:text-gray-400">Desconto</label>
                    <p className="font-medium text-green-600 dark:text-green-400 mt-1">- {formatCurrencyBRL(entry.discount)}</p>
                  </div>
                )}
                {entry.penalty && (
                  <div>
                    <label className="text-xs text-gray-500 dark:text-gray-400">Multa</label>
                    <p className="font-medium text-red-600 dark:text-red-400 mt-1">+ {formatCurrencyBRL(entry.penalty)}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ========== OBSERVAÇÕES ========== */}
          {entry.notes && (
            <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg">
              <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-4">📝 Observações</h3>
              <p className="text-gray-900 dark:text-gray-100 whitespace-pre-wrap">{entry.notes}</p>
            </div>
          )}

          {/* ========== METADADOS ========== */}
          <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg">
            <h3 className="font-semibold text-gray-700 dark:text-gray-300 mb-4">ℹ️ Informações do Sistema</h3>
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div>
                <label className="text-gray-500 dark:text-gray-400">ID</label>
                <p className="font-mono text-gray-900 dark:text-gray-100 mt-1">{entry.id}</p>
              </div>
              <div>
                <label className="text-gray-500 dark:text-gray-400">Criado em</label>
                <p className="text-gray-900 dark:text-gray-100 mt-1">{formatDateBR(entry.created_at)}</p>
              </div>
              {entry.origin && (
                <div>
                  <label className="text-gray-500 dark:text-gray-400">Origem</label>
                  <p className="text-gray-900 dark:text-gray-100 mt-1 capitalize">{entry.origin}</p>
                </div>
              )}
              {entry.is_recurring && (
                <div>
                  <label className="text-gray-500 dark:text-gray-400">Recorrente</label>
                  <p className="text-gray-900 dark:text-gray-100 mt-1">
                    Sim {entry.recurrence_frequency && `(${entry.recurrence_frequency})`}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="sticky bottom-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-6">
          <button
            onClick={onClose}
            className="w-full bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-100 px-4 py-2 rounded-lg font-medium transition-colors"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
}
