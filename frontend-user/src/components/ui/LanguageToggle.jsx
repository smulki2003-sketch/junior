import { motion } from "framer-motion";
import { useI18n } from "../../i18n/useI18n";

export function LanguageToggle() {
  const { lang, toggleLanguage, t } = useI18n();
  const isArabic = lang === "ar";

  return (
    <motion.button
      type="button"
      whileTap={{ scale: 0.95 }}
      onClick={toggleLanguage}
      className="rounded-lg border border-[var(--border-subtle)] bg-elevated px-2.5 py-1.5 text-xs font-semibold"
      aria-label={`${t("common.language")}: ${isArabic ? t("common.arabic") : t("common.english")}`}
      title={`${t("common.language")}: ${isArabic ? t("common.arabic") : t("common.english")}`}
    >
      {isArabic ? "AR" : "EN"}
    </motion.button>
  );
}
