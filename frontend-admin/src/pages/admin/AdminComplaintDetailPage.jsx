import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getAdminComplaints } from "../../api/admin/complaints";
import { fadeIn } from "../../animations/variants";
import { AdminShell } from "../../components/layout/AdminShell";
import { AuditLog } from "../../components/shared/AuditLog";
import { StatusBadge } from "../../components/shared/StatusBadge";
import { Button } from "../../components/ui/Button";
import { ErrorState } from "../../components/ui/ErrorState";
import { Skeleton } from "../../components/ui/Skeleton";
import { formatDateTime } from "../../utils/formatters";

function getPriorityClass(priority) {
  const value = String(priority || "").toLowerCase();
  if (value === "urgent") return "text-danger";
  if (value === "low") return "text-[var(--text-secondary)]";
  return "text-amber";
}

export default function AdminComplaintDetailPage() {
  const navigate = useNavigate();
  const { id } = useParams();
  const hasValidId = id != null && id !== "undefined" && id !== "null";
  const [status, setStatus] = useState("in_review");
  const [priority, setPriority] = useState("normal");
  const [assignee, setAssignee] = useState("admin_ahmed");
  const [composerType, setComposerType] = useState("internal");
  const [draft, setDraft] = useState("");

  const complaintsQuery = useQuery({
    queryKey: ["admin-complaints", "detail", id],
    queryFn: () => getAdminComplaints({ complaint_id: id }),
    enabled: hasValidId,
  });

  const complaints = complaintsQuery.data?.results || complaintsQuery.data || [];
  const complaint = useMemo(
    () => complaints.find((item) => String(item.id) === String(id)) || complaints[0] || null,
    [complaints, id]
  );

  const conversation = complaint?.comments || [
    {
      id: "c1",
      type: "internal",
      text: "Escalated to moderation lead for policy review.",
      author: "Ahmed R.",
      created_at: new Date(Date.now() - 1000 * 60 * 24).toISOString(),
    },
    {
      id: "c2",
      type: "external",
      text: "We are actively reviewing your complaint and will update you shortly.",
      author: "Ahmed R.",
      created_at: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
    },
  ];
  const targetRouteByType = {
    booking: "bookings",
    bookings: "bookings",
    listing: "housing",
    housing: "housing",
    payment: "payments",
    user: "users",
  };
  const targetRoute = targetRouteByType[String(complaint?.target_type || "").toLowerCase()] || "complaints";
  const targetPath = targetRoute === "payments" ? `/admin/payments` : `/admin/${targetRoute}/${complaint?.target_id || complaint?.id}`;

  return (
    <AdminShell breadcrumb="Moderation / Complaints / Case Detail" complaintCount={complaints.length}>
      {complaintsQuery.isLoading ? (
        <Skeleton className="h-[620px]" />
      ) : !hasValidId ? (
        <ErrorState message="Invalid complaint id." onRetry={() => navigate("/admin/complaints")} />
      ) : complaintsQuery.isError ? (
        <ErrorState message="Unable to load complaint case." onRetry={() => complaintsQuery.refetch()} />
      ) : !complaint ? (
        <ErrorState message="Complaint not found." actionText="Back to complaints" onRetry={() => navigate("/admin/complaints")} />
      ) : (
        <motion.div variants={fadeIn} initial="hidden" animate="visible" className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_260px]">
          <section className="space-y-4 rounded-[10px] border border-[var(--table-border)] bg-surface p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h1 className="font-display text-xl font-semibold">{complaint.title || `Complaint #${complaint.id}`}</h1>
                <p className="mt-1 text-sm text-[var(--text-secondary)]">
                  Submitted by {complaint.reporter_name || `User ${complaint.reporter_user_id}`} on {formatDateTime(complaint.created_at)}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <StatusBadge status={complaint.status || status} />
                <span className={`rounded-full bg-elevated px-2 py-1 text-xs ${getPriorityClass(complaint.priority || priority)}`}>
                  {complaint.priority || priority}
                </span>
              </div>
            </div>

            <div className="rounded-md border border-[var(--table-border)] bg-elevated p-3">
              <p className="mb-1 text-xs text-[var(--text-secondary)]">Description</p>
              <p className="text-sm leading-relaxed">
                {complaint.description ||
                  "The user reported a policy violation and requested immediate review on the associated entity."}
              </p>
            </div>

            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <div className="rounded-md border border-[var(--table-border)] bg-elevated p-3">
                <p className="text-xs text-[var(--text-secondary)]">Related Entity</p>
                <button className="mt-1 text-sm text-blue" onClick={() => navigate(targetPath)}>
                  {complaint.target_type || "booking"} #{complaint.target_id || complaint.id}
                </button>
              </div>
              <div className="rounded-md border border-[var(--table-border)] bg-elevated p-3">
                <p className="text-xs text-[var(--text-secondary)]">Attachments</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {(complaint.evidence_urls || []).length > 0 ? (
                    complaint.evidence_urls.map((url, index) => (
                      <a key={url} className="rounded-md border border-[var(--border-subtle)] px-2 py-1 text-xs text-cyan" href={url} target="_blank" rel="noreferrer">
                        Attachment {index + 1}
                      </a>
                    ))
                  ) : (
                    <span className="rounded-md border border-[var(--border-subtle)] px-2 py-1 text-xs text-[var(--text-secondary)]">
                      No attachments
                    </span>
                  )}
                </div>
              </div>
            </div>

            <div className="rounded-md border border-[var(--table-border)] bg-elevated p-3">
              <h2 className="mb-2 font-display text-base">Conversation</h2>
              <div className="space-y-2">
                {conversation.map((item) => (
                  <div key={item.id} className={`rounded-md p-2 text-xs ${item.type === "internal" ? "bg-surface" : "bg-hover"}`}>
                    <p className="mb-1 text-[10px] text-[var(--text-secondary)]">
                      {item.type === "internal" ? "Internal note" : "Sent to user"} • {item.author}
                    </p>
                    <p>{item.text}</p>
                    <p className="mt-1 font-mono text-[10px] text-[var(--text-secondary)]">{formatDateTime(item.created_at)}</p>
                  </div>
                ))}
              </div>
              <div className="mt-3 space-y-2">
                <textarea
                  className="h-24 w-full rounded-md border border-[var(--border-subtle)] bg-surface px-2 py-2 text-xs"
                  placeholder="Write a response..."
                  value={draft}
                  onChange={(event) => setDraft(event.target.value)}
                />
                <div className="flex flex-wrap items-center gap-2">
                  <select
                    className="rounded-md border border-[var(--border-subtle)] bg-surface px-2 py-2 text-xs"
                    value={composerType}
                    onChange={(event) => setComposerType(event.target.value)}
                  >
                    <option value="internal">Add Note (Internal)</option>
                    <option value="external">Reply to User</option>
                  </select>
                  <Button onClick={() => setDraft("")} disabled={!draft.trim()}>
                    Send
                  </Button>
                </div>
              </div>
            </div>

            <div className="rounded-md border border-[var(--table-border)] bg-elevated p-3">
              <h2 className="mb-2 font-display text-base">Case Timeline</h2>
              <AuditLog
                entries={
                  complaint.audit_logs || [
                    {
                      id: "a1",
                      admin_name: "Ahmed R.",
                      action: "Status changed to In Review",
                      created_at: new Date(Date.now() - 1000 * 60 * 35).toISOString(),
                      reason: "Initial triage complete.",
                    },
                    {
                      id: "a2",
                      admin_name: "Nora M.",
                      action: "Priority updated to Urgent",
                      created_at: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
                      reason: "Potential financial harm identified.",
                    },
                  ]
                }
              />
            </div>
          </section>

          <aside className="space-y-3 rounded-[10px] border border-[var(--table-border)] bg-surface p-3">
            <h3 className="font-display text-sm">Actions</h3>
            <div>
              <p className="mb-1 text-xs text-[var(--text-secondary)]">Status</p>
              <select className="w-full rounded-md border border-[var(--border-subtle)] bg-elevated px-2 py-2 text-xs" value={status} onChange={(event) => setStatus(event.target.value)}>
                <option value="open">Open</option>
                <option value="in_review">In Review</option>
                <option value="resolved">Resolved</option>
                <option value="closed">Closed</option>
              </select>
            </div>
            <div>
              <p className="mb-1 text-xs text-[var(--text-secondary)]">Priority</p>
              <select className="w-full rounded-md border border-[var(--border-subtle)] bg-elevated px-2 py-2 text-xs" value={priority} onChange={(event) => setPriority(event.target.value)}>
                <option value="low">Low</option>
                <option value="normal">Normal</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>
            <div>
              <p className="mb-1 text-xs text-[var(--text-secondary)]">Assigned To</p>
              <select className="w-full rounded-md border border-[var(--border-subtle)] bg-elevated px-2 py-2 text-xs" value={assignee} onChange={(event) => setAssignee(event.target.value)}>
                <option value="admin_ahmed">Ahmed R.</option>
                <option value="admin_nora">Nora M.</option>
                <option value="admin_khaled">Khaled S.</option>
              </select>
            </div>
            <div>
              <p className="mb-1 text-xs text-[var(--text-secondary)]">Tags</p>
              <div className="flex flex-wrap gap-1">
                {["billing", "urgent", "duplicate"].map((tag) => (
                  <span key={tag} className="rounded-full bg-elevated px-2 py-1 text-[10px] text-[var(--text-label)]">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
            <Button variant="success" className="w-full">
              Resolve Case
            </Button>
            <Button variant="outline" className="w-full text-amber">
              Escalate
            </Button>
            <Button variant="ghost" className="w-full">
              Close without action
            </Button>
          </aside>
        </motion.div>
      )}
    </AdminShell>
  );
}

