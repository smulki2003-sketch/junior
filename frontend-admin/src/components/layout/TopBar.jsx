import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useI18n } from "../../i18n/useI18n";
import { useUIStore } from "../../store/uiStore";
import { LanguageToggle } from "../ui/LanguageToggle";
import { ThemeToggle } from "../ui/ThemeToggle";

const quickItems = [
  { type: "Users", label: "Users", to: "/admin/users" },
  { type: "Bookings", label: "Bookings", to: "/admin/bookings" },
  { type: "Listings", label: "Housing Queue", to: "/admin/housing" },
  { type: "Reports", label: "Reports", to: "/admin/reports" },
];

function BellIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M15 17h5l-1.4-1.4A2 2 0 0 1 18 14.2V11a6 6 0 1 0-12 0v3.2a2 2 0 0 1-.6 1.4L4 17h5" />
      <path d="M9 17a3 3 0 0 0 6 0" />
    </svg>
  );
}

export function TopBar({ breadcrumb = "Overview / Dashboard", collapsed = false }) {
  const navigate = useNavigate();
  const { commandPaletteOpen, setCommandPaletteOpen } = useUIStore();
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const { t, isRTL } = useI18n();

  useEffect(() => {
    const onKeyDown = (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setCommandPaletteOpen(true);
      }
      if (event.key === "Escape") {
        setCommandPaletteOpen(false);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [setCommandPaletteOpen]);

  const filtered = useMemo(() => {
    if (!query.trim()) return quickItems;
    return quickItems.filter((x) => `${x.type} ${x.label}`.toLowerCase().includes(query.toLowerCase()));
  }, [query]);

  return (
    <>
      <header className="fixed left-0 right-0 top-0 z-20 h-[60px] border-b border-[var(--table-border)] bg-surface/95 px-6 backdrop-blur-sm">
        <div
          className="flex h-full items-center justify-between gap-3 text-data"
          style={isRTL ? { marginRight: collapsed ? 64 : 240 } : { marginLeft: collapsed ? 64 : 240 }}
        >
          <p className="text-[var(--text-secondary)]">{breadcrumb}</p>
          <div className="mx-4 max-w-xl flex-1">
            <button onClick={() => setCommandPaletteOpen(true)} className="w-full rounded-md border border-[var(--border-subtle)] bg-elevated px-3 py-2 text-left text-[var(--text-secondary)]">
              {t("common.searchPlaceholder")} {t("topbar.commandHint")}
            </button>
          </div>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <LanguageToggle />
            <span aria-label={t("topbar.notifications")} className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-[var(--border-subtle)] bg-elevated text-[var(--text-secondary)]">
              <BellIcon />
            </span>
            <span className="rounded-full bg-elevated px-2 py-1">A</span>
          </div>
        </div>
      </header>

      <AnimatePresence>
        {commandPaletteOpen ? (
          <motion.div
            className="fixed inset-0 z-50 flex items-start justify-center bg-black/70 p-8"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setCommandPaletteOpen(false)}
          >
            <motion.div
              className="glass mt-20 w-full max-w-2xl rounded-[10px] border border-[var(--border-subtle)] p-4"
              initial={{ y: -8, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -8, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <input
                autoFocus
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "ArrowDown") setSelectedIndex((i) => Math.min(filtered.length - 1, i + 1));
                  if (e.key === "ArrowUp") setSelectedIndex((i) => Math.max(0, i - 1));
                  if (e.key === "Enter" && filtered[selectedIndex]) {
                    navigate(filtered[selectedIndex].to);
                    setCommandPaletteOpen(false);
                  }
                }}
                className="w-full rounded-md border border-[var(--border-subtle)] bg-elevated px-3 py-2"
                placeholder={t("common.searchPlaceholder")}
              />
              <div className="mt-3 space-y-2">
                {filtered.map((item, index) => (
                  <button
                    key={`${item.type}-${item.to}`}
                    onClick={() => {
                      navigate(item.to);
                      setCommandPaletteOpen(false);
                    }}
                    className={`flex w-full items-center justify-between rounded-md px-3 py-2 text-left ${
                      index === selectedIndex ? "bg-hover" : "bg-surface"
                    }`}
                  >
                    <span>{item.label}</span>
                    <span className="text-xs text-[var(--text-secondary)]">{item.type}</span>
                  </button>
                ))}
              </div>
            </motion.div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </>
  );
}
