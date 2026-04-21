import client from "../client";

export async function getAdminPayments(params) {
  const { data } = await client.get("/api/v1/admin/payments", { params });
  return data;
}

