import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";
import {
  addComplaintComment,
  getAdminComplaints,
  getComplaintDetail,
  updateComplaintStatus,
} from "../../api/admin/complaints";
import { AdminShell } from "../../components/layout/AdminShell";
import { StatusBadge } from "../../components/shared/StatusBadge";
import { Button } from "../../components/ui/Button";
import { ErrorState } from "../../components/ui/ErrorState";
import { Skeleton } from "../../components/ui/Skeleton";

export default function AdminComplaintsPage() {
  const [selectedComplaintId, setSelectedComplaintId] = useState(null);
  const [status, setStatus] = useState("in_review");
  const [internalNote, setInternalNote] = useState("");
  const [reply, setReply] = useState("");

  const listQuery = useQuery({
    queryKey: ["admin-complaints"],
    queryFn: () => getAdminComplaints(),
    refetchInterval: 7000,
  });

  const complaints = useMemo(() => listQuery.data?.results || [], [listQuery.data]);
  const activeComplaintId = selectedComplaintId || complaints[0]?.id || null;

  const detailQuery = useQuery({
    queryKey: ["admin-complaint-detail", activeComplaintId],
    enabled: Boolean(activeComplaintId),
    queryFn: () => getComplaintDetail(activeComplaintId),
  });

  const statusMutation = useMutation({
    mutationFn: (payload) => updateComplaintStatus(activeComplaintId, payload),
    onSuccess: () => {
      listQuery.refetch();
      detailQuery.refetch();
      setInternalNote("");
      toast.success("Complaint status updated.");
    },
  });

  const commentMutation = useMutation({
    mutationFn: (payload) => addComplaintComment(detailQuery.data?.moderation_case?.id, payload),
    onSuccess: () => {
      setReply("");
      detailQuery.refetch();
      toast.success("Reply sent to user.");
    },
  });

  useEffect(() => {
    if (detailQuery.data?.status) {
      setStatus(detailQuery.data.status);
    }
  }, [detailQuery.data?.status]);

  return (
    <AdminShell breadcrumb="Moderation / Complaints" complaintCount={complaints.length}>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[320px_1fr]">
        <aside className="rounded-xl border border-[var(--table-border)] bg-surface p-3">
          <h2 className="mb-2 font-display text-lg">Complaints</h2>
          {listQuery.isLoading ? (
            <Skeleton className="h-24" />
          ) : listQuery.isError ? (
            <ErrorState message="Unable to load complaints." onRetry={() => listQuery.refetch()} />
          ) : complaints.length === 0 ? (
            <p className="text-sm text-[var(--text-secondary)]">No complaints found.</p>
          ) : (
            <div className="space-y-2">
              {complaints.map((item) => (
                <button
                  key={item.id}
                  className="w-full rounded-md border border-[var(--table-border)] bg-elevated p-2 text-left"
                  onClick={() => setSelectedComplaintId(item.id)}
                >
                  <p className="text-sm font-semibold">Complaint #{item.id}</p>
                  <p className="text-xs text-[var(--text-secondary)]">{item.target_type} #{item.target_id}</p>
                  <StatusBadge status={item.status} />
                </button>
              ))}
            </div>
          )}
        </aside>

        <section className="rounded-xl border border-[var(--table-border)] bg-surface p-4">
          {!activeComplaintId ? (
            <p className="text-sm text-[var(--text-secondary)]">Select a complaint.</p>
          ) : detailQuery.isLoading ? (
            <Skeleton className="h-32" />
          ) : detailQuery.isError ? (
            <ErrorState message="Unable to load complaint detail." onRetry={() => detailQuery.refetch()} />
          ) : (
            <div className="space-y-4">
              <div>
                <h2 className="font-display text-xl">Complaint #{detailQuery.data.id}</h2>
                <p className="text-sm text-[var(--text-secondary)]">
                  Reporter: User {detailQuery.data.reporter_user_id} · Target: {detailQuery.data.target_type} #{detailQuery.data.target_id}
                </p>
              </div>
              <div className="rounded-md border border-[var(--table-border)] bg-elevated p-3">
                <p className="text-sm">{detailQuery.data.reason}</p>
              </div>
              <div className="grid grid-cols-1 gap-2 md:grid-cols-[200px_1fr_auto]">
                <select
                  className="rounded-md border border-[var(--border-subtle)] bg-elevated px-3 py-2 text-sm"
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                >
                  <option value="triaged">Triaged</option>
                  <option value="in_review">In Review</option>
                  <option value="resolved">Resolved</option>
                  <option value="closed">Closed</option>
                  <option value="rejected">Rejected</option>
                </select>
                <input
                  className="rounded-md border border-[var(--border-subtle)] bg-elevated px-3 py-2 text-sm"
                  placeholder="Internal note"
                  value={internalNote}
                  onChange={(e) => setInternalNote(e.target.value)}
                />
                <Button
                  onClick={() =>
                    statusMutation.mutate({
                      status,
                      case_status: ["resolved", "closed"].includes(status) ? status : "in_progress",
                      internal_note: internalNote || undefined,
                    })
                  }
                  disabled={statusMutation.isPending}
                >
                  Update
                </Button>
              </div>

              <div className="space-y-2 rounded-md border border-[var(--table-border)] bg-elevated p-3">
                <h3 className="font-display text-lg">Admin Replies</h3>
                {Array.isArray(detailQuery.data.comments) && detailQuery.data.comments.length > 0 ? (
                  detailQuery.data.comments.map((comment) => (
                    <div key={comment.id} className="rounded-md bg-surface p-2 text-sm">
                      {comment.comment}
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-[var(--text-secondary)]">No replies yet.</p>
                )}
                <textarea
                  className="h-24 w-full rounded-md border border-[var(--border-subtle)] bg-surface px-3 py-2 text-sm"
                  value={reply}
                  onChange={(e) => setReply(e.target.value)}
                  placeholder="Write response to user..."
                />
                <Button
                  onClick={() => commentMutation.mutate({ comment: reply })}
                  disabled={reply.trim().length < 2 || commentMutation.isPending}
                >
                  Send Reply
                </Button>
              </div>
            </div>
          )}
        </section>
      </div>
    </AdminShell>
  );
}
