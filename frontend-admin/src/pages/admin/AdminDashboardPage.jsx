import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { getDashboardOverview } from "../../api/admin/reports";
import { staggerTable, tableRowEnter } from "../../animations/variants";
import { BookingsLineChart } from "../../components/charts/BookingsLineChart";
import { StatusDonutChart } from "../../components/charts/StatusDonutChart";
import { AdminShell } from "../../components/layout/AdminShell";
import { KPICard } from "../../components/shared/KPICard";
import { Button } from "../../components/ui/Button";
import { ErrorState } from "../../components/ui/ErrorState";
import { Skeleton } from "../../components/ui/Skeleton";
import { formatDateTime, formatRelative } from "../../utils/formatters";

export default function AdminDashboardPage() {
  const overviewQuery = useQuery({
    queryKey: ["admin-dashboard-overview"],
    queryFn: getDashboardOverview,
  });

  const overview = overviewQuery.data || {};
  const now = new Date();
  const activity = Array.isArray(overview.activity) ? overview.activity.slice(0, 20) : [];
  const chartData = Array.isArray(overview.booking_trend) ? overview.booking_trend : [];

  return (
    <AdminShell breadcrumb="Overview / Dashboard" complaintCount={overview.open_complaints_count || 0}>
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold">Admin Dashboard</h1>
          <p className="text-sm text-[var(--text-secondary)]">{formatDateTime(now)} - live data from services.</p>
        </div>
        <div className="text-right">
          <Button variant="outline" onClick={() => overviewQuery.refetch()}>Refresh Data</Button>
          <p className="mt-2 text-xs text-[var(--text-secondary)]">Last updated: {formatDateTime(now)}</p>
        </div>
      </div>

      {overviewQuery.isLoading ? (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      ) : overviewQuery.isError ? (
        <ErrorState message="Unable to load dashboard overview." onRetry={() => overviewQuery.refetch()} />
      ) : (
        <>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
            <KPICard icon="Users" value={overview.total_users ?? 0} label="Total Users" delta="" accent="var(--accent-primary)" />
            <KPICard icon="Housing" value={overview.active_listings ?? 0} label="Active Listings" delta="" accent="var(--accent-success)" />
            <KPICard icon="Bookings" value={overview.bookings_this_month ?? 0} label="Bookings This Month" delta="" accent="var(--accent-purple)" />
            <KPICard icon="Revenue" value={overview.revenue ?? 0} label="Revenue" delta="" accent="var(--accent-cyan)" />
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-2">
            <div className="rounded-[10px] border border-[var(--table-border)] bg-surface p-4">
              <h3 className="mb-2 font-display text-lg">Bookings Over Time</h3>
              {chartData.length ? <BookingsLineChart data={chartData} /> : <p className="text-sm text-[var(--text-secondary)]">No booking trend data yet.</p>}
            </div>
            <div className="rounded-[10px] border border-[var(--table-border)] bg-surface p-4">
              <h3 className="mb-2 font-display text-lg">Listing Status Breakdown</h3>
              <StatusDonutChart
                data={[
                  { name: "Approved", value: overview.approved_listings ?? 0 },
                  { name: "Pending", value: overview.pending_housing_count ?? 0 },
                  { name: "Rejected", value: overview.rejected_listings ?? 0 },
                ]}
              />
            </div>
          </div>

          <div className="mt-4 rounded-[10px] border border-[var(--table-border)] bg-surface p-4">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="font-display text-lg">Recent Activity</h3>
            </div>
            <motion.div variants={staggerTable} initial="hidden" animate="visible" className="space-y-2">
              {activity.map((item, index) => (
                <motion.div key={item.id || index} variants={tableRowEnter} className="table-row rounded-md px-3 py-2">
                  <div className="flex items-center justify-between">
                    <p className="text-sm">
                      {item.description || "Activity"}
                      {item.entity ? <span className="text-blue"> - {item.entity}</span> : null}
                    </p>
                    <p className="text-xs text-[var(--text-secondary)]">{item.created_at ? formatRelative(item.created_at) : "-"}</p>
                  </div>
                </motion.div>
              ))}
              {!activity.length ? <p className="text-sm text-[var(--text-secondary)]">No recent activity found.</p> : null}
            </motion.div>
          </div>
        </>
      )}
    </AdminShell>
  );
}
