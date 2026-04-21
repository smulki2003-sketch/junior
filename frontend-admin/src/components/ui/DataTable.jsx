import { Button } from "./Button";
import { Skeleton } from "./Skeleton";

export function DataTable({
  columns,
  data,
  loading,
  emptyText = "No data",
  onRowClick,
  selectable = false,
  selectedIds = [],
  onToggleSelect,
  onToggleSelectAll,
  onSort,
  sortKey,
  sortDirection,
  pagination,
}) {
  if (loading) {
    return (
      <div className="rounded-[10px] border border-[var(--table-border)] bg-surface p-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="mb-2 h-9 w-full" />
        ))}
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-[10px] border border-[var(--table-border)] bg-surface">
      <table className="w-full text-left text-data">
        <thead className="bg-[var(--table-header-bg)] text-[var(--text-label)]">
          <tr>
            {selectable ? (
              <th className="px-3 py-2">
                <input
                  type="checkbox"
                  checked={data.length > 0 && data.every((row) => selectedIds.includes(row.id))}
                  onChange={() => onToggleSelectAll?.(data)}
                />
              </th>
            ) : null}
            {columns.map((col) => (
              <th key={col.key} className="px-3 py-2">
                <button className="inline-flex items-center gap-1" onClick={() => onSort?.(col.key)}>
                  {col.title}
                  {sortKey === col.key ? (sortDirection === "asc" ? "↑" : "↓") : "↕"}
                </button>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.length === 0 ? (
            <tr>
              <td colSpan={columns.length + (selectable ? 1 : 0)} className="px-3 py-8 text-center text-[var(--text-secondary)]">
                {emptyText}
              </td>
            </tr>
          ) : (
            data.map((row, index) => (
              <tr
                key={row.id ?? index}
                className="table-row"
                style={index % 2 === 1 ? { background: "var(--table-row-alt)" } : undefined}
                onClick={() => onRowClick?.(row)}
              >
                {selectable ? (
                  <td className="px-3 py-2" onClick={(e) => e.stopPropagation()}>
                    <input type="checkbox" checked={selectedIds.includes(row.id)} onChange={() => onToggleSelect?.(row.id)} />
                  </td>
                ) : null}
                {columns.map((col) => (
                  <td key={col.key} className="px-3 py-2">
                    {col.render ? col.render(row) : row[col.key]}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
      {pagination ? (
        <div className="flex items-center justify-between border-t border-[var(--table-border)] px-3 py-2 text-xs text-[var(--text-secondary)]">
          <span>
            Showing {(pagination.page - 1) * pagination.pageSize + 1}–{Math.min(pagination.page * pagination.pageSize, pagination.total)} of{" "}
            {pagination.total}
          </span>
          <div className="flex items-center gap-2">
            <Button variant="ghost" onClick={() => pagination.onChange(Math.max(1, pagination.page - 1))}>
              Prev
            </Button>
            <Button variant="ghost" onClick={() => pagination.onChange(pagination.page + 1)}>
              Next
            </Button>
            <input
              className="w-16 rounded-md border border-[var(--border-subtle)] bg-elevated px-2 py-1"
              value={pagination.page}
              onChange={(e) => pagination.onChange(Number(e.target.value) || 1)}
            />
          </div>
        </div>
      ) : null}
    </div>
  );
}

