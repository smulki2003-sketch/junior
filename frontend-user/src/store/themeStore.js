import { create } from "zustand";
import { persist } from "zustand/middleware";

export function applyThemeToDocument(theme) {
  if (typeof document === "undefined") return;
  document.documentElement.setAttribute("data-theme", theme);
}

export const useThemeStore = create()(
  persist(
    (set, get) => ({
      theme: "dark",
      setTheme: (theme) => {
        set({ theme });
        applyThemeToDocument(theme);
      },
      toggleTheme: () => {
        const nextTheme = get().theme === "dark" ? "light" : "dark";
        set({ theme: nextTheme });
        applyThemeToDocument(nextTheme);
      },
    }),
    { name: "nestu-user-theme" }
  )
);
