export const translations = {
  en: {
    common: {
      theme: "Theme",
      language: "Language",
      dark: "Dark",
      light: "Light",
      english: "English",
      arabic: "Arabic",
      searchPlaceholder: "Search users, bookings, IDs...",
    },
    topbar: {
      notifications: "Notifications",
      commandHint: "(Ctrl+K)",
    },
    sidebar: {
      overview: "Overview",
      management: "Management",
      moderation: "Moderation",
      analytics: "Analytics",
      comms: "Comms",
      dashboard: "Dashboard",
      users: "Users",
      housing: "Housing",
      bookings: "Bookings",
      payments: "Payments",
      complaints: "Complaints",
      questionnaires: "Questionnaires",
      reports: "Reports",
      notifications: "Notifications",
      logout: "Logout",
    },
  },
  ar: {
    common: {
      theme: "المظهر",
      language: "اللغة",
      dark: "داكن",
      light: "فاتح",
      english: "English",
      arabic: "العربية",
      searchPlaceholder: "ابحث عن المستخدمين أو الحجوزات أو المعرّفات...",
    },
    topbar: {
      notifications: "الإشعارات",
      commandHint: "(Ctrl+K)",
    },
    sidebar: {
      overview: "نظرة عامة",
      management: "الإدارة",
      moderation: "المراجعة",
      analytics: "التحليلات",
      comms: "الاتصالات",
      dashboard: "لوحة التحكم",
      users: "المستخدمون",
      housing: "السكن",
      bookings: "الحجوزات",
      payments: "المدفوعات",
      complaints: "الشكاوى",
      questionnaires: "الاستبيانات",
      reports: "التقارير",
      notifications: "الإشعارات",
      logout: "تسجيل الخروج",
    },
  },
};

export function translate(lang, key, fallback = "") {
  const keys = key.split(".");
  let current = translations[lang] || translations.en;
  for (const segment of keys) {
    current = current?.[segment];
    if (current == null) return fallback || key;
  }
  return typeof current === "string" ? current : fallback || key;
}
