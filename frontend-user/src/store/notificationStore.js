import { create } from "zustand";

export const useNotificationStore = create((set) => ({
  unreadCount: 0,
  setUnreadCount: (unreadCount) => set({ unreadCount }),
}));

