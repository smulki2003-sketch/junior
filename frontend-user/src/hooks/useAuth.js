import { useMutation } from "@tanstack/react-query";
import { getMeRequest, loginRequest, registerRequest } from "../api/auth";
import { useAuthStore } from "../store/authStore";

export function useAuth() {
  const auth = useAuthStore();

  const loginMutation = useMutation({
    mutationFn: loginRequest,
    onSuccess: async (data) => {
      auth.login({
        user: data.user,
        accessToken: data.tokens?.access_token || "",
        refreshToken: data.tokens?.refresh_token || "",
      });
      try {
        const me = await getMeRequest();
        auth.hydrateUser(me);
      } catch {
        // no-op: token remains valid, fallback is existing user payload.
      }
    },
  });

  const registerMutation = useMutation({
    mutationFn: registerRequest,
  });

  return {
    ...auth,
    loginMutation,
    registerMutation,
  };
}
