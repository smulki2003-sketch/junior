import { useMutation } from "@tanstack/react-query";
import { exportReports } from "../api/admin/reports";

export function useExport() {
  return useMutation({
    mutationFn: exportReports,
  });
}

