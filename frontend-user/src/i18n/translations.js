export const translations = {
  en: {
    common: {
      language: "Language",
      theme: "Theme",
      light: "Light",
      dark: "Dark",
      english: "English",
      arabic: "Arabic",
    },
    nav: {
      housing: "Housing",
      bookings: "Bookings",
      recommendations: "Recommendations",
      roommates: "Roommates",
      notifications: "Notifications",
      signIn: "Sign In",
      logout: "Logout",
      openMenu: "Open menu",
      closeMenu: "Close menu",
    },
    footer: {
      rights: "All rights reserved.",
      student: "Student Housing Platform",
    },
  },
  ar: {
    common: {
      language: "اللغة",
      theme: "المظهر",
      light: "فاتح",
      dark: "داكن",
      english: "English",
      arabic: "العربية",
    },
    nav: {
      housing: "السكن",
      bookings: "الحجوزات",
      recommendations: "التوصيات",
      roommates: "زملاء الغرفة",
      notifications: "الإشعارات",
      signIn: "تسجيل الدخول",
      logout: "تسجيل الخروج",
      openMenu: "فتح القائمة",
      closeMenu: "إغلاق القائمة",
    },
    footer: {
      rights: "جميع الحقوق محفوظة.",
      student: "منصة سكن الطلاب",
    },
  },
};

export function translate(lang, key, fallback = "") {
  const keys = key.split(".");
  let current = translations[lang] || translations.en;
  for (const segment of keys) {
    current = current?.[segment];
    if (current == null) {
      return fallback || key;
    }
  }
  return typeof current === "string" ? current : fallback || key;
}
