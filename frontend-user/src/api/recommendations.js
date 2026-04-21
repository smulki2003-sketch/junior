import client from "./client";

export const getRecommendations = async (userId) => {
  const { data } = await client.get(`/api/v1/ai/recommendations/housing/${userId}`);
  return data;
};

export const refreshRecommendations = async (userId, payload = {}) => {
  const { data } = await client.post(`/api/v1/ai/recommendations/housing/${userId}/refresh`, payload);
  return data;
};
