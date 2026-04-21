import { Link } from "react-router-dom";
import { Badge } from "../ui/Badge";

const statusTone = {
  pending: "amber",
  confirmed: "teal",
  cancelled: "coral",
  completed: "muted",
};

export function BookingCard({ booking }) {
  return (
    <article className="card flex items-center gap-4 rounded-xl border border-[var(--border-subtle)] bg-surface p-4">
      <img
        src={booking.image || "https://images.unsplash.com/photo-1460317442991-0ec209397118?q=80&w=600&auto=format&fit=crop"}
        alt={booking.title || `Booking ${booking.id}`}
        className="h-20 w-20 rounded-lg object-cover"
      />
      <div className="min-w-0 flex-1">
        <p className="font-display text-lg">{booking.title || `Property #${booking.unit_id || booking.id}`}</p>
        <p className="text-sm text-[var(--text-secondary)]">
          {booking.start_date || "2026-06-01"} → {booking.end_date || "2026-06-15"}
        </p>
        <p className="font-mono text-sm text-[var(--text-primary)]">${booking.total_price || 1200}</p>
      </div>
      <div className="flex flex-col items-end gap-2">
        <Badge tone={statusTone[booking.status] || "muted"}>{booking.status || "pending"}</Badge>
        <Link className="text-sm text-primary" to={`/bookings/${booking.id}`}>
          View Details
        </Link>
      </div>
    </article>
  );
}

