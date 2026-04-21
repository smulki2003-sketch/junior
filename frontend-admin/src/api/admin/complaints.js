import client from "../client";

export async function getAdminComplaints(params) {
  const { data } = await client.get("/api/v1/admin/complaints", { params });
  return data;
}

export async function getComplaintDetail(complaintId) {
  const { data } = await client.get(`/api/v1/moderation/complaints/${complaintId}`);
  return data;
}

export async function updateComplaintStatus(complaintId, payload) {
  const { data } = await client.patch(`/api/v1/moderation/complaints/${complaintId}/status`, payload);
  return data;
}

export async function addComplaintComment(caseId, payload) {
  const { data } = await client.post(`/api/v1/moderation/cases/${caseId}/comments`, payload);
  return data;
}
