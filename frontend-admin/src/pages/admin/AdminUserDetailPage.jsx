import { useMutation, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { getAdminUsers, updateAdminUserStatus } from "../../api/admin/users";
import { AdminShell } from "../../components/layout/AdminShell";
import { AuditLog } from "../../components/shared/AuditLog";
import { StatusBadge } from "../../components/shared/StatusBadge";
import { Button } from "../../components/ui/Button";
import { ErrorState } from "../../components/ui/ErrorState";
import { Input } from "../../components/ui/Input";
import { Skeleton } from "../../components/ui/Skeleton";
import { formatDate } from "../../utils/formatters";

const tabs = ["Overview", "Bookings", "Complaints", "Activity Log"];

export default function AdminUserDetailPage() {
  const { id } = useParams();
  const hasValidId = id != null && id !== "undefined" && id !== "null";
  const [tab, setTab] = useState("Overview");
  const [status, setStatus] = useState("active");
  const [reason, setReason] = useState("");

  const query = useQuery({
    queryKey: ["admin-user", id],
    queryFn: async () => {
      const payload = await getAdminUsers({ user_ids: id });
      return payload.results?.[0] || null;
    },
    enabled: hasValidId,
  });

  const updateMutation = useMutation({
    mutationFn: (payload) => updateAdminUserStatus(id, payload),
    onSuccess: () => query.refetch(),
  });

  const user = query.data;
  const auditEntries = useMemo(
    () => user?.activity || [{ id: 1, admin_name: "Ahmed", action: "Status changed to active", created_at: new Date().toISOString(), reason: "Manual review completed" }],
    [user]
  );

  return (
    <AdminShell breadcrumb="Management / Users / Detail">
      {!hasValidId ? (
        <ErrorState message="Invalid user id." />
      ) : query.isLoading ? (
        <Skeleton className="h-64" />
      ) : query.isError || !user ? (
        <ErrorState message="Unable to load user detail." onRetry={() => query.refetch()} />
      ) : (
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
          <div className="rounded-[10px] border border-[var(--table-border)] bg-surface p-4">
            <div className="mb-3 flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-elevated">{(user.profile?.first_name || "U").slice(0, 1).toUpperCase()}</div>
              <div>
                <p className="font-display text-lg">{user.profile?.first_name || "User"} {user.profile?.last_name || ""}</p>
                <p className="text-xs text-[var(--text-secondary)]">{user.profile?.email || "-"}</p>
              </div>
            </div>
            <div className="space-y-1 text-sm">
              <p>University: {user.profile?.university || "-"}</p>
              <p>Joined: {formatDate(user.created_at)}</p>
              <div className="pt-2"><StatusBadge status={user.status || "active"} /></div>
            </div>
          </div>

          <div className="xl:col-span-2">
            <div className="mb-3 flex flex-wrap gap-2">
              {tabs.map((item) => (
                <Button key={item} variant={tab === item ? "primary" : "outline"} onClick={() => setTab(item)}>{item}</Button>
              ))}
            </div>

            <div className="space-y-4 rounded-[10px] border border-[var(--table-border)] bg-surface p-4">
              {tab === "Overview" ? <p className="text-sm text-[var(--text-secondary)]">User overview and profile metadata.</p> : null}
              {tab === "Bookings" ? <p className="text-sm text-[var(--text-secondary)]">Booking history would appear here.</p> : null}
              {tab === "Complaints" ? <p className="text-sm text-[var(--text-secondary)]">Complaint history would appear here.</p> : null}
              {tab === "Activity Log" ? <AuditLog entries={auditEntries} /> : null}

              <div className="rounded-md border border-[var(--table-border)] bg-elevated p-3">
                <h4 className="mb-2 text-sm font-medium">Status Change</h4>
                <div className="grid grid-cols-1 gap-3 md:grid-cols-[180px_1fr_auto]">
                  <select className="rounded-md border border-[var(--border-subtle)] bg-surface px-2 py-2" value={status} onChange={(e) => setStatus(e.target.value)}>
                    <option value="active">Active</option>
                    <option value="suspended">Suspended</option>
                  </select>
                  <Input label="Reason" value={reason} onChange={(e) => setReason(e.target.value)} />
                  <Button disabled={!reason.trim() || updateMutation.isPending} onClick={() => updateMutation.mutate({ status, reason })}>Apply</Button>
                </div>
              </div>

              <AuditLog entries={auditEntries} />
            </div>
          </div>
        </div>
      )}
    </AdminShell>
  );
}
