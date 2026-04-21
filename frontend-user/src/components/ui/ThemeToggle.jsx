import { motion } from "framer-motion";
import { useI18n } from "../../i18n/useI18n";
import { useThemeStore } from "../../store/themeStore";

export function ThemeToggle() {
  const theme = useThemeStore((state) => state.theme);
  const toggleTheme = useThemeStore((state) => state.toggleTheme);
  const { t } = useI18n();
  const isDark = theme === "dark";

  return (
    <motion.button
      type="button"
      whileTap={{ scale: 0.95 }}
      onClick={toggleTheme}
      className="relative h-8 w-16 rounded-full border border-[var(--border-subtle)] bg-elevated p-1"
      aria-label={`${t("common.theme")}: ${isDark ? t("common.dark") : t("common.light")}`}
      title={`${t("common.theme")}: ${isDark ? t("common.dark") : t("common.light")}`}
    >
      <motion.span
        animate={{ x: isDark ? 0 : 32 }}
        transition={{ type: "spring", stiffness: 460, damping: 30 }}
        className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-[var(--accent-primary)] text-xs text-white"
      >
        {isDark ? "🌙" : "☀️"}
      </motion.span>
    </motion.button>
  );
}
