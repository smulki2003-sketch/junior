import client from "./client";

export const getRoommateQuestionnaire = async () => {
  const { data } = await client.get("/api/v1/roommate/ai/roommates/questionnaire");
  return data;
};

export const submitRoommateAnswers = async (userId, answers) => {
  const { data } = await client.post(`/api/v1/roommate/ai/roommates/answers/${userId}`, { answers });
  return data;
};

export const refreshRoommateMatches = async (userId, payload = {}) => {
  const { data } = await client.post(`/api/v1/roommate/ai/roommates/matches/${userId}/refresh`, payload);
  return data;
};

export const getRoommateMatches = async (userId) => {
  const { data } = await client.get(`/api/v1/roommate/ai/roommates/matches/${userId}`);
  return data;
};
