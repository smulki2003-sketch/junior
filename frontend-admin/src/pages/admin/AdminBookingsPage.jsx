import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import toast from "react-hot-toast";
import { useNavigate } from "react-router-dom";
import { getAdminBookings, overrideBookingStatus } from "../../api/admin/bookings";
import { AdminShell } from "../../components/layout/AdminShell";
import { ActionMenu } from "../../components/shared/ActionMenu";
import { StatusBadge } from "../../components/shared/StatusBadge";
import { Button } from "../../components/ui/Button";
import { DataTable } from "../../components/ui/DataTable";
import { ErrorState } from "../../components/ui/ErrorState";
import { Modal } from "../../components/ui/Modal";
import { useTable } from "../../hooks/useTable";
import { formatCurrency, formatDate, formatId } from "../../utils/formatters";

export default function AdminBookingsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("All");
  const [searchValue, setSearchValue] = useState("");
  const [overrideModal, setOverrideModal] = useState({ open: false, booking: null });
  const [overridePayload, setOverridePayload] = useState({ status: "confirmed", reason: "" });

  const query = useQuery({
    queryKey: ["admin-bookings", searchValue],
    queryFn: () => getAdminBookings({ booking_ids: searchValue }),
  });
  const source = query.data?.results || query.data || [];
  const filtered = useMemo(
    () => source.filter((x) => statusFilter === "All" || String(x.status).toLowerCase() === statusFilter.toLowerCase()),
    [source, statusFilter]
  );
  const table = useTable(filtered, { initialPageSize: 20, initialSortKey: "id" });

  const overrideMutation = useMutation({
    mutationFn: ({ bookingId, payload }) => overrideBookingStatus(bookingId, payload),
    onSuccess: (response, variables) => {
      queryClient.setQueryData(["admin-bookings", searchValue], (current) => {
        const sourceRows = current?.results || current || [];
        if (!Array.isArray(sourceRows)) return current;
        const nextRows = sourceRows.map((row) =>
          row.id === variables.bookingId ? { ...row, status: response?.status || variables.payload.status } : row
        );
        return current?.results ? { ...current, results: nextRows } : nextRows;
      });
      setOverrideModal({ open: false, booking: null });
      setOverridePayload({ status: "confirmed", reason: "" });
      query.refetch();
      toast.success("Booking status updated.");
    },
    onError: (error) => {
      const message =
        error?.response?.data?.error?.message
        || error?.response?.data?.error?.details
        || "Unable to update booking status.";
      toast.error(message);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-bookings"] });
    },
  });
  const overrideErrorText =
    overrideMutation.error?.response?.data?.error?.details
    || overrideMutation.error?.response?.data?.error?.message
    || "";

  const columns = [
    { key: "booking_id", title: "Booking ID", render: (row) => <span className="font-mono">{formatId("B", row.id)}</span> },
    { key: "tenant", title: "Tenant", render: (row) => <div><p>{row.user_name || `User ${row.user_id}`}</p><p className="text-xs text-[var(--text-secondary)]">{row.user_email || "-"}</p></div> },
    { key: "property", title: "Property", render: (row) => <span className="max-w-[160px] truncate">{row.unit_name || `Unit ${row.unit_id}`}</span> },
    { key: "dates", title: "Dates", render: (row) => <span className="font-mono text-xs">{formatDate(row.start_date)} → {formatDate(row.end_date)}</span> },
    { key: "amount", title: "Amount", render: (row) => <span className="font-mono">{formatCurrency(row.total_price)}</span> },
    { key: "bank", title: "Bank", render: (row) => <span>{row.payer_bank_name || "-"}</span> },
    {
      key: "account",
      title: "Account",
      render: (row) => <span className="font-mono">{row.payer_account_number || "-"}</span>,
    },
    { key: "status", title: "Status", render: (row) => <StatusBadge status={row.status} /> },
    { key: "payment", title: "Payment", render: (row) => <StatusBadge status={row.payment_status || "pending"} /> },
    {
      key: "actions",
      title: "Actions",
      render: (row) => (
        <ActionMenu>
          <button className="action-btn" onClick={(e) => { e.stopPropagation(); navigate(`/admin/bookings/${row.id}`); }}>
            View
          </button>
          <button className="action-btn" onClick={(e) => { e.stopPropagation(); setOverrideModal({ open: true, booking: row }); }}>
            Override
          </button>
        </ActionMenu>
      ),
    },
  ];

  return (
    <AdminShell breadcrumb="Management / Bookings">
      <div className="mb-3 flex flex-wrap gap-2">
        {["All", "Pending", "Confirmed", "Completed", "Cancelled", "Failed"].map((item) => (
          <Button key={item} variant={statusFilter === item ? "primary" : "outline"} onClick={() => setStatusFilter(item)}>
            {item}
          </Button>
        ))}
        <input
          className="rounded-md border border-[var(--border-subtle)] bg-elevated px-3 py-2 text-sm"
          value={searchValue}
          onChange={(e) => setSearchValue(e.target.value)}
          placeholder="Search booking IDs"
        />
      </div>

      {query.isError ? (
        <ErrorState message="Unable to load bookings." onRetry={() => query.refetch()} />
      ) : (
        <DataTable
          columns={columns}
          data={table.rows}
          loading={query.isLoading}
          onRowClick={(row) => navigate(`/admin/bookings/${row.id}`)}
          onSort={table.toggleSort}
          sortKey={table.sortKey}
          sortDirection={table.sortDirection}
          pagination={{ page: table.page, pageSize: table.pageSize, total: table.total, onChange: table.setPage }}
          emptyText="No bookings found."
        />
      )}

      <Modal open={overrideModal.open} onClose={() => setOverrideModal({ open: false, booking: null })}>
        <h3 className="font-display text-lg">Override Booking Status</h3>
        <p className="mt-1 text-xs text-[var(--text-secondary)]">Current status: {overrideModal.booking?.status || "-"}</p>
        <div className="mt-3 space-y-3">
          <select
            className="w-full rounded-md border border-[var(--border-subtle)] bg-elevated px-3 py-2"
            value={overridePayload.status}
            onChange={(e) => setOverridePayload((prev) => ({ ...prev, status: e.target.value }))}
          >
            <option value="pending">Pending</option>
            <option value="confirmed">Confirmed</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
            <option value="failed">Failed</option>
          </select>
          <textarea
            className="h-28 w-full rounded-md border border-[var(--border-subtle)] bg-elevated px-3 py-2 text-sm"
            placeholder="Reason for override (min 3 chars)"
            value={overridePayload.reason}
            onChange={(e) => setOverridePayload((prev) => ({ ...prev, reason: e.target.value }))}
          />
          {overrideErrorText ? <p className="text-xs text-danger">{overrideErrorText}</p> : null}
          <p className="text-xs text-amber">⚠️ This action will be logged and cannot be undone.</p>
          <Button
            className="w-full"
            disabled={overridePayload.reason.trim().length < 3 || overrideMutation.isPending}
            onClick={() =>
              overrideMutation.mutate({
                bookingId: overrideModal.booking?.id,
                payload: overridePayload,
              })
            }
          >
            {overrideMutation.isPending ? "Updating..." : "Confirm Override"}
          </Button>
        </div>
      </Modal>
    </AdminShell>
  );
}
