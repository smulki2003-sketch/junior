import { useMutation } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { markAllNotificationsRead, markNotificationRead } from "../api/notifications";
import { PageWrapper } from "../components/layout/PageWrapper";
import { NotificationItem } from "../components/shared/NotificationItem";
import { Button } from "../components/ui/Button";
import { ErrorState } from "../components/ui/ErrorState";
import { Skeleton } from "../components/ui/Skeleton";
import { useNotifications } from "../hooks/useNotifications";
import { useAuthStore } from "../store/authStore";
import { useNotificationStore } from "../store/notificationStore";

const tabs = ["All", "Bookings", "Payments", "System", "Recommendations"];

export default function NotificationsPage() {
  const user = useAuthStore((state) => state.user);
  const [tab, setTab] = useState("All");
  const setUnread = useNotificationStore((state) => state.setUnreadCount);
  const query = useNotifications(user?.id);

  const markReadMutation = useMutation({
    mutationFn: (notificationId) => markNotificationRead(notificationId),
    onSuccess: () => query.refetch(),
  });

  const markAllMutation = useMutation({
    mutationFn: () => markAllNotificationsRead(user.id),
    onSuccess: () => query.refetch(),
  });

  const payload = query.data?.results || query.data || [];
  const notifications = Array.isArray(payload) ? payload : [];

  const filtered = useMemo(() => {
    if (tab === "All") return notifications;
    const map = {
      Bookings: "booking",
      Payments: "payment",
      System: "system",
      Recommendations: "recommendation",
    };
    return notifications.filter((item) => item.category === map[tab]);
  }, [notifications, tab]);

  const unreadCount = notifications.filter((item) => !item.is_read).length;
  useEffect(() => {
    setUnread(unreadCount);
  }, [setUnread, unreadCount]);

  return (
    <PageWrapper>
      <div className="mx-auto max-w-[720px] space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="font-display text-4xl font-bold">Notifications</h1>
          {unreadCount > 0 ? (
            <button onClick={() => markAllMutation.mutate()} className="text-sm text-[var(--text-secondary)]">
              Mark all as read
            </button>
          ) : null}
        </div>

        <div className="flex flex-wrap gap-2">
          {tabs.map((item) => (
            <Button key={item} variant={item === tab ? "primary" : "outline"} onClick={() => setTab(item)}>
              {item}
            </Button>
          ))}
        </div>

        {query.isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-24" />
            ))}
          </div>
        ) : query.isError ? (
          <ErrorState message="Unable to load notifications." onRetry={() => query.refetch()} />
        ) : filtered.length === 0 ? (
          <div className="rounded-xl border border-[var(--border-subtle)] bg-surface p-10 text-center">
            <div className="mx-auto mb-3 h-16 w-16 rounded-full bg-elevated" />
            <p className="text-[var(--text-secondary)]">No notifications in this tab.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {filtered.map((item) => (
              <NotificationItem
                key={item.id}
                item={item}
                onMarkRead={(notification) => markReadMutation.mutate(notification.id)}
              />
            ))}
          </div>
        )}
      </div>
    </PageWrapper>
  );
}
