import { formatDateTime } from "../../utils/format";

const iconMap = {
  booking: { icon: "🏠", color: "text-primary" },
  payment: { icon: "💳", color: "text-teal" },
  recommendation: { icon: "✨", color: "text-amber" },
  system: { icon: "⚙️", color: "text-[var(--text-secondary)]" },
};

export function NotificationItem({ item, onMarkRead }) {
  const category = item.category || "system";
  const iconEntry = iconMap[category] || iconMap.system;
  return (
    <article
      className={`group relative flex items-start gap-3 rounded-xl border p-4 transition ${
        item.is_read
          ? "border-[var(--border-subtle)] bg-surface"
          : "border-[var(--border-glow)] bg-elevated before:absolute before:inset-y-2 before:left-0 before:w-[3px] before:rounded-full before:bg-primary before:content-['']"
      }`}
    >
      <div className={`text-xl ${iconEntry.color}`}>{iconEntry.icon}</div>
      <div className="min-w-0 flex-1">
        <p className="font-medium">{item.title || "Notification"}</p>
        <p className="text-sm text-[var(--text-secondary)]">{item.body || item.message}</p>
      </div>
      <div className="text-right text-xs text-[var(--text-secondary)]">
        <p>{formatDateTime(item.created_at)}</p>
        {!item.is_read ? (
          <button
            className="mt-2 translate-x-2 text-primary opacity-0 transition group-hover:translate-x-0 group-hover:opacity-100"
            onClick={() => onMarkRead(item)}
          >
            Mark as read
          </button>
        ) : null}
      </div>
    </article>
  );
}

