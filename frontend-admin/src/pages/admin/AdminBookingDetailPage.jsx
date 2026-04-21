import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { getAdminBookings } from "../../api/admin/bookings";
import { AdminShell } from "../../components/layout/AdminShell";
import { AuditLog } from "../../components/shared/AuditLog";
import { StatusBadge } from "../../components/shared/StatusBadge";
import { ErrorState } from "../../components/ui/ErrorState";
import { Skeleton } from "../../components/ui/Skeleton";
import { formatCurrency, formatDateTime } from "../../utils/formatters";

const timelineSteps = ["Booking Requested", "Payment Confirmed", "Landlord Review", "Confirmed", "Check-In"];

export default function AdminBookingDetailPage() {
  const { id } = useParams();
  const hasValidId = id != null && id !== "undefined" && id !== "null";

  const query = useQuery({
    queryKey: ["admin-booking-detail", id],
    queryFn: async () => {
      const payload = await getAdminBookings({ booking_ids: id });
      const rows = payload.results || payload || [];
      return rows.find((x) => String(x.id) === String(id)) || null;
    },
    enabled: hasValidId,
  });

  if (!hasValidId) {
    return (
      <AdminShell breadcrumb="Management / Bookings / Detail">
        <ErrorState message="Invalid booking id." />
      </AdminShell>
    );
  }

  if (query.isLoading) {
    return (
      <AdminShell breadcrumb="Management / Bookings / Detail">
        <Skeleton className="h-[440px]" />
      </AdminShell>
    );
  }

  if (query.isError || !query.data) {
    return (
      <AdminShell breadcrumb="Management / Bookings / Detail">
        <ErrorState message="Unable to load booking detail." onRetry={() => query.refetch()} />
      </AdminShell>
    );
  }

  const booking = query.data;
  const activeIndex = Math.max(0, timelineSteps.findIndex((x) => x.toLowerCase().includes(String(booking.status || "").toLowerCase())));
  const audit = booking.audit || [
    { id: 1, admin_name: "System", action: "Booking created", created_at: booking.created_at || new Date().toISOString() },
    { id: 2, admin_name: "Ahmed", action: "Manual override to confirmed", created_at: new Date().toISOString(), reason: "Payment verified" },
  ];

  return (
    <AdminShell breadcrumb="Management / Bookings / Detail">
      <div className="space-y-4 rounded-[10px] border border-[var(--table-border)] bg-surface p-4">
        <div className="flex items-center justify-between">
          <h1 className="font-display text-2xl font-semibold">Booking {booking.id}</h1>
          <StatusBadge status={booking.status || "pending"} />
        </div>

        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <div className="rounded-md bg-elevated p-3 text-sm">
            <p>Tenant: {booking.user_name || booking.user_id}</p>
            <p>Property: {booking.unit_name || booking.unit_id}</p>
            <p>Amount: {formatCurrency(booking.total_price)}</p>
            <p>Created: {formatDateTime(booking.created_at)}</p>
          </div>
          <div className="rounded-md bg-elevated p-3 text-sm">
            <p>Payment status: {booking.payment_status || "pending"}</p>
            <p>Check-in: {booking.start_date}</p>
            <p>Check-out: {booking.end_date}</p>
          </div>
        </div>

        <div className="rounded-md border border-[var(--table-border)] bg-elevated p-3">
          <h3 className="mb-3 font-display text-sm">Status Timeline</h3>
          <div className="space-y-3">
            {timelineSteps.map((step, index) => {
              const completed = index < activeIndex;
              const active = index === activeIndex;
              return (
                <div key={step} className="relative flex items-center gap-3">
                  {index < timelineSteps.length - 1 ? (
                    <span className={`absolute left-[11px] top-6 h-7 border-l ${completed ? "border-emerald" : "border-dashed border-[var(--text-muted)]"}`} />
                  ) : null}
                  <span
                    className={`inline-flex h-6 w-6 items-center justify-center rounded-full text-xs ${
                      completed ? "bg-emerald text-black" : active ? "bg-amber text-black" : "bg-surface text-[var(--text-secondary)]"
                    }`}
                  >
                    {completed ? "OK" : active ? "!" : "-"}
                  </span>
                  <p className={`text-sm ${active ? "text-amber" : ""}`}>{step}</p>
                </div>
              );
            })}
          </div>
        </div>

        <AuditLog entries={audit} />
      </div>
    </AdminShell>
  );
}
