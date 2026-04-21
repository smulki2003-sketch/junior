import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useParams } from "react-router-dom";
import { getPendingHousing, updateHousingApproval } from "../../api/admin/housing";
import { AdminShell } from "../../components/layout/AdminShell";
import { AuditLog } from "../../components/shared/AuditLog";
import { StatusBadge } from "../../components/shared/StatusBadge";
import { Button } from "../../components/ui/Button";
import { ErrorState } from "../../components/ui/ErrorState";
import { Input } from "../../components/ui/Input";
import { Skeleton } from "../../components/ui/Skeleton";

export default function AdminHousingDetailPage() {
  const { id } = useParams();
  const hasValidId = id != null && id !== "undefined" && id !== "null";
  const [reason, setReason] = useState("");

  const query = useQuery({
    queryKey: ["admin-housing-detail", id],
    queryFn: async () => {
      const payload = await getPendingHousing();
      const items = payload.results || payload || [];
      return items.find((item) => String(item.id) === String(id)) || null;
    },
    enabled: hasValidId,
  });

  const mutation = useMutation({
    mutationFn: ({ approval, reason }) => updateHousingApproval(id, { approval, reason }),
    onSuccess: () => query.refetch(),
  });

  if (!hasValidId) {
    return (
      <AdminShell breadcrumb="Management / Housing / Detail">
        <ErrorState message="Invalid listing id." />
      </AdminShell>
    );
  }

  if (query.isLoading) {
    return (
      <AdminShell breadcrumb="Management / Housing / Detail">
        <Skeleton className="h-[460px]" />
      </AdminShell>
    );
  }

  if (query.isError || !query.data) {
    return (
      <AdminShell breadcrumb="Management / Housing / Detail">
        <ErrorState message="Unable to load listing detail." onRetry={() => query.refetch()} />
      </AdminShell>
    );
  }

  const item = query.data;
  const history = item.history || [
    { id: 1, admin_name: "Ahmed", action: "Submitted for review", created_at: new Date().toISOString() },
  ];

  return (
    <AdminShell breadcrumb="Management / Housing / Detail">
      <div className="space-y-4 rounded-[10px] border border-[var(--table-border)] bg-surface p-4">
        <div className="flex items-center justify-between">
          <h1 className="font-display text-2xl font-semibold">{item.title || `Listing #${item.id}`}</h1>
          <StatusBadge status={item.moderation_status || "pending"} />
        </div>

        <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <img key={i} src={item.image_url || "https://images.unsplash.com/photo-1494526585095-c41746248156?q=80&w=600&auto=format&fit=crop"} alt={`Listing detail image ${i + 1}`} className="h-28 w-full rounded-md object-cover" />
          ))}
        </div>

        <p className="text-sm text-[var(--text-secondary)]">{item.description || "Listing detail and moderation context."}</p>

        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <div className="rounded-md border border-[var(--table-border)] bg-elevated p-3 text-sm">
            <p>Landlord: {item.owner_name || "-"}</p>
            <p>Email: {item.owner_email || "-"}</p>
            <p>Account age: {item.owner_account_age || "-"}</p>
          </div>
          <div className="rounded-md border border-[var(--table-border)] bg-elevated p-3 text-sm">
            <p>Price: {item.price || "-"}</p>
            <p>Location: {item.location || "-"}</p>
            <p>Amenities: {(item.amenities || []).join(", ") || "-"}</p>
          </div>
        </div>

        <div className="rounded-md border border-[var(--table-border)] bg-elevated p-3">
          <h3 className="mb-2 font-display text-sm">Decision Panel</h3>
          <div className="space-y-2">
            <Button className="w-full" variant="success" onClick={() => mutation.mutate({ approval: "approved", reason: "Approved" })}>Approve Listing</Button>
            <Input label="Rejection reason" value={reason} onChange={(e) => setReason(e.target.value)} />
            <Button className="w-full" variant="danger" onClick={() => mutation.mutate({ approval: "rejected", reason: reason || "Rejected by reviewer" })}>Reject Listing</Button>
            <Button className="w-full" variant="outline">Flag for Review</Button>
          </div>
        </div>

        <AuditLog entries={history} />
      </div>
    </AdminShell>
  );
}
