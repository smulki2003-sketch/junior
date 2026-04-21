import { create } from "zustand";

const USER_STORAGE_KEY = "auth_user";

function parseStoredUser() {
  const raw = localStorage.getItem(USER_STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function normalizeUser(user) {
  if (!user || typeof user !== "object") return null;
  const resolvedId = user.id ?? user.user_id ?? null;
  return {
    ...user,
    id: resolvedId,
  };
}

export const useAuthStore = create((set) => ({
  user: normalizeUser(parseStoredUser()),
  token: localStorage.getItem("access_token") || "",
  refreshToken: localStorage.getItem("refresh_token") || "",
  isAuthenticated: Boolean(localStorage.getItem("access_token")),
  login: ({ user, accessToken, refreshToken }) => {
    const normalizedUser = normalizeUser(user);
    localStorage.setItem("access_token", accessToken);
    if (refreshToken) localStorage.setItem("refresh_token", refreshToken);
    if (normalizedUser) {
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(normalizedUser));
    }
    set({
      user: normalizedUser,
      token: accessToken,
      refreshToken: refreshToken || "",
      isAuthenticated: true,
    });
  },
  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem(USER_STORAGE_KEY);
    set({ user: null, token: "", refreshToken: "", isAuthenticated: false });
  },
  hydrateUser: (user) => {
    const normalizedUser = normalizeUser(user);
    if (normalizedUser) {
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(normalizedUser));
    } else {
      localStorage.removeItem(USER_STORAGE_KEY);
    }
    set((state) => ({ ...state, user: normalizedUser }));
  },
}));
