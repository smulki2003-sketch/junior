import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { getBookingDetail, getBookingTimeline } from "../api/bookings";
import { PageWrapper } from "../components/layout/PageWrapper";
import { Button } from "../components/ui/Button";
import { ErrorState } from "../components/ui/ErrorState";
import { Skeleton } from "../components/ui/Skeleton";
import { formatDateTime, formatPrice } from "../utils/format";

const displaySteps = [
  { label: "Booking Requested", icon: "OK" },
  { label: "Payment Confirmed", icon: "OK" },
  { label: "Landlord Review", icon: "..." },
  { label: "Confirmed", icon: "-" },
  { label: "Check-In", icon: "-" },
];

export default function BookingTimelinePage() {
  const { id } = useParams();
  const hasValidId = id != null && id !== "undefined" && id !== "null";

  const detailQuery = useQuery({
    queryKey: ["booking-detail", id],
    queryFn: () => getBookingDetail(id),
    enabled: hasValidId,
  });

  const timelineQuery = useQuery({
    queryKey: ["booking-timeline", id],
    queryFn: () => getBookingTimeline(id),
    enabled: hasValidId,
  });

  if (!hasValidId) {
    return (
      <PageWrapper>
        <ErrorState message="Invalid booking id." />
      </PageWrapper>
    );
  }

  if (detailQuery.isLoading || timelineQuery.isLoading) {
    return (
      <PageWrapper>
        <Skeleton className="h-[220px]" />
      </PageWrapper>
    );
  }

  if (detailQuery.isError || timelineQuery.isError) {
    return (
      <PageWrapper>
        <ErrorState message="Unable to load booking timeline." onRetry={() => { detailQuery.refetch(); timelineQuery.refetch(); }} />
      </PageWrapper>
    );
  }

  const booking = detailQuery.data || {};
  const timeline = Array.isArray(timelineQuery.data) ? timelineQuery.data : [];
  const reached = Math.min(displaySteps.length - 1, timeline.length + 1);

  return (
    <PageWrapper>
      <div className="mx-auto max-w-[680px] space-y-6">
        <div className="overflow-hidden rounded-xl border border-[var(--border-subtle)] bg-surface">
          <img src="https://images.unsplash.com/photo-1494526585095-c41746248156?q=80&w=1200&auto=format&fit=crop" alt="Property banner" className="h-[200px] w-full object-cover" />
          <div className="p-4">
            <p className="font-display text-2xl">{booking.property_name || `Property #${booking.unit_id || id}`}</p>
            <p className="text-sm text-[var(--text-secondary)]">{booking.location || "Near campus"}</p>
          </div>
        </div>

        <div className="rounded-xl border border-[var(--border-subtle)] bg-surface p-5">
          <div className="space-y-6">
            {displaySteps.map((step, index) => {
              const completed = index < reached - 1;
              const active = index === reached - 1;
              return (
                <div key={step.label} className="relative flex gap-4">
                  {index < displaySteps.length - 1 ? (
                    <span className={`absolute left-[14px] top-8 h-10 border-l ${completed ? "border-teal" : "border-dashed border-[var(--text-muted)]"}`} />
                  ) : null}
                  <span
                    className={`relative mt-1 inline-flex h-7 w-7 items-center justify-center rounded-full text-xs ${
                      completed ? "bg-teal text-black" : active ? "bg-primary text-white animate-pulse-glow" : "bg-elevated text-[var(--text-secondary)]"
                    }`}
                    style={active ? { animation: "pulse-ring 2s infinite" } : undefined}
                  >
                    {step.icon}
                  </span>
                  <div>
                    <p className={completed || active ? "text-white" : "text-[var(--text-secondary)]"}>{step.label}</p>
                    <p className="text-xs text-[var(--text-secondary)]">{timeline[index] ? formatDateTime(timeline[index].changed_at) : "Pending"}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="rounded-xl border border-[var(--border-subtle)] bg-surface p-5">
          <h3 className="mb-3 font-display text-lg">Payment Summary</h3>
          <div className="space-y-2 text-sm">
            <p className="flex justify-between"><span>Rent</span><span>{formatPrice(booking.total_price || 900)}</span></p>
            <p className="flex justify-between"><span>Service fee</span><span>{formatPrice(50)}</span></p>
            <p className="flex justify-between"><span>Deposit</span><span>{formatPrice(200)}</span></p>
            <p className="flex justify-between pt-2 font-mono text-lg"><span>Total</span><span>{formatPrice((Number(booking.total_price) || 900) + 250)}</span></p>
          </div>
          <Button className="mt-4 w-full">Download Receipt</Button>
        </div>

        {booking.status === "pending" ? (
          <div className="flex gap-3">
            <Button variant="outline" className="border-coral/40 text-coral">Cancel Booking</Button>
            <Button variant="ghost">Contact Support</Button>
          </div>
        ) : null}
      </div>
    </PageWrapper>
  );
}
