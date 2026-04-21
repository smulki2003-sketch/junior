import { AnimatePresence, motion } from "framer-motion";
import { useEffect } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { applyAutoLanguage } from "./i18n/autoTranslate";
import { useI18n } from "./i18n/useI18n";
import { applyLanguageToDocument, useLanguageStore } from "./store/languageStore";
import { applyThemeToDocument, useThemeStore } from "./store/themeStore";
import { ProtectedAdminRoute } from "./components/layout/ProtectedAdminRoute";
import { pageSlide } from "./animations/variants";
import AdminBookingsPage from "./pages/admin/AdminBookingsPage";
import AdminBookingDetailPage from "./pages/admin/AdminBookingDetailPage";
import AdminComplaintsPage from "./pages/admin/AdminComplaintsPage";
import AdminComplaintDetailPage from "./pages/admin/AdminComplaintDetailPage";
import AdminDashboardPage from "./pages/admin/AdminDashboardPage";
import AdminHousingPage from "./pages/admin/AdminHousingPage";
import AdminHousingDetailPage from "./pages/admin/AdminHousingDetailPage";
import AdminLoginPage from "./pages/admin/AdminLoginPage";
import AdminNotificationsPage from "./pages/admin/AdminNotificationsPage";
import AdminPaymentsPage from "./pages/admin/AdminPaymentsPage";
import AdminQuestionnairesPage from "./pages/admin/AdminQuestionnairesPage";
import AdminReportsPage from "./pages/admin/AdminReportsPage";
import AdminUserDetailPage from "./pages/admin/AdminUserDetailPage";
import AdminUsersPage from "./pages/admin/AdminUsersPage";

function PageMotion({ children }) {
  return (
    <motion.div initial={pageSlide.initial} animate={pageSlide.animate} exit={pageSlide.exit}>
      {children}
    </motion.div>
  );
}

export default function App() {
  const location = useLocation();
  const theme = useThemeStore((state) => state.theme);
  const lang = useLanguageStore((state) => state.lang);
  const { isRTL } = useI18n();

  useEffect(() => {
    applyThemeToDocument(theme);
  }, [theme]);

  useEffect(() => {
    applyLanguageToDocument(lang);
  }, [lang]);

  useEffect(() => {
    const cleanup = applyAutoLanguage(lang);
    return cleanup;
  }, [lang, location.pathname]);

  return (
    <motion.div
      key={lang}
      initial={{ opacity: 0.96, filter: "blur(6px)" }}
      animate={{ opacity: 1, filter: "blur(0px)" }}
      transition={{ duration: 0.24 }}
      dir={isRTL ? "rtl" : "ltr"}
    >
      <AnimatePresence mode="wait">
        <Routes key={location.pathname} location={location}>
          <Route path="/" element={<Navigate to="/admin/login" replace />} />
          <Route path="/admin/login" element={<PageMotion><AdminLoginPage /></PageMotion>} />
          <Route path="/admin/dashboard" element={<ProtectedAdminRoute><PageMotion><AdminDashboardPage /></PageMotion></ProtectedAdminRoute>} />
          <Route path="/admin/users" element={<ProtectedAdminRoute><PageMotion><AdminUsersPage /></PageMotion></ProtectedAdminRoute>} />
          <Route path="/admin/users/:id" element={<ProtectedAdminRoute><PageMotion><AdminUserDetailPage /></PageMotion></ProtectedAdminRoute>} />
          <Route path="/admin/housing" element={<ProtectedAdminRoute><PageMotion><AdminHousingPage /></PageMotion></ProtectedAdminRoute>} />
          <Route path="/admin/housing/:id" element={<ProtectedAdminRoute><PageMotion><AdminHousingDetailPage /></PageMotion></ProtectedAdminRoute>} />
          <Route path="/admin/bookings" element={<ProtectedAdminRoute><PageMotion><AdminBookingsPage /></PageMotion></ProtectedAdminRoute>} />
          <Route path="/admin/bookings/:id" element={<ProtectedAdminRoute><PageMotion><AdminBookingDetailPage /></PageMotion></ProtectedAdminRoute>} />
          <Route path="/admin/payments" element={<ProtectedAdminRoute><PageMotion><AdminPaymentsPage /></PageMotion></ProtectedAdminRoute>} />
          <Route path="/admin/complaints" element={<ProtectedAdminRoute><PageMotion><AdminComplaintsPage /></PageMotion></ProtectedAdminRoute>} />
          <Route path="/admin/complaints/:id" element={<ProtectedAdminRoute><PageMotion><AdminComplaintDetailPage /></PageMotion></ProtectedAdminRoute>} />
          <Route path="/admin/reports" element={<ProtectedAdminRoute><PageMotion><AdminReportsPage /></PageMotion></ProtectedAdminRoute>} />
          <Route path="/admin/notifications" element={<ProtectedAdminRoute><PageMotion><AdminNotificationsPage /></PageMotion></ProtectedAdminRoute>} />
          <Route path="/admin/questionnaires" element={<ProtectedAdminRoute><PageMotion><AdminQuestionnairesPage /></PageMotion></ProtectedAdminRoute>} />
        </Routes>
      </AnimatePresence>
    </motion.div>
  );
}
