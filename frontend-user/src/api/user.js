import client from "./client";

export const getUserProfile = async (userId) => {
  const { data } = await client.get(`/api/v1/users/${userId}/profile`);
  return data;
};

export const updateUserProfile = async (userId, payload) => {
  const { data } = await client.put(`/api/v1/users/${userId}/profile`, payload);
  return data;
};

export const getProfileMetadata = async () => {
  const { data } = await client.get("/api/v1/users/metadata/profile-options");
  return data;
};

export const getHousingPreferences = async (userId) => {
  const { data } = await client.get(`/api/v1/users/${userId}/preferences/housing`);
  return data;
};

export const updateHousingPreferences = async (userId, payload) => {
  const { data } = await client.put(`/api/v1/users/${userId}/preferences/housing`, payload);
  return data;
};
