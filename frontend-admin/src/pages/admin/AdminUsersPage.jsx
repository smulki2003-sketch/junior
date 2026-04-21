import { useMutation, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getAdminUsers, updateAdminUserStatus } from "../../api/admin/users";
import { AdminShell } from "../../components/layout/AdminShell";
import { ActionMenu } from "../../components/shared/ActionMenu";
import { StatusBadge } from "../../components/shared/StatusBadge";
import { Button } from "../../components/ui/Button";
import { DataTable } from "../../components/ui/DataTable";
import { ErrorState } from "../../components/ui/ErrorState";
import { Modal } from "../../components/ui/Modal";
import { Input } from "../../components/ui/Input";
import { useTable } from "../../hooks/useTable";
import { formatRelative } from "../../utils/formatters";

export default function AdminUsersPage() {
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState("All");
  const [roleFilter, setRoleFilter] = useState("All");
  const [search, setSearch] = useState("");
  const [statusModal, setStatusModal] = useState({ open: false, user: null });
  const [statusPayload, setStatusPayload] = useState({ status: "suspended", reason: "" });

  const usersQuery = useQuery({
    queryKey: ["admin-users", search],
    queryFn: () => getAdminUsers({ user_ids: search }),
  });
  const usersRaw = usersQuery.data?.results || [];

  const filtered = useMemo(() => {
    return usersRaw.filter((item) => {
      const statusOk = statusFilter === "All" || String(item.status || "active").toLowerCase() === statusFilter.toLowerCase();
      const roleOk = roleFilter === "All" || String(item.role || "student").toLowerCase() === roleFilter.toLowerCase();
      return statusOk && roleOk;
    });
  }, [usersRaw, statusFilter, roleFilter]);

  const table = useTable(filtered, { initialPageSize: 50, initialSortKey: "id" });

  const updateStatusMutation = useMutation({
    mutationFn: ({ userId, payload }) => updateAdminUserStatus(userId, payload),
    onSuccess: () => {
      setStatusModal({ open: false, user: null });
      usersQuery.refetch();
    },
  });

  const columns = [
    {
      key: "user",
      title: "User",
      render: (row) => (
        <div>
          <p className="font-medium">{row.profile?.first_name || "User"} {row.profile?.last_name || row.user_id}</p>
          <p className="text-xs text-[var(--text-secondary)]">{row.profile?.email || "-"}</p>
        </div>
      ),
    },
    { key: "university", title: "University", render: (row) => row.profile?.university || "-" },
    { key: "role", title: "Role", render: (row) => <StatusBadge status={row.role || "student"} /> },
    { key: "status", title: "Status", render: (row) => <StatusBadge status={row.status || "active"} /> },
    { key: "registered", title: "Registered", render: (row) => <span className="font-mono">{formatRelative(row.created_at)}</span> },
    { key: "bookings", title: "Bookings", render: (row) => <span className="font-mono">{row.bookings || 0}</span> },
    {
      key: "actions",
      title: "Actions",
      render: (row) => (
        <ActionMenu>
          <button className="action-btn" onClick={(e) => { e.stopPropagation(); navigate(`/admin/users/${row.user_id}`); }}>👁</button>
          <button className="action-btn" onClick={(e) => { e.stopPropagation(); setStatusModal({ open: true, user: row }); }}>⛔</button>
        </ActionMenu>
      ),
    },
  ];

  return (
    <AdminShell breadcrumb="Management / Users">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold">Users</h1>
          <p className="text-sm text-[var(--text-secondary)]">{table.total.toLocaleString()} users</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="cyan">Export CSV</Button>
          <input value={search} onChange={(e) => setSearch(e.target.value)} className="rounded-md border border-[var(--border-subtle)] bg-elevated px-3 py-2 text-sm" placeholder="Search IDs (comma separated)" />
        </div>
      </div>

      <div className="mb-3 flex flex-wrap gap-2">
        {["All", "Active", "Suspended", "Banned"].map((item) => (
          <Button key={item} variant={statusFilter === item ? "primary" : "outline"} onClick={() => setStatusFilter(item)}>
            {item}
          </Button>
        ))}
        {["All", "Student", "Landlord"].map((item) => (
          <Button key={item} variant={roleFilter === item ? "primary" : "outline"} onClick={() => setRoleFilter(item)}>
            {item}
          </Button>
        ))}
      </div>

      {table.selectedIds.length > 0 ? (
        <div className="mb-3 flex items-center justify-between rounded-md border border-[var(--border-active)] bg-blue/10 px-3 py-2 text-sm">
          <span>{table.selectedIds.length} selected</span>
          <div className="flex gap-2">
            <Button variant="outline">Suspend selected</Button>
            <Button variant="cyan">Export selected</Button>
            <Button variant="danger">Delete</Button>
          </div>
        </div>
      ) : null}

      {usersQuery.isError ? (
        <ErrorState message="Unable to load users." onRetry={() => usersQuery.refetch()} />
      ) : (
        <DataTable
          columns={columns}
          data={table.rows}
          loading={usersQuery.isLoading}
          selectable
          selectedIds={table.selectedIds}
          onToggleSelect={table.toggleSelect}
          onToggleSelectAll={table.toggleSelectAll}
          onSort={table.toggleSort}
          sortKey={table.sortKey}
          sortDirection={table.sortDirection}
          onRowClick={(row) => navigate(`/admin/users/${row.user_id}`)}
          pagination={{ page: table.page, pageSize: table.pageSize, total: table.total, onChange: table.setPage }}
          emptyText="No users found."
        />
      )}

      <Modal open={statusModal.open} onClose={() => setStatusModal({ open: false, user: null })}>
        <h3 className="font-display text-lg">Update User Status</h3>
        <div className="mt-3 space-y-3">
          <select className="w-full rounded-md border border-[var(--border-subtle)] bg-elevated px-3 py-2" value={statusPayload.status} onChange={(e) => setStatusPayload((p) => ({ ...p, status: e.target.value }))}>
            <option value="active">Active</option>
            <option value="suspended">Suspended</option>
          </select>
          <Input label="Reason" value={statusPayload.reason} onChange={(e) => setStatusPayload((p) => ({ ...p, reason: e.target.value }))} />
          <Button
            className="w-full"
            disabled={!statusPayload.reason.trim() || updateStatusMutation.isPending}
            onClick={() =>
              updateStatusMutation.mutate({
                userId: statusModal.user?.user_id,
                payload: statusPayload,
              })
            }
          >
            Confirm
          </Button>
        </div>
      </Modal>
    </AdminShell>
  );
}

