import { motion } from "framer-motion";
import { useMemo, useState } from "react";
import { PageWrapper } from "../components/layout/PageWrapper";
import { BookingCard } from "../components/shared/BookingCard";
import { Button } from "../components/ui/Button";
import { ErrorState } from "../components/ui/ErrorState";
import { Skeleton } from "../components/ui/Skeleton";
import { useBookings } from "../hooks/useBookings";
import { useAuthStore } from "../store/authStore";

const tabs = ["Upcoming", "Active", "Completed", "Cancelled"];

export default function BookingsPage() {
  const user = useAuthStore((state) => state.user);
  const [activeTab, setActiveTab] = useState("Upcoming");
  const bookingsQuery = useBookings(user?.id);

  const bookings = useMemo(() => {
    const source = Array.isArray(bookingsQuery.data) ? bookingsQuery.data : bookingsQuery.data || [];
    if (activeTab === "Cancelled") return source.filter((item) => item.status === "cancelled");
    if (activeTab === "Completed") return source.filter((item) => item.status === "completed");
    if (activeTab === "Active") return source.filter((item) => item.status === "confirmed");
    return source.filter((item) => item.status === "pending" || item.status === "confirmed");
  }, [bookingsQuery.data, activeTab]);

  return (
    <PageWrapper>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[260px_1fr]">
        <aside className="rounded-xl border border-[var(--border-subtle)] bg-surface p-4">
          <p className="mb-3 font-display text-lg">Filters</p>
          <div className="space-y-2 text-sm text-[var(--text-secondary)]">
            <p>• Date range</p>
            <p>• Property type</p>
            <p>• Price</p>
          </div>
        </aside>

        <section>
          <div className="relative mb-4 flex gap-2">
            {tabs.map((tab) => (
              <Button key={tab} variant="ghost" className="relative" onClick={() => setActiveTab(tab)}>
                {activeTab === tab ? (
                  <motion.div layoutId="booking-tab-underline" className="absolute inset-x-0 -bottom-1 h-[2px] bg-primary" />
                ) : null}
                {tab}
              </Button>
            ))}
          </div>

          {bookingsQuery.isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-28" />
              ))}
            </div>
          ) : bookingsQuery.isError ? (
            <ErrorState message="Unable to load bookings." onRetry={() => bookingsQuery.refetch()} />
          ) : bookings.length === 0 ? (
            <div className="rounded-xl border border-[var(--border-subtle)] bg-surface p-10 text-center">
              <div className="mx-auto mb-3 h-16 w-16 rounded-full bg-elevated" />
              <p className="text-[var(--text-secondary)]">No bookings yet — explore housing →</p>
            </div>
          ) : (
            <div className="space-y-3">
              {bookings.map((booking) => (
                <BookingCard key={booking.id} booking={booking} />
              ))}
            </div>
          )}
        </section>
      </div>
    </PageWrapper>
  );
}

