import { translate } from "./translations";
import { useLanguageStore } from "../store/languageStore";

export function useI18n() {
  const lang = useLanguageStore((state) => state.lang);
  const isRTL = useLanguageStore((state) => state.isRTL);
  const toggleLanguage = useLanguageStore((state) => state.toggleLanguage);
  const setLanguage = useLanguageStore((state) => state.setLanguage);

  return {
    lang,
    isRTL,
    toggleLanguage,
    setLanguage,
    t: (key, fallback) => translate(lang, key, fallback),
  };
}
