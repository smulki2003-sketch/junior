import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { exportReports, getReportKPIs } from "../../api/admin/reports";
import { AdminShell } from "../../components/layout/AdminShell";
import { KPICard } from "../../components/shared/KPICard";
import { Button } from "../../components/ui/Button";
import { ErrorState } from "../../components/ui/ErrorState";
import { Skeleton } from "../../components/ui/Skeleton";

const rangeOptions = [
  { label: "Today", value: "today" },
  { label: "7d", value: "7d" },
  { label: "30d", value: "30d" },
  { label: "90d", value: "90d" },
];

export default function AdminReportsPage() {
  const [range, setRange] = useState("30d");
  const [reportType, setReportType] = useState("kpis");
  const [downloadUrl, setDownloadUrl] = useState("");
  const [refreshVersion, setRefreshVersion] = useState(0);
  const reportsQuery = useQuery({
    queryKey: ["admin-reports-kpis", range, refreshVersion],
    queryFn: () => getReportKPIs({ range, refresh: refreshVersion > 0 ? "true" : "false" }),
  });

  const summary = reportsQuery.data?.summary || {};
  const rows = Array.isArray(reportsQuery.data?.results) ? reportsQuery.data.results : [];

  const cards = useMemo(
    () => [
      { icon: "Days", value: Number(summary.days || 0), label: "Days", accent: "var(--accent-primary)" },
      { icon: "Users", value: Number(summary.active_users || 0), label: "Active Users", accent: "var(--accent-success)" },
      { icon: "New", value: Number(summary.new_registrations || 0), label: "New Registrations", accent: "var(--accent-purple)" },
      { icon: "Bookings", value: Number(summary.total_bookings || 0), label: "Total Bookings", accent: "var(--accent-cyan)" },
      { icon: "Volume", value: Number(summary.gross_volume || 0), label: "Gross Volume", accent: "var(--accent-warning)" },
    ],
    [summary]
  );

  async function handleExport() {
    const endDate = new Date();
    const startDate = new Date(endDate);
    if (range === "today") startDate.setDate(endDate.getDate());
    if (range === "7d") startDate.setDate(endDate.getDate() - 6);
    if (range === "30d") startDate.setDate(endDate.getDate() - 29);
    if (range === "90d") startDate.setDate(endDate.getDate() - 89);
    const fmt = (d) => d.toISOString().slice(0, 10);
    const blob = await exportReports({
      report_type: reportType,
      start_date: fmt(startDate),
      end_date: fmt(endDate),
    });
    const url = URL.createObjectURL(blob);
    setDownloadUrl(url);
  }

  return (
    <AdminShell breadcrumb="Analytics / Reports">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-2">
          {rangeOptions.map((item) => (
            <Button key={item.value} variant={range === item.value ? "primary" : "outline"} onClick={() => setRange(item.value)}>
              {item.label}
            </Button>
          ))}
        </div>
        <Button variant="outline" onClick={() => setRefreshVersion((value) => value + 1)}>Refresh</Button>
      </div>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <select
          className="rounded-md border border-[var(--border-subtle)] bg-elevated px-3 py-2 text-sm"
          value={reportType}
          onChange={(e) => setReportType(e.target.value)}
        >
          <option value="kpis">KPIs</option>
          <option value="bookings">Bookings</option>
          <option value="payments">Payments</option>
          <option value="housing">Housing</option>
          <option value="ai_recommendations">AI Recommendations</option>
          <option value="ai_roommates">AI Roommates</option>
          <option value="moderation">Moderation</option>
        </select>
        <Button onClick={handleExport}>Generate Export</Button>
        {downloadUrl ? (
          <a href={downloadUrl} download={`${reportType}_report.csv`} className="text-sm text-primary underline">
            Download Export
          </a>
        ) : null}
      </div>

      {reportsQuery.isLoading ? (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          {Array.from({ length: 5 }).map((_, index) => (
            <Skeleton key={index} className="h-28" />
          ))}
        </div>
      ) : reportsQuery.isError ? (
        <ErrorState message="Unable to load reports data." onRetry={() => reportsQuery.refetch()} />
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-5">
            {cards.map((item) => (
              <KPICard key={item.label} icon={item.icon} value={item.value} label={item.label} delta="" accent={item.accent} />
            ))}
          </div>

          <div className="rounded-[10px] border border-[var(--table-border)] bg-surface p-4">
            <h2 className="mb-3 font-display text-lg">Daily KPI Rows (from database)</h2>
            {!rows.length ? (
              <p className="text-sm text-[var(--text-secondary)]">No KPI rows found for selected range.</p>
            ) : (
              <div className="overflow-auto">
                <table className="min-w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-[var(--table-border)]">
                      <th className="px-2 py-2">Date</th>
                      <th className="px-2 py-2">Active Users</th>
                      <th className="px-2 py-2">New Registrations</th>
                      <th className="px-2 py-2">Bookings</th>
                      <th className="px-2 py-2">Gross Volume</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row) => (
                      <tr key={row.date} className="border-b border-[var(--table-border)]/50">
                        <td className="px-2 py-2">{row.date}</td>
                        <td className="px-2 py-2">{row.active_users}</td>
                        <td className="px-2 py-2">{row.new_registrations}</td>
                        <td className="px-2 py-2">{row.total_bookings}</td>
                        <td className="px-2 py-2">{row.gross_volume}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </AdminShell>
  );
}
