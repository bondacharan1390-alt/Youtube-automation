"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Film,
  PlusCircle,
  Settings,
  X,
  Search,
  FileText,
  Mic,
  Image as ImageIcon,
  Video,
  BarChart3,
  Youtube,
} from "lucide-react";
import { useStudioStore } from "@/lib/store";
import { useTranslation } from "@/lib/i18n";
import { cn } from "@/lib/utils";

export const MobileNav: React.FC = () => {
  const pathname = usePathname();
  const { t } = useTranslation();
  const isDrawerOpen = useStudioStore((state) => state.isMobileDrawerOpen);
  const setDrawerOpen = useStudioStore((state) => state.setMobileDrawerOpen);
  const setCreateModalOpen = useStudioStore((state) => state.setCreateModalOpen);

  const bottomNavItems = [
    { href: "/", label: t.nav.dashboard, icon: LayoutDashboard },
    { href: "/projects", label: t.nav.projects, icon: Film },
    {
      action: () => setCreateModalOpen(true),
      label: t.common.create,
      icon: PlusCircle,
      isSpecial: true,
    },
    { href: "/settings", label: t.nav.settings, icon: Settings },
  ];

  const fullDrawerItems = [
    { href: "/", label: t.nav.dashboard, icon: LayoutDashboard },
    { href: "/projects", label: t.nav.projects, icon: Film },
    { href: "/research", label: t.nav.researchStudio, icon: Search },
    { href: "/scripts", label: t.nav.scriptStudio, icon: FileText },
    { href: "/voice", label: t.nav.voiceStudio, icon: Mic },
    { href: "/images", label: t.nav.imageStudio, icon: ImageIcon },
    { href: "/editor", label: t.nav.videoEditor, icon: Video },
    { href: "/analytics", label: t.nav.analytics, icon: BarChart3 },
    { href: "/settings", label: t.nav.settings, icon: Settings },
  ];

  return (
    <>
      {/* Fixed Bottom Navigation for Mobile (< 768px) */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 h-16 bg-white/95 dark:bg-studio-950/95 backdrop-blur-lg border-t border-slate-200 dark:border-studio-800 z-40 flex items-center justify-around px-2">
        {bottomNavItems.map((item, idx) => {
          const Icon = item.icon;
          if (item.action) {
            return (
              <button
                key={idx}
                onClick={item.action}
                className="flex flex-col items-center justify-center p-1 text-red-600"
              >
                <div className="w-10 h-10 -mt-5 rounded-full bg-red-600 text-white flex items-center justify-center shadow-lg shadow-red-600/30">
                  <Icon className="w-6 h-6" />
                </div>
                <span className="text-[10px] font-semibold mt-1">
                  {item.label}
                </span>
              </button>
            );
          }

          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href!}
              className={cn(
                "flex flex-col items-center justify-center p-1.5 transition-colors",
                isActive
                  ? "text-red-600 dark:text-red-400 font-semibold"
                  : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
              )}
            >
              <Icon className="w-5 h-5" />
              <span className="text-[10px] mt-0.5">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Slide-out Drawer for All Studio Modules on Mobile */}
      {isDrawerOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-slate-950/70 backdrop-blur-xs"
            onClick={() => setDrawerOpen(false)}
          />

          {/* Drawer Body */}
          <div className="relative w-72 max-w-[80vw] bg-white dark:bg-studio-950 h-full shadow-2xl flex flex-col z-10 border-r border-slate-200 dark:border-studio-800">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-studio-800">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 rounded-lg bg-red-600 text-white flex items-center justify-center">
                  <Youtube className="w-5 h-5" />
                </div>
                <span className="font-bold text-sm text-slate-900 dark:text-white">
                  AI YOUTUBE
                </span>
              </div>
              <button
                onClick={() => setDrawerOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Links */}
            <div className="flex-1 overflow-y-auto p-3 space-y-1">
              {fullDrawerItems.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setDrawerOpen(false)}
                    className={cn(
                      "flex items-center space-x-3 px-3 py-2.5 rounded-xl text-sm transition-colors",
                      isActive
                        ? "bg-red-50 text-red-600 dark:bg-red-950/40 dark:text-red-400 font-semibold"
                        : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-studio-900"
                    )}
                  >
                    <Icon className="w-5 h-5" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </>
  );
};
