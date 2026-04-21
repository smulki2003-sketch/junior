import { create } from "zustand";

export const useBookingStore = create((set) => ({
  selectedBookingId: null,
  setSelectedBookingId: (id) => set({ selectedBookingId: id }),
}));

