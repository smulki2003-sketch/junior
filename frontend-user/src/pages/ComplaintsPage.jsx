import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";
import { createComplaint, getComplaintDetail, listMyComplaints } from "../api/complaints";
import { getUserBookings } from "../api/bookings";
import { getHousingUnit } from "../api/housing";
import { PageWrapper } from "../components/layout/PageWrapper";
import { Button } from "../components/ui/Button";
import { ErrorState } from "../components/ui/ErrorState";
import { Skeleton } from "../components/ui/Skeleton";
import { useAuthStore } from "../store/authStore";

export default function ComplaintsPage() {
  const user = useAuthStore((state) => state.user);
  const userId = user?.id ?? user?.user_id ?? null;
  const [bookingId, setBookingId] = useState("");
  const [reason, setReason] = useState("");
  const [selectedComplaintId, setSelectedComplaintId] = useState(null);

  const bookingsQuery = useQuery({
    queryKey: ["complaint-bookings", userId],
    enabled: Boolean(userId),
    queryFn: () => getUserBookings(userId),
  });
  const complaintsQuery = useQuery({
    queryKey: ["my-complaints", userId],
    enabled: Boolean(userId),
    queryFn: listMyComplaints,
    refetchInterval: 7000,
  });

  const eligibleBookings = useMemo(() => {
    const rows = Array.isArray(bookingsQuery.data) ? bookingsQuery.data : [];
    return rows.filter((item) => ["confirmed", "completed"].includes(String(item.status).toLowerCase()));
  }, [bookingsQuery.data]);
  const unitIdsKey = useMemo(
    () => eligibleBookings.map((item) => item.unit_id).filter((id) => Number.isInteger(id)).sort((a, b) => a - b).join(","),
    [eligibleBookings]
  );
  const unitDetailsQuery = useQuery({
    queryKey: ["complaint-unit-details", unitIdsKey],
    enabled: Boolean(unitIdsKey),
    queryFn: async () => {
      const unitIds = unitIdsKey.split(",").filter(Boolean).map((item) => Number(item));
      const settled = await Promise.allSettled(unitIds.map((unitId) => getHousingUnit(unitId)));
      const nextMap = {};
      settled.forEach((entry, index) => {
        if (entry.status === "fulfilled") {
          nextMap[unitIds[index]] = entry.value;
        }
      });
      return nextMap;
    },
  });
  const unitById = unitDetailsQuery.data || {};

  useEffect(() => {
    if (eligibleBookings.length > 0 && !bookingId) {
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
      toast.success("Complaint submitted. Please check notifications for updates.");
    },
    onError: (error) => {
      const message =
        error?.response?.data?.error?.message
        || error?.response?.data?.error?.details?.upstream_response?.error?.message
        || "Unable to submit complaint. Please try again.";
      toast.error(message);
    },
  });

  function handleSubmitComplaint() {
    if (!userId) {
      toast.error("Your session is not ready yet. Please reopen this page.");
      return;
    }
    if (!bookingId) {
      toast.error("Please select a booking first.");
      return;
    }
    if (reason.trim().length < 10) {
      toast.error("Complaint message must be at least 10 characters.");
      return;
    }
    createMutation.mutate();
  }

  const detailQuery = useQuery({
    queryKey: ["complaint-detail", selectedComplaintId],
    enabled: Boolean(selectedComplaintId),
    queryFn: () => getComplaintDetail(selectedComplaintId),
  });

  const complaints = Array.isArray(complaintsQuery.data) ? complaintsQuery.data : [];

  useEffect(() => {
    if (!selectedComplaintId && complaints.length > 0) {
      setSelectedComplaintId(complaints[0].id);
    }
  }, [complaints, selectedComplaintId]);

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
                    Booking #{item.id} - {unitById[item.unit_id]?.title || `Unit ${item.unit_id}`}
                  </option>
                ))}
              </select>
            ) : (
              <p className="text-sm">
                Booking #{eligibleBookings[0].id} - {unitById[eligibleBookings[0].unit_id]?.title || `Unit ${eligibleBookings[0].unit_id}`}
              </p>
            )}
            <textarea
              className="h-32 w-full rounded-md border border-[var(--border-subtle)] bg-elevated px-3 py-2"
              placeholder="Write your complaint..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
            <Button
              onClick={handleSubmitComplaint}
              disabled={createMutation.isPending}
            >
              {createMutation.isPending ? "Submitting..." : "Submit Complaint"}
            </Button>
            {!bookingId ? <p className="text-xs text-amber">Please select a booking first.</p> : null}
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
