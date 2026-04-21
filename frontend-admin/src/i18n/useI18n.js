import { useLanguageStore } from "../store/languageStore";
import { translate } from "./translations";

export function useI18n() {
  const lang = useLanguageStore((state) => state.lang);
  const isRTL = useLanguageStore((state) => state.isRTL);
  const setLanguage = useLanguageStore((state) => state.setLanguage);
  const toggleLanguage = useLanguageStore((state) => state.toggleLanguage);

  return {
    lang,
    isRTL,
    setLanguage,
    toggleLanguage,
    t: (key, fallback) => translate(lang, key, fallback),
  };
}
