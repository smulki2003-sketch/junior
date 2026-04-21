import client from "../client";

export async function getDashboardOverview() {
  const { data } = await client.get("/api/v1/admin/dashboard/overview");
  return data;
}

export async function getReportKPIs(params) {
  const { data } = await client.get("/api/v1/reports/kpis", { params: { ...(params || {}), refresh: "true" } });
  return data;
}

export async function exportReports(params) {
  const response = await client.get("/api/v1/reports/export", {
    params,
    responseType: "blob",
  });
  return response.data;
}
