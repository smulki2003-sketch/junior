import { formatDistanceToNow, format } from "date-fns";

export function formatDate(value) {
  if (!value) return "-";
  try {
    return format(new Date(value), "MMM d, yyyy");
  } catch {
    return value;
  }
}

export function formatDateTime(value) {
  if (!value) return "-";
  try {
    return format(new Date(value), "MMM d, yyyy HH:mm");
  } catch {
    return value;
  }
}

export function formatRelative(value) {
  if (!value) return "-";
  try {
    return formatDistanceToNow(new Date(value), { addSuffix: true });
  } catch {
    return value;
  }
}

export function formatCurrency(value, currency = "USD") {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(Number(value || 0));
}

export function formatId(prefix, id) {
  return `#${prefix}-${String(id || 0).padStart(5, "0")}`;
}

