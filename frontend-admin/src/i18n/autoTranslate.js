const originals = new WeakMap();

const arMap = {
  Dashboard: "لوحة التحكم",
  Users: "المستخدمون",
  Housing: "السكن",
  Bookings: "الحجوزات",
  Payments: "المدفوعات",
  Complaints: "الشكاوى",
  Reports: "التقارير",
  Notifications: "الإشعارات",
  Questionnaires: "الاستبيانات",
  Overview: "نظرة عامة",
  Management: "الإدارة",
  Moderation: "المراجعة",
  Analytics: "التحليلات",
  Comms: "الاتصالات",
  "Search users, bookings, IDs...": "ابحث عن المستخدمين أو الحجوزات أو المعرّفات...",
  "Admin Dashboard": "لوحة تحكم الإدارة",
  "Refresh Data": "تحديث البيانات",
  "Last updated:": "آخر تحديث:",
  "Bookings Over Time": "الحجوزات عبر الوقت",
  "Listing Status Breakdown": "توزيع حالة العقارات",
  "Recent Activity": "النشاط الأخير",
  "No recent activity found.": "لا يوجد نشاط حديث.",
  "Approve Listing": "موافقة على العقار",
  "Reject Listing": "رفض العقار",
  "Decision Panel": "لوحة القرار",
  "Status Timeline": "تسلسل الحالة",
  "Status Change": "تغيير الحالة",
  Apply: "تطبيق",
  "Resolve Case": "حل القضية",
  Escalate: "تصعيد",
  "Close without action": "إغلاق دون إجراء",
  "Invalid booking id.": "معرّف الحجز غير صالح.",
  "Invalid listing id.": "معرّف العقار غير صالح.",
  "Invalid user id.": "معرّف المستخدم غير صالح.",
  Logout: "تسجيل الخروج",
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
