import { useI18n } from "../../i18n/useI18n";

export function Footer() {
  const { t } = useI18n();

  return (
    <footer className="border-t border-[var(--border-subtle)] bg-surface/80">
      <div className="mx-auto flex h-16 w-full max-w-[1280px] items-center justify-between px-6 text-sm text-[var(--text-secondary)]">
        <span className="font-display font-semibold text-[var(--text-primary)]">NestU</span>
        <div className="flex gap-6">
          <a href="/housing">{t("nav.housing")}</a>
          <a href="/bookings">{t("nav.bookings")}</a>
          <a href="/profile">Profile</a>
        </div>
        <div className="hidden gap-3 md:flex" aria-hidden="true">
          <span>*</span>
          <span>*</span>
          <span>*</span>
        </div>
      </div>
    </footer>
  );
}
