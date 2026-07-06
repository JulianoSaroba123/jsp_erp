import { useMemo, useState, type ReactNode } from 'react';
import { Button, EmptyState, ErrorState, Input, LoadingBlock } from '../ui';

export interface DataTableColumn<T> {
  id: string;
  header: ReactNode;
  accessorKey?: keyof T;
  accessorFn?: (row: T) => unknown;
  cell?: (value: unknown, row: T) => ReactNode;
  sortable?: boolean;
  searchable?: boolean;
  width?: string;
  align?: 'left' | 'center' | 'right';
}

export interface DataTableEnterpriseProps<T extends Record<string, unknown>> {
  columns: Array<DataTableColumn<T>>;
  data: T[];
  loading?: boolean;
  error?: string | null;
  rowKey?: (row: T, index: number) => string;
  defaultPageSize?: number;
  pageSizeOptions?: number[];
  searchPlaceholder?: string;
  title?: string;
  subtitle?: string;
  toolbarSlot?: ReactNode;
  actionsSlot?: ReactNode;
  renderRowActions?: (row: T) => ReactNode;
  emptyTitle?: string;
  emptyDescription?: string;
}

type SortDirection = 'asc' | 'desc';

function resolveValue<T extends Record<string, unknown>>(row: T, column: DataTableColumn<T>) {
  if (column.accessorFn) {
    return column.accessorFn(row);
  }

  if (column.accessorKey) {
    return row[column.accessorKey];
  }

  return undefined;
}

function normalizeSearchValue(value: unknown) {
  if (value == null) {
    return '';
  }

  if (typeof value === 'string') {
    return value.toLowerCase();
  }

  if (typeof value === 'number' || typeof value === 'boolean') {
    return String(value).toLowerCase();
  }

  return '';
}

function toComparable(value: unknown) {
  if (typeof value === 'number') {
    return value;
  }

  if (typeof value === 'string') {
    return value.toLowerCase();
  }

  if (typeof value === 'boolean') {
    return value ? 1 : 0;
  }

  return '';
}

export function DataTableEnterprise<T extends Record<string, unknown>>({
  columns,
  data,
  loading = false,
  error,
  rowKey,
  defaultPageSize = 10,
  pageSizeOptions = [10, 20, 50],
  searchPlaceholder = 'Buscar registros',
  title,
  subtitle,
  toolbarSlot,
  actionsSlot,
  renderRowActions,
  emptyTitle = 'Nenhum registro encontrado',
  emptyDescription = 'Ajuste os filtros ou atualize os dados para tentar novamente.',
}: DataTableEnterpriseProps<T>) {
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(defaultPageSize);
  const [sortState, setSortState] = useState<{ columnId: string; direction: SortDirection } | null>(null);

  const searchableColumns = useMemo(() => {
    return columns.filter((column) => column.searchable !== false);
  }, [columns]);

  const filteredData = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase();

    if (!normalizedSearch) {
      return data;
    }

    return data.filter((row) => {
      return searchableColumns.some((column) => {
        const value = resolveValue(row, column);
        return normalizeSearchValue(value).includes(normalizedSearch);
      });
    });
  }, [data, searchableColumns, searchTerm]);

  const sortedData = useMemo(() => {
    if (!sortState) {
      return filteredData;
    }

    const column = columns.find((item) => item.id === sortState.columnId);
    if (!column) {
      return filteredData;
    }

    const sorted = [...filteredData].sort((a, b) => {
      const aValue = toComparable(resolveValue(a, column));
      const bValue = toComparable(resolveValue(b, column));

      if (aValue < bValue) {
        return sortState.direction === 'asc' ? -1 : 1;
      }

      if (aValue > bValue) {
        return sortState.direction === 'asc' ? 1 : -1;
      }

      return 0;
    });

    return sorted;
  }, [columns, filteredData, sortState]);

  const totalPages = Math.max(1, Math.ceil(sortedData.length / pageSize));

  const pagedData = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return sortedData.slice(start, start + pageSize);
  }, [currentPage, pageSize, sortedData]);

  const canGoPrev = currentPage > 1;
  const canGoNext = currentPage < totalPages;

  const toggleSort = (column: DataTableColumn<T>) => {
    if (!column.sortable) {
      return;
    }

    setCurrentPage(1);

    setSortState((current) => {
      if (!current || current.columnId !== column.id) {
        return { columnId: column.id, direction: 'asc' };
      }

      if (current.direction === 'asc') {
        return { columnId: column.id, direction: 'desc' };
      }

      return null;
    });
  };

  if (loading) {
    return <LoadingBlock title="Carregando tabela" description="Preparando dados para exibicao." />;
  }

  if (error) {
    return <ErrorState title="Erro ao carregar dados" description={error} />;
  }

  return (
    <section
      className="border"
      style={{
        borderColor: 'var(--color-border)',
        borderRadius: 'var(--radius-lg)',
        backgroundColor: 'var(--color-surface)',
        boxShadow: 'var(--shadow-sm)',
      }}
    >
      <header className="p-4 border-b" style={{ borderColor: 'var(--color-border)' }}>
        {(title || subtitle) && (
          <div className="mb-4">
            {title && (
              <h3 className="text-base font-semibold" style={{ color: 'var(--color-text)' }}>
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-sm mt-1" style={{ color: 'var(--color-text-muted)' }}>
                {subtitle}
              </p>
            )}
          </div>
        )}

        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div className="w-full md:max-w-sm">
            <Input
              value={searchTerm}
              onChange={(event) => {
                setSearchTerm(event.target.value);
                setCurrentPage(1);
              }}
              placeholder={searchPlaceholder}
              aria-label="Busca na tabela"
            />
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {toolbarSlot}
            {actionsSlot}
          </div>
        </div>
      </header>

      {sortedData.length === 0 ? (
        <div className="p-6">
          <EmptyState title={emptyTitle} description={emptyDescription} />
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] border-collapse">
              <thead>
                <tr style={{ backgroundColor: 'var(--color-surface-muted)' }}>
                  {columns.map((column) => {
                    const isSorted = sortState?.columnId === column.id;
                    const sortIndicator = isSorted
                      ? sortState?.direction === 'asc'
                        ? '↑'
                        : '↓'
                      : '↕';

                    return (
                      <th
                        key={column.id}
                        className="px-4 py-3 text-xs font-semibold uppercase tracking-wide"
                        style={{
                          color: 'var(--color-text-muted)',
                          textAlign: column.align || 'left',
                          width: column.width,
                        }}
                      >
                        <button
                          type="button"
                          onClick={() => toggleSort(column)}
                          disabled={!column.sortable}
                          className="inline-flex items-center gap-2 disabled:cursor-default"
                          style={{ color: 'inherit' }}
                        >
                          <span>{column.header}</span>
                          {column.sortable && <span aria-hidden="true">{sortIndicator}</span>}
                        </button>
                      </th>
                    );
                  })}

                  {renderRowActions && (
                    <th
                      className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-right"
                      style={{ color: 'var(--color-text-muted)' }}
                    >
                      Acoes
                    </th>
                  )}
                </tr>
              </thead>

              <tbody>
                {pagedData.map((row, index) => {
                  const key = rowKey ? rowKey(row, index) : String(index);

                  return (
                    <tr key={key} className="border-t" style={{ borderColor: 'var(--color-border)' }}>
                      {columns.map((column) => {
                        const value = resolveValue(row, column);
                        const rendered = column.cell ? column.cell(value, row) : String(value ?? '-');

                        return (
                          <td
                            key={column.id}
                            className="px-4 py-3 text-sm"
                            style={{ color: 'var(--color-text)', textAlign: column.align || 'left' }}
                          >
                            {rendered}
                          </td>
                        );
                      })}

                      {renderRowActions && (
                        <td className="px-4 py-3 text-right">
                          <div className="inline-flex items-center gap-2">{renderRowActions(row)}</div>
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <footer className="p-4 border-t flex flex-col gap-3 md:flex-row md:items-center md:justify-between" style={{ borderColor: 'var(--color-border)' }}>
            <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
              Mostrando {(currentPage - 1) * pageSize + 1} a {Math.min(currentPage * pageSize, sortedData.length)} de {sortedData.length} registro(s)
            </p>

            <div className="flex items-center gap-2">
              <label className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
                Linhas
              </label>
              <select
                value={pageSize}
                onChange={(event) => {
                  setPageSize(Number(event.target.value));
                  setCurrentPage(1);
                }}
                className="h-9 px-2 border text-sm"
                style={{
                  borderColor: 'var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--color-surface)',
                  color: 'var(--color-text)',
                }}
              >
                {pageSizeOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>

              <Button variant="secondary" size="sm" disabled={!canGoPrev} onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}>
                Anterior
              </Button>
              <span className="text-sm px-2" style={{ color: 'var(--color-text-muted)' }}>
                {currentPage}/{totalPages}
              </span>
              <Button variant="secondary" size="sm" disabled={!canGoNext} onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}>
                Proxima
              </Button>
            </div>
          </footer>
        </>
      )}
    </section>
  );
}
