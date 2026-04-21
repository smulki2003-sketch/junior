import client from "./client";

export const getNotifications = async (userId) => {
  const { data } = await client.get(`/api/v1/notifications/users/${userId}`);
  return data;
};

export const markNotificationRead = async (notificationId) => {
  const { data } = await client.patch(`/api/v1/notifications/${notificationId}/read`);
  return data;
};

export const markAllNotificationsRead = async (userId) => {
  const { data } = await client.patch(`/api/v1/notifications/users/${userId}/read-all`);
  return data;
};

