import { useMutation } from "@tanstack/react-query";
import { loginRequest, registerRequest } from "../api/auth";
import { useAuthStore } from "../store/authStore";

export function useAuth() {
  const auth = useAuthStore();

  const loginMutation = useMutation({
    mutationFn: loginRequest,
    onSuccess: (data) => {
      auth.login({
        user: data.user,
        accessToken: data.tokens?.access_token || "",
        refreshToken: data.tokens?.refresh_token || "",
      });
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

