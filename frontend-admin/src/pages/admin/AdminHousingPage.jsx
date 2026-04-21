import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AnimatePresence, motion } from "framer-motion";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getPendingHousing, updateHousingApproval } from "../../api/admin/housing";
import { AdminShell } from "../../components/layout/AdminShell";
import { StatusBadge } from "../../components/shared/StatusBadge";
import { Button } from "../../components/ui/Button";
import { ErrorState } from "../../components/ui/ErrorState";
import { Input } from "../../components/ui/Input";
import { Skeleton } from "../../components/ui/Skeleton";
import { formatRelative } from "../../utils/formatters";

const tabs = ["Pending Review", "Approved", "Rejected", "All"];

export default function AdminHousingPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState("Pending Review");
  const [selectedId, setSelectedId] = useState(null);
  const [rejectionReason, setRejectionReason] = useState("");

  const queueQuery = useQuery({
    queryKey: ["admin-housing-pending"],
    queryFn: () => getPendingHousing(),
  });

  const rows = queueQuery.data?.results || queueQuery.data || [];
  const selected = useMemo(
    () => rows.find((row) => String(row.id) === String(selectedId)) || rows[0] || null,
    [rows, selectedId]
  );

  const approvalMutation = useMutation({
    mutationFn: ({ unitId, payload }) => updateHousingApproval(unitId, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-housing-pending"] }),
  });

  return (
    <AdminShell breadcrumb="Management / Housing" complaintCount={0}>
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h1 className="font-display text-2xl font-semibold">Listing Moderation</h1>
          <span className="badge-pending rounded-full bg-amber/20 px-2 py-1 text-xs text-amber">
            {rows.length} pending
          </span>
        </div>
      </div>
      <div className="mb-3 flex gap-2">
        {tabs.map((item) => (
          <Button key={item} variant={tab === item ? "primary" : "outline"} onClick={() => setTab(item)}>
            {item}
          </Button>
        ))}
      </div>

      {queueQuery.isLoading ? (
        <Skeleton className="h-[560px]" />
      ) : queueQuery.isError ? (
        <ErrorState message="Unable to load moderation queue." onRetry={() => queueQuery.refetch()} />
      ) : (
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-[360px_1fr]">
          <aside className="max-h-[calc(100vh-180px)] overflow-y-auto rounded-[10px] border border-[var(--table-border)] bg-surface p-2">
            <AnimatePresence>
              {rows.map((item) => (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className={`mb-2 rounded-md border p-2 ${String(selected?.id) === String(item.id) ? "border-blue" : "border-[var(--table-border)]"}`}
                  onClick={() => setSelectedId(item.id)}
                >
                  <div className="flex gap-2">
                    <img
                      src={item.image_url || "https://images.unsplash.com/photo-1494526585095-c41746248156?q=80&w=500&auto=format&fit=crop"}
                      alt={item.title || "Listing thumbnail"}
                      className="h-14 w-14 rounded-md object-cover"
                    />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{item.title || `Listing #${item.id}`}</p>
                      <p className="truncate text-xs text-[var(--text-secondary)]">{item.location || "Location"}</p>
                      <p className="text-xs text-amber">Waiting {formatRelative(item.created_at || new Date())}</p>
                    </div>
                  </div>
                  <div className="mt-2 flex gap-2">
                    <Button
                      variant="success"
                      className="flex-1 text-xs"
                      onClick={(e) => {
                        e.stopPropagation();
                        approvalMutation.mutate({ unitId: item.id, payload: { approval: "approved", reason: "Approved by moderator" } });
                      }}
                    >
                      ✓ Approve
                    </Button>
                    <Button
                      variant="danger"
                      className="flex-1 text-xs"
                      onClick={(e) => {
                        e.stopPropagation();
                        approvalMutation.mutate({ unitId: item.id, payload: { approval: "rejected", reason: "Rejected by moderator" } });
                      }}
                    >
                      ✕ Reject
                    </Button>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </aside>

          <section className="rounded-[10px] border border-[var(--table-border)] bg-surface p-4">
            {selected ? (
              <>
                <div className="mb-3 flex items-center justify-between">
                  <h2 className="font-display text-xl">{selected.title || `Listing #${selected.id}`}</h2>
                  <StatusBadge status={selected.moderation_status || "pending"} />
                </div>
                <div className="mb-3 grid grid-cols-2 gap-2 md:grid-cols-4">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <img
                      key={i}
                      src={selected.image_url || "https://images.unsplash.com/photo-1494526585095-c41746248156?q=80&w=600&auto=format&fit=crop"}
                      alt={`Listing gallery ${i + 1}`}
                      className="h-24 w-full rounded-md object-cover"
                    />
                  ))}
                </div>
                <p className="mb-3 text-sm text-[var(--text-secondary)]">{selected.description || "Listing preview details and amenities."}</p>
                <div className="mb-4 rounded-md border border-[var(--table-border)] bg-elevated p-3 text-sm">
                  <p>Landlord: {selected.owner_name || "Owner"}</p>
                  <p>Email: {selected.owner_email || "-"}</p>
                  <p>Total listings: {selected.owner_total_listings || 0}</p>
                </div>

                <div className="sticky bottom-0 space-y-2 rounded-md border border-[var(--table-border)] bg-elevated p-3">
                  <Button
                    className="w-full"
                    variant="success"
                    onClick={() => approvalMutation.mutate({ unitId: selected.id, payload: { approval: "approved", reason: "Approved by admin" } })}
                  >
                    Approve Listing
                  </Button>
                  <Input label="Rejection reason" value={rejectionReason} onChange={(e) => setRejectionReason(e.target.value)} />
                  <Button
                    className="w-full"
                    variant="danger"
                    disabled={!rejectionReason.trim()}
                    onClick={() => approvalMutation.mutate({ unitId: selected.id, payload: { approval: "rejected", reason: rejectionReason } })}
                  >
                    Reject Listing
                  </Button>
                  <Button className="w-full" variant="outline">
                    Flag for Review
                  </Button>
                  <Button className="w-full" variant="ghost" onClick={() => navigate(`/admin/housing/${selected.id}`)}>
                    Open Detail Page
                  </Button>
                </div>
              </>
            ) : (
              <p className="text-sm text-[var(--text-secondary)]">No listing selected.</p>
            )}
          </section>
        </div>
      )}
    </AdminShell>
  );
}

