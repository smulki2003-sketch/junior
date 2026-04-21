import client from "../client";

export async function sendBroadcast(payload) {
  const { data } = await client.post("/api/v1/admin/notifications/broadcast", payload);
  return data;
}

