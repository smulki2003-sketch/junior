import client from "./client";

export const createPaymentIntent = async (payload) => {
  const { data } = await client.post("/api/v1/payments/intents", payload);
  return data;
};

export const simulatePaymentSuccess = async (paymentIntentId) => {
  const { data } = await client.post(`/api/v1/payments/${paymentIntentId}/simulate-success`);
  return data;
};

export const getPaymentBanks = async () => {
  const { data } = await client.get("/api/v1/payments/banks");
  return data;
};
