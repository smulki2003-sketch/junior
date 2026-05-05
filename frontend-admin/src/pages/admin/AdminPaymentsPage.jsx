import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getAdminPayments } from "../../api/admin/payments";
import { AdminShell } from "../../components/layout/AdminShell";
import { StatusBadge } from "../../components/shared/StatusBadge";
import { Button } from "../../components/ui/Button";
import { DataTable } from "../../components/ui/DataTable";
import { ErrorState } from "../../components/ui/ErrorState";
import { useTable } from "../../hooks/useTable";
import { formatCurrency, formatDateTime, formatId } from "../../utils/formatters";

export default function AdminPaymentsPage() {
  const [statusFilter, setStatusFilter] = useState("All");
  const query = useQuery({
    queryKey: ["admin-payments"],
    queryFn: () => getAdminPayments(),
  });

  const source = query.data?.results || query.data || [];
  const payoutEligible = useMemo(
    () =>
      source.filter(
        (item) =>
          ["success", "succeeded"].includes(String(item.status || "").toLowerCase()) &&
          String(item.booking_status || "").toLowerCase() === "completed"
      ),
    [source]
  );
  const filtered = useMemo(
    () => payoutEligible.filter((x) => statusFilter === "All" || String(x.status).toLowerCase() === statusFilter.toLowerCase()),
    [payoutEligible, statusFilter]
  );
  const table = useTable(filtered, { initialPageSize: 20, initialSortKey: "id" });

  const totalRevenue = filtered.reduce((acc, item) => acc + Number(item.amount || 0), 0);
  const successCount = filtered.length;
  const awaitingCompletionCount = source.filter(
    (item) =>
      ["success", "succeeded"].includes(String(item.status || "").toLowerCase()) &&
      String(item.booking_status || "").toLowerCase() !== "completed"
  ).length;

  const columns = [
    { key: "payment_id", title: "Payment ID", render: (row) => <span className="font-mono">{formatId("PAY", row.id)}</span> },
    { key: "booking_id", title: "Booking ID", render: (row) => <span className="text-blue">{formatId("B", row.booking_id)}</span> },
    { key: "user", title: "User", render: (row) => row.user_name || `User ${row.user_id}` },
    { key: "amount", title: "Amount", render: (row) => <span className="font-mono">{formatCurrency(row.amount)}</span> },
    { key: "method", title: "Method", render: (row) => `•••• ${row.last4 || "4242"}` },
    { key: "booking_status", title: "Booking", render: (row) => <StatusBadge status={row.booking_status || "pending"} /> },
    { key: "status", title: "Status", render: (row) => <StatusBadge status={row.status || "pending"} /> },
    { key: "created_at", title: "Created At", render: (row) => <span className="font-mono text-xs">{formatDateTime(row.created_at)}</span> },
    {
      key: "actions",
      title: "Actions",
      render: (row) => (
        <div className="flex gap-1">
          <button className="action-btn">View receipt</button>
          {String(row.status).toLowerCase() === "failed" ? <button className="action-btn text-danger">Retry</button> : null}
          {String(row.status).toLowerCase() === "succeeded" ? <button className="action-btn text-cyan">Refund</button> : null}
        </div>
      ),
    },
  ];

  return (
    <AdminShell breadcrumb="Management / Payments">
      <div className="mb-4 grid grid-cols-1 gap-3 md:grid-cols-3">
        <div className="rounded-[10px] border border-[var(--table-border)] bg-elevated p-4">
          <p className="text-xs text-[var(--text-secondary)]">Recognized Revenue (Completed Bookings)</p>
          <p className="font-mono text-2xl">{formatCurrency(totalRevenue)}</p>
        </div>
        <div className="rounded-[10px] border border-[var(--table-border)] bg-elevated p-4">
          <p className="text-xs text-[var(--text-secondary)]">Eligible Payments</p>
          <p className="font-mono text-2xl">{successCount}</p>
        </div>
        <div className="rounded-[10px] border border-[var(--table-border)] bg-elevated p-4">
          <p className="text-xs text-[var(--text-secondary)]">Waiting Booking Completion</p>
          <p className={`font-mono text-2xl ${awaitingCompletionCount > 0 ? "text-amber" : ""}`}>{awaitingCompletionCount}</p>
        </div>
      </div>

      <div className="mb-3 flex gap-2">
        {["All", "Success", "Pending", "Failed"].map((item) => (
          <Button key={item} variant={statusFilter === item ? "primary" : "outline"} onClick={() => setStatusFilter(item)}>
            {item}
          </Button>
        ))}
      </div>

      {query.isError ? (
        <ErrorState message="Unable to load payments." onRetry={() => query.refetch()} />
      ) : (
        <DataTable
          columns={columns}
          data={table.rows}
          loading={query.isLoading}
          onSort={table.toggleSort}
          sortKey={table.sortKey}
          sortDirection={table.sortDirection}
          pagination={{ page: table.page, pageSize: table.pageSize, total: table.total, onChange: table.setPage }}
          emptyText="No payments are eligible yet. Mark bookings as completed first."
        />
      )}
    </AdminShell>
  );
}
