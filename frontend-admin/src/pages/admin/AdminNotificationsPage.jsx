import { useMutation, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { sendBroadcast } from "../../api/admin/notifications";
import { getAdminUsers } from "../../api/admin/users";
import { AdminShell } from "../../components/layout/AdminShell";
import { StatusBadge } from "../../components/shared/StatusBadge";
import { Button } from "../../components/ui/Button";
import { Modal } from "../../components/ui/Modal";
import { formatDateTime } from "../../utils/formatters";

const typeOptions = [
  { value: "info", label: "Info" },
  { value: "warning", label: "Warning" },
  { value: "success", label: "Success" },
  { value: "urgent", label: "Urgent" },
];

const audienceOptions = [
  { value: "all_users", label: "All Users" },
  { value: "students_only", label: "Students Only" },
  { value: "landlords_only", label: "Landlords Only" },
];

export default function AdminNotificationsPage() {
  const [payload, setPayload] = useState({
    title: "",
    body: "",
    audience: "all_users",
    type: "info",
  });
  const [history, setHistory] = useState([]);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const usersQuery = useQuery({
    queryKey: ["admin-users-for-broadcast"],
    queryFn: () => getAdminUsers({}),
  });

  const users = Array.isArray(usersQuery.data?.results) ? usersQuery.data.results : [];

  const targetUserIds = useMemo(() => {
    if (payload.audience === "all_users") {
      return users.map((user) => user.user_id);
    }
    if (payload.audience === "students_only") {
      return users.filter((user) => (user.role || "").toLowerCase() === "student").map((user) => user.user_id);
    }
    if (payload.audience === "landlords_only") {
      return users.filter((user) => (user.role || "").toLowerCase() === "landlord").map((user) => user.user_id);
    }
    return [];
  }, [payload.audience, users]);

  const audienceLabel = useMemo(
    () => audienceOptions.find((option) => option.value === payload.audience)?.label || "All Users",
    [payload.audience]
  );

  const broadcastMutation = useMutation({
    mutationFn: sendBroadcast,
    onSuccess: (response) => {
      setHistory((prev) => [
        {
          id: `n${Date.now()}`,
          title: payload.title,
          type: payload.type,
          audience: audienceLabel,
          sent_at: new Date().toISOString(),
          reach: Number(response?.recipient_count || targetUserIds.length),
          status: "sent",
        },
        ...prev,
      ]);
      setConfirmOpen(false);
      setPayload({
        title: "",
        body: "",
        audience: "all_users",
        type: "info",
      });
    },
  });

  function sendNow() {
    broadcastMutation.mutate({
      title: payload.title,
      body: payload.body,
      target_user_ids: targetUserIds,
      event_key: `admin.broadcast.${payload.type}`,
    });
  }

  return (
    <AdminShell breadcrumb="Comms / Notifications">
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_380px]">
        <section className="space-y-4 rounded-[10px] border border-[var(--table-border)] bg-surface p-4">
          <h1 className="font-display text-xl font-semibold">New Broadcast</h1>

          <div>
            <p className="mb-1 text-xs text-[var(--text-secondary)]">Title</p>
            <input
              className="w-full rounded-md border border-[var(--border-subtle)] bg-elevated px-3 py-2 font-display text-sm"
              value={payload.title}
              onChange={(event) => setPayload((prev) => ({ ...prev, title: event.target.value }))}
              placeholder="Enter title"
            />
          </div>

          <div>
            <p className="mb-1 text-xs text-[var(--text-secondary)]">Message Body</p>
            <textarea
              className="h-36 w-full rounded-md border border-[var(--border-subtle)] bg-elevated px-3 py-2 text-sm"
              value={payload.body}
              onChange={(event) => setPayload((prev) => ({ ...prev, body: event.target.value }))}
              placeholder="Write your message"
            />
          </div>

          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <div>
              <p className="mb-1 text-xs text-[var(--text-secondary)]">Target Audience</p>
              <select
                className="w-full rounded-md border border-[var(--border-subtle)] bg-elevated px-3 py-2 text-sm"
                value={payload.audience}
                onChange={(event) => setPayload((prev) => ({ ...prev, audience: event.target.value }))}
              >
                {audienceOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <p className="mb-1 text-xs text-[var(--text-secondary)]">Type</p>
              <select
                className="w-full rounded-md border border-[var(--border-subtle)] bg-elevated px-3 py-2 text-sm"
                value={payload.type}
                onChange={(event) => setPayload((prev) => ({ ...prev, type: event.target.value }))}
              >
                {typeOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="rounded-md border border-[var(--table-border)] bg-elevated p-3">
            <p className="mb-2 text-xs text-[var(--text-secondary)]">Live Preview</p>
            <p className="font-display text-sm">{payload.title || "Notification title"}</p>
            <p className="mt-1 text-sm text-[var(--text-secondary)]">{payload.body || "Your message preview will appear here."}</p>
            <div className="mt-2 flex items-center gap-2 text-xs">
              <StatusBadge status={payload.type} />
              <span className="rounded-full bg-surface px-2 py-1">{audienceLabel}</span>
              <span className="rounded-full bg-surface px-2 py-1">{targetUserIds.length} recipients</span>
            </div>
          </div>

          <Button
            className="w-full"
            onClick={() => setConfirmOpen(true)}
            disabled={!payload.title.trim() || !payload.body.trim() || usersQuery.isLoading}
          >
            Send Broadcast
          </Button>
        </section>

        <aside className="rounded-[10px] border border-[var(--table-border)] bg-surface p-4">
          <h2 className="mb-3 font-display text-lg">Broadcast History</h2>
          {!history.length ? <p className="text-sm text-[var(--text-secondary)]">No broadcasts yet.</p> : null}
          <div className="space-y-2">
            {history.map((item) => (
              <div key={item.id} className="rounded-md border border-[var(--table-border)] bg-elevated p-3 text-sm">
                <div className="mb-1 flex items-start justify-between gap-2">
                  <p className="font-medium">{item.title}</p>
                  <StatusBadge status={item.status} />
                </div>
                <p className="text-xs text-[var(--text-secondary)]">
                  {item.audience} - {formatDateTime(item.sent_at)}
                </p>
                <p className="mt-1 text-xs text-cyan">Sent to {item.reach.toLocaleString()} users</p>
              </div>
            ))}
          </div>
        </aside>
      </div>

      <Modal open={confirmOpen} onClose={() => setConfirmOpen(false)}>
        <h3 className="font-display text-lg">Confirm Broadcast</h3>
        <p className="mt-1 text-sm text-[var(--text-secondary)]">You are about to notify {targetUserIds.length.toLocaleString()} users. Confirm?</p>
        <div className="mt-4 flex gap-2">
          <Button variant="ghost" onClick={() => setConfirmOpen(false)}>
            Cancel
          </Button>
          <Button onClick={sendNow} disabled={broadcastMutation.isPending || targetUserIds.length === 0}>
            {broadcastMutation.isPending ? "Sending..." : "Confirm & Send"}
          </Button>
        </div>
      </Modal>
    </AdminShell>
  );
}
