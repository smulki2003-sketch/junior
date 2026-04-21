import { useMutation } from "@tanstack/react-query";
import { adminLogin } from "../api/auth";
import { useAdminAuthStore } from "../store/adminAuthStore";

export function useAdminAuth() {
  const auth = useAdminAuthStore();
  const loginMutation = useMutation({
    mutationFn: adminLogin,
    onSuccess: (data) => {
      const roles = data.user?.roles || [];
      const role = roles.includes("superadmin") ? "superadmin" : roles.includes("admin") ? "admin" : roles[0] || "";
      localStorage.setItem("admin_user_id", String(data.user?.id || ""));
      auth.login({
        user: data.user,
        accessToken: data.tokens?.access_token || "",
        role,
      });
    },
  });

  return { ...auth, loginMutation };
}

