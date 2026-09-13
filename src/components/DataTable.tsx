import React from 'react';

export interface Column<T> {
  key: string;
  header: string;
  render?: (row: T) => React.ReactNode;
  align?: 'left' | 'center' | 'right';
  width?: string | number;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  onRowClick?: (row: T) => void;
  keyExtractor: (row: T) => string;
  className?: string;
}

export function DataTable<T>({
  columns,
  data,
  onRowClick,
  keyExtractor,
  className = '',
}: DataTableProps<T>) {
  return (
    <div className={`overflow-x-auto rounded-lg border border-[var(--border-hairline)] bg-[var(--surface-raised)] ${className}`}>
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="bg-[var(--surface-sunken)] border-b border-[var(--border-hairline)]">
            {columns.map(col => (
              <th
                key={col.key}
                className="px-4 py-3 text-[10px] font-semibold uppercase tracking-widest text-[var(--text-muted)]"
                style={{
                  textAlign: col.align || 'left',
                  width: col.width,
                }}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-[var(--border-hairline)]">
          {data.map(row => (
            <tr
              key={keyExtractor(row)}
              onClick={() => onRowClick && onRowClick(row)}
              className={`transition-colors text-xs ${
                onRowClick ? 'cursor-pointer hover:bg-[var(--glass-bg)]' : ''
              }`}
            >
              {columns.map(col => (
                <td
                  key={col.key}
                  className="px-4 py-3 text-[var(--text-primary)]"
                  style={{ textAlign: col.align || 'left' }}
                >
                  {col.render
                    ? col.render(row)
                    : (row as Record<string, unknown>)[col.key] != null
                    ? String((row as Record<string, unknown>)[col.key])
                    : '—'}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default DataTable;
