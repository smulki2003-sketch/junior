import client from "../client";

export async function getPendingHousing(params) {
  const { data } = await client.get("/api/v1/admin/housing/pending", { params });
  return data;
}

export async function updateHousingApproval(unitId, payload) {
  const { data } = await client.patch(`/api/v1/admin/housing/${unitId}/approval`, payload);
  return data;
}

