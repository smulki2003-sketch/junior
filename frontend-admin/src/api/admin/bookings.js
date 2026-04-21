import client from "../client";

export async function getAdminBookings(params) {
  const { data } = await client.get("/api/v1/admin/bookings", { params });
  return data;
}

export async function overrideBookingStatus(bookingId, payload) {
  const { data } = await client.patch(`/api/v1/admin/bookings/${bookingId}/status`, payload);
  return data;
}

