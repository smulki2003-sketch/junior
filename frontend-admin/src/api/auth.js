import client from "./client";

export async function adminLogin(payload) {
  const { data } = await client.post("/api/v1/auth/login", payload);
  return data;
}

