import { motion } from "framer-motion";
import { Link, useLocation } from "react-router-dom";
import { useI18n } from "../../i18n/useI18n";
import { useAdminAuthStore } from "../../store/adminAuthStore";
import { useUIStore } from "../../store/uiStore";
import { Button } from "../ui/Button";

function Icon({ children }) {
  return (
    <span className="inline-flex h-5 w-5 items-center justify-center text-[var(--text-secondary)]">
      <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        {children}
      </svg>
    </span>
  );
}

const icons = {
  dashboard: <Icon><path d="M3 13h8V3H3z" /><path d="M13 21h8v-6h-8z" /><path d="M13 11h8V3h-8z" /><path d="M3 21h8v-4H3z" /></Icon>,
  users: <Icon><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="3" /><path d="M22 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a3 3 0 0 1 0 5.74" /></Icon>,
  housing: <Icon><path d="m3 11 9-8 9 8" /><path d="M5 10v10h14V10" /></Icon>,
  bookings: <Icon><rect x="3" y="4" width="18" height="18" rx="2" /><path d="M16 2v4" /><path d="M8 2v4" /><path d="M3 10h18" /></Icon>,
  payments: <Icon><rect x="2" y="5" width="20" height="14" rx="2" /><path d="M2 10h20" /><path d="M6 15h2" /></Icon>,
  complaints: <Icon><path d="M10.3 3.4a2 2 0 0 1 3.4 0l6.2 10.7A2 2 0 0 1 18.2 17H5.8a2 2 0 0 1-1.7-2.9z" /><path d="M12 9v3" /><path d="M12 15h.01" /></Icon>,
  questionnaires: <Icon><circle cx="12" cy="12" r="10" /><path d="M9.1 9a3 3 0 1 1 5.8 1c-.8.7-1.4 1.2-1.4 2" /><path d="M12 17h.01" /></Icon>,
  reports: <Icon><path d="M3 3v18h18" /><path d="m8 14 3-3 2 2 4-4" /></Icon>,
  notifications: <Icon><path d="M15 17h5l-1.4-1.4A2 2 0 0 1 18 14.2V11a6 6 0 1 0-12 0v3.2a2 2 0 0 1-.6 1.4L4 17h5" /><path d="M9 17a3 3 0 0 0 6 0" /></Icon>,
};

export function Sidebar({ complaintCount = 0 }) {
  const location = useLocation();
  const { sidebarCollapsed, toggleSidebar } = useUIStore();
  const { user, logout } = useAdminAuthStore();
  const { t, isRTL } = useI18n();

  const sections = [
    {
      title: t("sidebar.overview"),
      items: [{ to: "/admin/dashboard", icon: icons.dashboard, label: t("sidebar.dashboard") }],
    },
    {
      title: t("sidebar.management"),
      items: [
        { to: "/admin/users", icon: icons.users, label: t("sidebar.users") },
        { to: "/admin/housing", icon: icons.housing, label: t("sidebar.housing") },
        { to: "/admin/bookings", icon: icons.bookings, label: t("sidebar.bookings") },
        { to: "/admin/payments", icon: icons.payments, label: t("sidebar.payments") },
      ],
    },
    {
      title: t("sidebar.moderation"),
      items: [
        { to: "/admin/complaints", icon: icons.complaints, label: t("sidebar.complaints"), badgeKey: "complaints" },
        { to: "/admin/questionnaires", icon: icons.questionnaires, label: t("sidebar.questionnaires") },
      ],
    },
    {
      title: t("sidebar.analytics"),
      items: [{ to: "/admin/reports", icon: icons.reports, label: t("sidebar.reports") }],
    },
    {
      title: t("sidebar.comms"),
      items: [{ to: "/admin/notifications", icon: icons.notifications, label: t("sidebar.notifications") }],
    },
  ];

  return (
    <motion.aside
      animate={{ width: sidebarCollapsed ? 64 : 240 }}
      className={`fixed top-0 z-30 h-screen bg-surface ${isRTL ? "right-0 border-l border-[var(--table-border)]" : "left-0 border-r border-[var(--table-border)]"}`}
      transition={{ duration: 0.22 }}
    >
      <div className="flex h-full flex-col">
        <div className="h-[60px] border-b border-[var(--table-border)] px-3">
          <div className="flex h-full items-center gap-2">
            <span className="inline-flex h-5 w-5 items-center justify-center rounded bg-blue/20 text-[10px] text-blue">N</span>
            {!sidebarCollapsed ? <span className="font-display text-sm font-semibold text-blue">NestU Admin</span> : null}
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto px-2 py-3 text-data">
          {sections.map((section) => (
            <div key={section.title} className="mb-4">
              {!sidebarCollapsed ? <p className="mb-1 px-2 text-[10px] font-semibold text-[var(--text-secondary)]">{section.title}</p> : null}
              <div className="space-y-1">
                {section.items.map((item) => {
                  const active = location.pathname.startsWith(item.to);
                  const badge = item.badgeKey === "complaints" ? complaintCount : null;
                  return (
                    <Link
                      key={item.to}
                      to={item.to}
                      title={sidebarCollapsed ? item.label : ""}
                      className={`sidebar-link ${active ? "active" : ""} flex items-center justify-between rounded-md px-2 py-2 text-[var(--text-secondary)]`}
                    >
                      <span className="inline-flex items-center gap-2">
                        <span className="inline-flex h-5 min-w-5 items-center justify-center rounded bg-elevated px-1">{item.icon}</span>
                        {!sidebarCollapsed ? <span>{item.label}</span> : null}
                      </span>
                      {!sidebarCollapsed && badge ? <span className="rounded-full bg-amber/20 px-2 py-[2px] text-[10px] text-amber">{badge}</span> : null}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        <div className="border-t border-[var(--table-border)] p-2">
          {!sidebarCollapsed ? (
            <div className="mb-2 rounded-md bg-elevated p-2 text-xs">
              <p className="font-medium">{user?.email || "admin@nestu.com"}</p>
              <button onClick={logout} className="text-[var(--text-secondary)]">{t("sidebar.logout")}</button>
            </div>
          ) : null}
          <Button variant="ghost" className="w-full" onClick={toggleSidebar}>
            {sidebarCollapsed ? (isRTL ? "<" : ">") : (isRTL ? ">" : "<")}
          </Button>
        </div>
      </div>
    </motion.aside>
  );
}
