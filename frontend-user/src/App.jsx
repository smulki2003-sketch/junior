import { AnimatePresence, motion } from "framer-motion";
import { useEffect } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { getMeRequest } from "./api/auth";
import { applyAutoLanguage } from "./i18n/autoTranslate";
import { useI18n } from "./i18n/useI18n";
import { Footer } from "./components/layout/Footer";
import { Navbar } from "./components/layout/Navbar";
import { ProtectedRoute } from "./components/layout/ProtectedRoute";
import { useAuthStore } from "./store/authStore";
import { applyLanguageToDocument, useLanguageStore } from "./store/languageStore";
import { applyThemeToDocument, useThemeStore } from "./store/themeStore";
import BookingTimelinePage from "./pages/BookingTimelinePage";
import BookingsPage from "./pages/BookingsPage";
import HousingDetailPage from "./pages/HousingDetailPage";
import HousingPage from "./pages/HousingPage";
import LoginPage from "./pages/LoginPage";
import NotificationsPage from "./pages/NotificationsPage";
import ComplaintsPage from "./pages/ComplaintsPage";
import ProfilePage from "./pages/ProfilePage";
import RecommendationsPage from "./pages/RecommendationsPage";
import RegisterPage from "./pages/RegisterPage";
import RoommatesPage from "./pages/RoommatesPage";

export default function App() {
  const location = useLocation();
  const user = useAuthStore((state) => state.user);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const hydrateUser = useAuthStore((state) => state.hydrateUser);
  const logout = useAuthStore((state) => state.logout);
  const isAuthPage = ["/login", "/register"].includes(location.pathname);
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

  useEffect(() => {
    let isActive = true;
    if (!isAuthenticated) return () => {};

    getMeRequest()
      .then((me) => {
        if (!isActive) return;
        hydrateUser(me);
      })
      .catch(() => {
        if (!isActive) return;
        logout();
      });

    return () => {
      isActive = false;
    };
  }, [isAuthenticated, hydrateUser, logout]);

  return (
    <motion.div
      key={lang}
      initial={{ opacity: 0.96, filter: "blur(6px)" }}
      animate={{ opacity: 1, filter: "blur(0px)" }}
      transition={{ duration: 0.24 }}
      className="min-h-screen bg-base text-[var(--text-primary)]"
      dir={isRTL ? "rtl" : "ltr"}
    >
      {!isAuthPage ? <Navbar /> : null}
      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          <Route path="/" element={<Navigate to={isAuthenticated ? "/housing" : "/login"} replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/housing"
            element={
              <ProtectedRoute>
                <HousingPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/housing/:id"
            element={
              <ProtectedRoute>
                <HousingDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/bookings"
            element={
              <ProtectedRoute>
                <BookingsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/bookings/:id"
            element={
              <ProtectedRoute>
                <BookingTimelinePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/recommendations"
            element={
              <ProtectedRoute>
                <RecommendationsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/roommates"
            element={
              <ProtectedRoute>
                <RoommatesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/notifications"
            element={
              <ProtectedRoute>
                <NotificationsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/complaints"
            element={
              <ProtectedRoute>
                <ComplaintsPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </AnimatePresence>
      {!isAuthPage ? <Footer /> : null}
    </motion.div>
  );
}
