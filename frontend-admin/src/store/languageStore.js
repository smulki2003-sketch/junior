import { create } from "zustand";
import { persist } from "zustand/middleware";

export function applyLanguageToDocument(lang) {
  if (typeof document === "undefined") return;
  const isRTL = lang === "ar";
  document.documentElement.setAttribute("lang", lang);
  document.documentElement.setAttribute("dir", isRTL ? "rtl" : "ltr");
}

export const useLanguageStore = create()(
  persist(
    (set, get) => ({
      lang: "en",
      isRTL: false,
      setLanguage: (lang) => {
        const isRTL = lang === "ar";
        set({ lang, isRTL });
        applyLanguageToDocument(lang);
      },
      toggleLanguage: () => {
        const nextLang = get().lang === "en" ? "ar" : "en";
        const isRTL = nextLang === "ar";
        set({ lang: nextLang, isRTL });
        applyLanguageToDocument(nextLang);
      },
    }),
    { name: "nestu-admin-language" }
  )
);
