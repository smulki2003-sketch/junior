import client from "./client";

export const listMyComplaints = async () => {
  const { data } = await client.get("/api/v1/moderation/complaints");
  return data;
};

export const createComplaint = async (payload) => {
  const { data } = await client.post("/api/v1/moderation/complaints", payload);
  return data;
};

export const getComplaintDetail = async (complaintId) => {
  const { data } = await client.get(`/api/v1/moderation/complaints/${complaintId}`);
  return data;
};
