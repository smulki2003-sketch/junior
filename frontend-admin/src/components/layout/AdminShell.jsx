import { motion } from "framer-motion";
import { useMemo } from "react";
import { useI18n } from "../../i18n/useI18n";
import { useUIStore } from "../../store/uiStore";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

export function AdminShell({ children, breadcrumb, complaintCount = 0 }) {
  const sidebarCollapsed = useUIStore((state) => state.sidebarCollapsed);
  const layoutWidth = useMemo(() => (sidebarCollapsed ? 64 : 240), [sidebarCollapsed]);
  const { isRTL } = useI18n();

  return (
    <div className="admin-shell">
      <Sidebar complaintCount={complaintCount} />
      <TopBar breadcrumb={breadcrumb} collapsed={sidebarCollapsed} />
      <motion.main
        animate={isRTL ? { marginRight: layoutWidth, width: `calc(100vw - ${layoutWidth}px)` } : { marginLeft: layoutWidth, width: `calc(100vw - ${layoutWidth}px)` }}
        transition={{ duration: 0.22 }}
        className="pt-[60px]"
      >
        <div className="min-h-[calc(100vh-60px)] overflow-x-auto p-6 md:p-8">{children}</div>
      </motion.main>
    </div>
  );
}
