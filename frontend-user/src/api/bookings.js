import client from "./client";

export const createBooking = async (payload) => {
  const { data } = await client.post("/api/v1/bookings", payload);
  return data;
};

export const getUserBookings = async (userId) => {
  const { data } = await client.get(`/api/v1/bookings/users/${userId}`);
  return data;
};

export const getBookingDetail = async (bookingId) => {
  const { data } = await client.get(`/api/v1/bookings/${bookingId}`);
  return data;
};

export const getBookingTimeline = async (bookingId) => {
  const { data } = await client.get(`/api/v1/bookings/${bookingId}/timeline`);
  return data;
};

