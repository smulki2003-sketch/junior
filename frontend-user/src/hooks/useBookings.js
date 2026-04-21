import { useQuery } from "@tanstack/react-query";
import { getUserBookings } from "../api/bookings";

export function useBookings(userId) {
  return useQuery({
    queryKey: ["bookings", userId],
    queryFn: () => getUserBookings(userId),
    enabled: Boolean(userId),
  });
}

