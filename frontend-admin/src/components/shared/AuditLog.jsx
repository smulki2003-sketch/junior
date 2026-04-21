import { formatDateTime } from "../../utils/formatters";

export function AuditLog({ entries = [] }) {
  return (
    <div className="rounded-[10px] border border-[var(--table-border)] bg-surface p-3">
      <h4 className="mb-3 font-display text-sm">Audit Log</h4>
      <div className="space-y-2">
        {entries.length === 0 ? (
          <p className="text-xs text-[var(--text-secondary)]">No audit entries.</p>
        ) : (
          entries.map((entry, index) => (
            <div key={entry.id || index} className="rounded-md bg-elevated p-2 text-xs">
              <p>
                <span className="font-medium">{entry.admin_name || "Admin"}</span> — {entry.action}
              </p>
              <p className="text-[var(--text-secondary)]">{formatDateTime(entry.created_at)}</p>
              {entry.reason ? <p className="mt-1 text-[var(--text-label)]">{entry.reason}</p> : null}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

