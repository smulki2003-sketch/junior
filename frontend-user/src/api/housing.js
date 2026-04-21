import client from "./client";

export const searchHousing = async (params) => {
  const { data } = await client.get("/api/v1/search/housing", { params });
  return data;
};

export const getHousingUnit = async (unitId) => {
  const { data } = await client.get(`/api/v1/housing/units/${unitId}`);
  return data;
};

