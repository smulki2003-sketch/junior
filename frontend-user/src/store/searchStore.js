import { create } from "zustand";

export const useSearchStore = create((set) => ({
  query: "",
  filters: {
    unit_type: "",
    min_price: 0,
    max_price: 5000,
    min_stars: 1,
    min_workers: 1,
    amenities: [],
    location: "",
    is_available: true,
  },
  mode: "list",
  setQuery: (query) => set({ query }),
  setMode: (mode) => set({ mode }),
  updateFilters: (nextFilters) =>
    set((state) => ({ filters: { ...state.filters, ...nextFilters } })),
  resetFilters: () =>
    set({
      filters: {
        unit_type: "",
        min_price: 0,
        max_price: 5000,
        min_stars: 1,
        min_workers: 1,
        amenities: [],
        location: "",
        is_available: true,
      },
    }),
}));
