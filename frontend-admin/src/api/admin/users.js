import client from "../client";

export async function getAdminUsers(params) {
  const { data } = await client.get("/api/v1/admin/users", { params });
  return data;
}

export async function updateAdminUserStatus(userId, payload) {
  const { data } = await client.patch(`/api/v1/admin/users/${userId}/status`, payload);
  return data;
}

