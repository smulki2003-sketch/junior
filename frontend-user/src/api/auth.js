import client from "./client";

export const registerRequest = async (payload) => {
  const { data } = await client.post("/api/v1/auth/register", payload);
  return data;
};

export const loginRequest = async (payload) => {
  const { data } = await client.post("/api/v1/auth/login", payload);
  return data;
};

export const getMeRequest = async () => {
  const { data } = await client.get("/api/v1/auth/me");
  return data;
};
