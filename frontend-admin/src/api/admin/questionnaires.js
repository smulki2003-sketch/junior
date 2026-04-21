import client from "../client";

export async function getRoommateQuestionnaire() {
  try {
    const { data } = await client.get("/api/v1/roommate/ai/roommates/questionnaire");
    return data;
  } catch (error) {
    if (error?.response?.status === 404) {
      return {
        title: "Roommate Lifestyle Questionnaire",
        version: 1,
        is_active: true,
        questions: [],
      };
    }
    throw error;
  }
}

export async function upsertRoommateQuestionnaire(payload) {
  const { data } = await client.post("/api/v1/roommate/ai/roommates/questionnaire", payload);
  return data;
}
