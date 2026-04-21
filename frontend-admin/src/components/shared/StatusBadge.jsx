import { Badge } from "../ui/Badge";

const statusConfig = {
  active: { label: "Active", bg: "var(--status-active-bg)", color: "var(--accent-success)" },
  pending: { label: "Pending", bg: "var(--status-pending-bg)", color: "var(--accent-warning)", pulse: true },
  rejected: { label: "Rejected", bg: "var(--status-danger-bg)", color: "var(--accent-danger)" },
  suspended: { label: "Suspended", bg: "var(--status-danger-bg)", color: "var(--accent-danger)" },
  confirmed: { label: "Confirmed", bg: "var(--status-active-bg)", color: "var(--accent-success)" },
  banned: { label: "Banned", bg: "var(--status-danger-bg)", color: "var(--accent-danger)" },
  failed: { label: "Failed", bg: "var(--status-danger-bg)", color: "var(--accent-danger)" },
  resolved: { label: "Resolved", bg: "var(--status-active-bg)", color: "var(--accent-success)" },
  closed: { label: "Closed", bg: "var(--status-neutral-bg)", color: "var(--text-secondary)" },
  open: { label: "Open", bg: "var(--status-pending-bg)", color: "var(--accent-warning)" },
  in_review: { label: "In Review", bg: "var(--status-pending-bg)", color: "var(--accent-warning)", pulse: true },
  success: { label: "Success", bg: "var(--status-active-bg)", color: "var(--accent-success)" },
  warning: { label: "Warning", bg: "var(--status-pending-bg)", color: "var(--accent-warning)", pulse: true },
  info: { label: "Info", bg: "rgba(59,130,246,0.14)", color: "var(--accent-primary)" },
  urgent: { label: "Urgent", bg: "var(--status-danger-bg)", color: "var(--accent-danger)", pulse: true },
  sent: { label: "Sent", bg: "var(--status-active-bg)", color: "var(--accent-success)" },
  scheduled: { label: "Scheduled", bg: "rgba(59,130,246,0.14)", color: "var(--accent-primary)" },
};

export function StatusBadge({ status }) {
  const key = String(status || "").toLowerCase();
  const cfg = statusConfig[key] || { label: status || "Unknown", bg: "var(--status-neutral-bg)", color: "var(--text-secondary)" };
  return (
    <Badge className={`${cfg.pulse ? "badge-pending" : ""}`} style={{ background: cfg.bg, color: cfg.color }}>
      {cfg.label}
    </Badge>
  );
}
