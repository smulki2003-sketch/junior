import { format } from "date-fns";

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

export function formatPrice(value, currency = "USD") {
  const numberValue = Number(value || 0);
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(numberValue);
}

