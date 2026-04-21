import { create } from "zustand";
import { isAdminRole } from "../utils/permissions";

export const useAdminAuthStore = create((set) => ({
  user: null,
  token: localStorage.getItem("access_token") || "",
  role: localStorage.getItem("admin_role") || "",
  isAuthenticated: Boolean(localStorage.getItem("access_token")),
  login: ({ user, accessToken, role }) => {
    localStorage.setItem("access_token", accessToken || "");
    localStorage.setItem("admin_role", role || "");
    set({
      user,
      token: accessToken || "",
      role: role || "",
      isAuthenticated: Boolean(accessToken) && isAdminRole(role),
    });
  },
  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("admin_role");
    set({ user: null, token: "", role: "", isAuthenticated: false });
  },
}));

