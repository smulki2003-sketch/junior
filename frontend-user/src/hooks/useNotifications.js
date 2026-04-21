import { useQuery } from "@tanstack/react-query";
import { getNotifications } from "../api/notifications";

export function useNotifications(userId) {
  return useQuery({
    queryKey: ["notifications", userId],
    queryFn: () => getNotifications(userId),
    enabled: Boolean(userId),
  });
}

