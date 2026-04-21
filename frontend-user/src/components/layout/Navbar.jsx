import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useI18n } from "../../i18n/useI18n";
import { useAuthStore } from "../../store/authStore";
import { useNotificationStore } from "../../store/notificationStore";
import { LanguageToggle } from "../ui/LanguageToggle";
import { Button } from "../ui/Button";
import { ThemeToggle } from "../ui/ThemeToggle";

function BellIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M15 17h5l-1.4-1.4A2 2 0 0 1 18 14.2V11a6 6 0 1 0-12 0v3.2a2 2 0 0 1-.6 1.4L4 17h5" />
      <path d="M9 17a3 3 0 0 0 6 0" />
    </svg>
  );
}

function MenuIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <path d="M4 7h16" />
      <path d="M4 12h16" />
      <path d="M4 17h16" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <path d="M6 6l12 12" />
      <path d="M18 6 6 18" />
    </svg>
  );
}

export function Navbar() {
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const unreadCount = useNotificationStore((state) => state.unreadCount);
  const { user, isAuthenticated, logout } = useAuthStore();
  const { t, isRTL } = useI18n();

  const links = [
    { to: "/housing", label: t("nav.housing") },
    { to: "/bookings", label: t("nav.bookings") },
    { to: "/recommendations", label: t("nav.recommendations") },
    { to: "/roommates", label: t("nav.roommates") },
    { to: "/complaints", label: "Complaints" },
  ];

  return (
    <>
      <motion.nav
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass fixed inset-x-0 top-0 z-40 h-[68px] border-b border-[var(--border-subtle)]"
      >
        <div className="mx-auto flex h-full w-full max-w-[1280px] items-center justify-between px-6">
          <Link
            to="/housing"
            className="font-display text-2xl font-bold text-primary"
            style={{ textShadow: "0 0 20px rgba(108,99,255,0.5)" }}
          >
            NestU
          </Link>

          <div className="relative hidden items-center gap-8 md:flex">
            {links.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className="relative py-1 text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              >
                {item.label}
                {location.pathname.startsWith(item.to) ? (
                  <motion.div
                    layoutId="underline"
                    className="absolute -bottom-1 left-0 h-[2px] w-full rounded-full bg-primary"
                  />
                ) : null}
              </Link>
            ))}
          </div>

          <div className="flex items-center gap-3">
            <ThemeToggle />
            <LanguageToggle />
            <Link to="/notifications" className="relative inline-flex h-8 w-8 items-center justify-center rounded-full border border-[var(--border-subtle)] text-[var(--text-secondary)]" aria-label={t("nav.notifications")}>
              <BellIcon />
              {unreadCount > 0 ? (
                <span className={`absolute top-0 inline-flex h-2 w-2 rounded-full bg-coral ${isRTL ? "left-0" : "right-0"}`} />
              ) : null}
            </Link>
            {isAuthenticated ? (
              <div className="hidden items-center gap-2 md:flex">
                <Link to="/profile" className="rounded-full bg-elevated px-3 py-1 text-sm">
                  {(user?.email || "User").slice(0, 2).toUpperCase()}
                </Link>
                <Button variant="ghost" onClick={logout}>
                  {t("nav.logout")}
                </Button>
              </div>
            ) : (
              <Link to="/login" className="hidden text-sm text-[var(--text-secondary)] md:inline">
                {t("nav.signIn")}
              </Link>
            )}
            <button className="md:hidden inline-flex h-8 w-8 items-center justify-center rounded border border-[var(--border-subtle)]" onClick={() => setOpen(true)} aria-label={t("nav.openMenu")}>
              <MenuIcon />
            </button>
          </div>
        </div>
      </motion.nav>

      <AnimatePresence>
        {open ? (
          <motion.div
            className="fixed inset-0 z-50 bg-black/50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setOpen(false)}
          >
            <motion.aside
              className={`glass absolute top-0 h-full w-[280px] p-6 ${isRTL ? "left-0 border-r border-[var(--border-subtle)]" : "right-0 border-l border-[var(--border-subtle)]"}`}
              initial={{ x: isRTL ? -300 : 300 }}
              animate={{ x: 0 }}
              exit={{ x: isRTL ? -300 : 300 }}
              onClick={(event) => event.stopPropagation()}
            >
              <button onClick={() => setOpen(false)} className="mb-6 inline-flex h-8 w-8 items-center justify-center rounded border border-[var(--border-subtle)]" aria-label={t("nav.closeMenu")}>
                <CloseIcon />
              </button>
              <div className="flex flex-col gap-4">
                {links.map((item) => (
                  <Link key={item.to} to={item.to} onClick={() => setOpen(false)} className="text-lg">
                    {item.label}
                  </Link>
                ))}
              </div>
            </motion.aside>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </>
  );
}
