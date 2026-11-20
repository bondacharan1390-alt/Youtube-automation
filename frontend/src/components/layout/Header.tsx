"use client";

import React from "react";
import {
  Menu,
  Plus,
  User as UserIcon,
} from "lucide-react";
import { useStudioStore } from "@/lib/store";
import { useTranslation } from "@/lib/i18n";
import { Button } from "@/components/ui/Button";
import Link from "next/link";

export const Header: React.FC = () => {
  const { t, language, setLanguage } = useTranslation();
  const theme = useStudioStore((state) => state.theme);
  const toggleTheme = useStudioStore((state) => state.toggleTheme);
  const setMobileDrawerOpen = useStudioStore((state) => state.setMobileDrawerOpen);
  const setCreateModalOpen = useStudioStore((state) => state.setCreateModalOpen);
  const user = useStudioStore((state) => state.user);

  return (
    <header className="h-16 px-4 md:px-6 border-b border-slate-200 dark:border-studio-800/80 bg-white/80 dark:bg-studio-950/80 backdrop-blur-md sticky top-0 z-20 flex items-center justify-between">
      {/* Mobile Menu Button */}
      <div className="flex items-center space-x-3 md:hidden">
        <button
          onClick={() => setMobileDrawerOpen(true)}
          className="p-2 rounded-xl text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-studio-900"
        >
          <Menu className="w-6 h-6" />
        </button>
        <span className="font-bold text-sm tracking-tight text-red-600">
          AI YOUTUBE
        </span>
      </div>

      {/* Left Title / Badge */}
      <div className="hidden md:flex items-center space-x-3">
        <span className="text-xs font-semibold uppercase px-2 py-1 rounded bg-slate-100 dark:bg-studio-900 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-studio-800">
          Windows 11 &bull; 8GB Optimized
        </span>
      </div>

      {/* Right Controls: New Project, Language, Theme, User */}
      <div className="flex items-center space-x-3">
        {/* Create Project Button */}
        <Button
          size="sm"
          onClick={() => setCreateModalOpen(true)}
          className="shadow-sm shadow-red-600/30 flex items-center space-x-1.5"
        >
          <Plus className="w-4 h-4" />
          <span className="hidden sm:inline">{t.projects.createNew}</span>
        </Button>

        {/* Bilingual Language Switcher */}
        <div className="flex items-center bg-slate-100 dark:bg-studio-900 rounded-lg p-1 border border-slate-200 dark:border-studio-800 text-xs font-medium">
          <button
            onClick={() => setLanguage("en")}
            className={`px-2 py-1 rounded-md transition-all ${
              language === "en"
                ? "bg-white dark:bg-studio-800 text-slate-900 dark:text-white shadow-xs font-bold"
                : "text-slate-500 hover:text-slate-900 dark:hover:text-slate-200"
            }`}
          >
            EN
          </button>
          <button
            onClick={() => setLanguage("te")}
            className={`px-2 py-1 rounded-md transition-all ${
              language === "te"
                ? "bg-white dark:bg-studio-800 text-red-600 dark:text-red-400 shadow-xs font-bold"
                : "text-slate-500 hover:text-slate-900 dark:hover:text-slate-200"
            }`}
          >
            తెలుగు
          </button>
        </div>

        {/* Theme Toggle Button */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg bg-slate-100 dark:bg-studio-900 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-studio-800 hover:bg-slate-200 dark:hover:bg-studio-800 transition-colors"
          title={`Switch to ${theme === "dark" ? "Light" : "Dark"} mode`}
        >
          {theme === "dark" ? (
            <svg
              className="w-4 h-4 text-amber-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 3v1m0 16v1m9-9h-1M4 9H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
              />
            </svg>
          ) : (
            <svg
              className="w-4 h-4 text-slate-700"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
              />
            </svg>
          )}
        </button>

        {/* User Account / Login Link */}
        <Link
          href="/login"
          className="p-1.5 rounded-full bg-slate-100 dark:bg-studio-900 text-slate-600 dark:text-slate-300 hover:ring-2 hover:ring-red-500 transition-all flex items-center justify-center border border-slate-200 dark:border-studio-800"
          title={user?.email || "Account & Login"}
        >
          <UserIcon className="w-4 h-4" />
        </Link>
      </div>
    </header>
  );
};
