const originals = new WeakMap();

const arMap = {
  Housing: "السكن",
  Bookings: "الحجوزات",
  Recommendations: "التوصيات",
  Roommates: "زملاء الغرفة",
  Notifications: "الإشعارات",
  Profile: "الملف الشخصي",
  Logout: "تسجيل الخروج",
  "Sign In": "تسجيل الدخول",
  Filters: "الفلاتر",
  "Apply Filters": "تطبيق الفلاتر",
  Reset: "إعادة ضبط",
  "Map": "الخريطة",
  "List": "قائمة",
  "View Details": "عرض التفاصيل",
  "Book Now": "احجز الآن",
  "Add to Favorites": "أضف إلى المفضلة",
  "No listings found for the current filters.": "لا توجد نتائج للفلاتر الحالية.",
  "Unable to load listings.": "تعذّر تحميل العقارات.",
  "About this space": "عن هذا السكن",
  "Show less": "عرض أقل",
  "Show more": "عرض المزيد",
  "Location Preview": "معاينة الموقع",
  Reviews: "التقييمات",
  "Payment Summary": "ملخص الدفع",
  Rent: "الإيجار",
  Total: "الإجمالي",
  "Download Receipt": "تنزيل الإيصال",
  "Cancel Booking": "إلغاء الحجز",
  "Contact Support": "تواصل مع الدعم",
  "Invalid listing id.": "معرّف السكن غير صالح.",
  "Invalid booking id.": "معرّف الحجز غير صالح.",
  "Unable to load booking timeline.": "تعذّر تحميل تسلسل الحجز.",
  "Near campus": "قريب من الجامعة",
  "City Center": "وسط المدينة",
  Guests: "الضيوف",
  "View all photos": "عرض كل الصور",
  Photos: "الصور",
  "Why matched?": "لماذا هذا الترشيح؟",
  Popular: "شائع",
  New: "جديد",
  "Search by location, university, or keyword...": "ابحث بالموقع أو الجامعة أو كلمة مفتاحية...",
};

function translateTextNode(node, map) {
  const value = node.nodeValue;
  if (!value) return;
  if (!originals.has(node)) originals.set(node, value);
  const trimmed = value.trim();
  if (!trimmed) return;
  const translated = map[trimmed];
  if (!translated) return;
  const prefix = value.slice(0, value.indexOf(trimmed));
  const suffix = value.slice(value.indexOf(trimmed) + trimmed.length);
  node.nodeValue = `${prefix}${translated}${suffix}`;
}

function restoreTextNode(node) {
  if (originals.has(node)) node.nodeValue = originals.get(node);
}

function walkTextNodes(root, callback) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let node = walker.nextNode();
  while (node) {
    callback(node);
    node = walker.nextNode();
  }
}

export function applyAutoLanguage(lang) {
  if (typeof document === "undefined") return () => {};
  const root = document.body;

  const applyNow = () => {
    if (lang === "ar") walkTextNodes(root, (node) => translateTextNode(node, arMap));
    else walkTextNodes(root, restoreTextNode);
  };

  applyNow();
  const observer = new MutationObserver(() => applyNow());
  observer.observe(root, { childList: true, subtree: true });
  return () => observer.disconnect();
}
