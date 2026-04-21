import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { createComplaint, getComplaintDetail, listMyComplaints } from "../api/complaints";
import { getUserBookings } from "../api/bookings";
import { PageWrapper } from "../components/layout/PageWrapper";
import { Button } from "../components/ui/Button";
import { ErrorState } from "../components/ui/ErrorState";
import { Skeleton } from "../components/ui/Skeleton";
import { useAuthStore } from "../store/authStore";

export default function ComplaintsPage() {
  const user = useAuthStore((state) => state.user);
  const [bookingId, setBookingId] = useState("");
  const [reason, setReason] = useState("");
  const [selectedComplaintId, setSelectedComplaintId] = useState(null);

  const bookingsQuery = useQuery({
    queryKey: ["complaint-bookings", user?.id],
    enabled: Boolean(user?.id),
    queryFn: () => getUserBookings(user.id),
  });
  const complaintsQuery = useQuery({
    queryKey: ["my-complaints", user?.id],
    enabled: Boolean(user?.id),
    queryFn: listMyComplaints,
  });

  const eligibleBookings = useMemo(() => {
    const rows = Array.isArray(bookingsQuery.data) ? bookingsQuery.data : [];
    return rows.filter((item) => ["confirmed", "completed"].includes(String(item.status).toLowerCase()));
  }, [bookingsQuery.data]);

  useEffect(() => {
    if (eligibleBookings.length === 1 && !bookingId) {
      setBookingId(String(eligibleBookings[0].id));
    }
  }, [eligibleBookings, bookingId]);

  const createMutation = useMutation({
    mutationFn: () =>
      createComplaint({
        target_type: "booking",
        target_id: Number(bookingId),
        reason,
      }),
    onSuccess: (row) => {
      setReason("");
      setSelectedComplaintId(row?.id || null);
      complaintsQuery.refetch();
    },
  });

  const detailQuery = useQuery({
    queryKey: ["complaint-detail", selectedComplaintId],
    enabled: Boolean(selectedComplaintId),
    queryFn: () => getComplaintDetail(selectedComplaintId),
  });

  const complaints = Array.isArray(complaintsQuery.data) ? complaintsQuery.data : [];

  return (
    <PageWrapper className="space-y-6">
      <section className="rounded-xl border border-[var(--border-subtle)] bg-surface p-4">
        <h1 className="font-display text-2xl">Complaints</h1>
        <p className="text-sm text-[var(--text-secondary)]">Only confirmed or completed bookings can submit complaints.</p>
      </section>

      <section className="rounded-xl border border-[var(--border-subtle)] bg-surface p-4 space-y-3">
        <h2 className="font-display text-lg">New Complaint</h2>
        {bookingsQuery.isLoading ? (
          <Skeleton className="h-24" />
        ) : bookingsQuery.isError ? (
          <ErrorState message="Unable to load your eligible bookings." onRetry={() => bookingsQuery.refetch()} />
        ) : eligibleBookings.length === 0 ? (
          <p className="text-sm text-[var(--text-secondary)]">No eligible bookings found.</p>
        ) : (
          <>
            {eligibleBookings.length > 1 ? (
              <select
                className="w-full rounded-md border border-[var(--border-subtle)] bg-elevated px-3 py-2"
                value={bookingId}
                onChange={(e) => setBookingId(e.target.value)}
              >
                <option value="">Select booking</option>
                {eligibleBookings.map((item) => (
                  <option key={item.id} value={item.id}>
                    Booking #{item.id} - Unit {item.unit_id}
                  </option>
                ))}
              </select>
            ) : (
              <p className="text-sm">Booking #{eligibleBookings[0].id} - Unit {eligibleBookings[0].unit_id}</p>
            )}
            <textarea
              className="h-32 w-full rounded-md border border-[var(--border-subtle)] bg-elevated px-3 py-2"
              placeholder="Write your complaint..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
            <Button
              onClick={() => createMutation.mutate()}
              disabled={!bookingId || reason.trim().length < 10 || createMutation.isPending}
            >
              {createMutation.isPending ? "Submitting..." : "Submit Complaint"}
            </Button>
          </>
        )}
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-[280px_1fr]">
        <aside className="rounded-xl border border-[var(--border-subtle)] bg-surface p-3 space-y-2">
          <h3 className="font-display text-lg">My Complaints</h3>
          {complaintsQuery.isLoading ? (
            <Skeleton className="h-24" />
          ) : complaintsQuery.isError ? (
            <ErrorState message="Unable to load complaints." onRetry={() => complaintsQuery.refetch()} />
          ) : complaints.length === 0 ? (
            <p className="text-sm text-[var(--text-secondary)]">No complaints yet.</p>
          ) : (
            complaints.map((item) => (
              <button
                key={item.id}
                className="w-full rounded-md border border-[var(--border-subtle)] p-2 text-left"
                onClick={() => setSelectedComplaintId(item.id)}
              >
                <p className="text-sm font-semibold">Complaint #{item.id}</p>
                <p className="text-xs text-[var(--text-secondary)]">Status: {item.status}</p>
              </button>
            ))
          )}
        </aside>

        <div className="rounded-xl border border-[var(--border-subtle)] bg-surface p-4">
          {!selectedComplaintId ? (
            <p className="text-sm text-[var(--text-secondary)]">Select complaint to view admin response.</p>
          ) : detailQuery.isLoading ? (
            <Skeleton className="h-32" />
          ) : detailQuery.isError ? (
            <ErrorState message="Unable to load complaint detail." onRetry={() => detailQuery.refetch()} />
          ) : (
            <div className="space-y-3">
              <p className="text-sm">Status: <span className="font-semibold">{detailQuery.data?.status}</span></p>
              <p className="text-sm">{detailQuery.data?.reason}</p>
              <div className="rounded-md border border-[var(--border-subtle)] bg-elevated p-3 space-y-2">
                <h4 className="text-sm font-semibold">Admin Responses</h4>
                {Array.isArray(detailQuery.data?.comments) && detailQuery.data.comments.length ? (
                  detailQuery.data.comments.map((comment) => (
                    <div key={comment.id} className="rounded bg-surface p-2 text-sm">
                      {comment.comment}
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-[var(--text-secondary)]">No response yet.</p>
                )}
              </div>
            </div>
          )}
        </div>
      </section>
    </PageWrapper>
  );
}
