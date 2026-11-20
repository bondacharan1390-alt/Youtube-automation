import { create } from "zustand";

export interface User {
  id: string;
  email: string;
  full_name?: string;
  is_superuser: boolean;
}

export interface Channel {
  id: string;
  channel_name: string;
  youtube_channel_id?: string;
  thumbnail_url?: string;
  quota_units_used_today: number;
}

export interface StudioState {
  // Theme & Language
  theme: "dark" | "light";
  language: "en" | "te";
  setTheme: (theme: "dark" | "light") => void;
  toggleTheme: () => void;
  setLanguage: (lang: "en" | "te") => void;

  // Responsive Navigation
  isSidebarCollapsed: boolean;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebar: () => void;
  isMobileDrawerOpen: boolean;
  setMobileDrawerOpen: (open: boolean) => void;

  // Auth
  token: string | null;
  user: User | null;
  activeChannel: Channel | null;
  setAuth: (token: string, user: User) => void;
  setActiveChannel: (channel: Channel | null) => void;
  logout: () => void;

  // Modals
  isCreateModalOpen: boolean;
  setCreateModalOpen: (open: boolean) => void;
}

export const useStudioStore = create<StudioState>((set) => ({
  theme: "dark",
  language: "en",
  setTheme: (theme) => {
    if (typeof window !== "undefined") {
      document.documentElement.classList.toggle("dark", theme === "dark");
      localStorage.setItem("studio_theme", theme);
    }
    set({ theme });
  },
  toggleTheme: () =>
    set((state) => {
      const newTheme = state.theme === "dark" ? "light" : "dark";
      if (typeof window !== "undefined") {
        document.documentElement.classList.toggle("dark", newTheme === "dark");
        localStorage.setItem("studio_theme", newTheme);
      }
      return { theme: newTheme };
    }),
  setLanguage: (language) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("studio_language", language);
    }
    set({ language });
  },

  isSidebarCollapsed: false,
  setSidebarCollapsed: (isSidebarCollapsed) => set({ isSidebarCollapsed }),
  toggleSidebar: () => set((state) => ({ isSidebarCollapsed: !state.isSidebarCollapsed })),
  isMobileDrawerOpen: false,
  setMobileDrawerOpen: (isMobileDrawerOpen) => set({ isMobileDrawerOpen }),

  token: null,
  user: null,
  activeChannel: {
    id: "default-channel-1",
    channel_name: "AI Cinema Telugu & Global",
    quota_units_used_today: 150,
  },
  setAuth: (token, user) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("studio_token", token);
    }
    set({ token, user });
  },
  setActiveChannel: (activeChannel) => set({ activeChannel }),
  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("studio_token");
    }
    set({ token: null, user: null });
  },

  isCreateModalOpen: false,
  setCreateModalOpen: (isCreateModalOpen) => set({ isCreateModalOpen }),
}));
