import { create } from "zustand";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "CUSTOMER" | "ADMIN" | "OBSERVER";
}

interface AuthStore {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
  initAuth: () => void;
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,

  login: (token, user) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("sister_auth_token", token);
      localStorage.setItem("sister_auth_user", JSON.stringify(user));
    }
    set({ token, user, isAuthenticated: true });
  },

  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("sister_auth_token");
      localStorage.removeItem("sister_auth_user");
    }
    set({ token: null, user: null, isAuthenticated: false });
  },

  initAuth: () => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("sister_auth_token");
      const userStr = localStorage.getItem("sister_auth_user");
      if (token && userStr) {
        try {
          const user = JSON.parse(userStr);
          set({ token, user, isAuthenticated: true });
        } catch {
          localStorage.removeItem("sister_auth_token");
          localStorage.removeItem("sister_auth_user");
        }
      }
    }
  },
}));
