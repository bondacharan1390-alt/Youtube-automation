"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Film,
  Sparkles,
  FileText,
  Mic,
  Image as ImageIcon,
  Subtitles,
  Video,
  Palette,
  Search,
  Radio,
  UploadCloud,
  BarChart3,
  Settings,
  History,
  ChevronLeft,
  ChevronRight,
  Youtube,
  Workflow,
} from "lucide-react";
import { useStudioStore } from "@/lib/store";
import { useTranslation } from "@/lib/i18n";
import { cn } from "@/lib/utils";

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const { t } = useTranslation();
  const isCollapsed = useStudioStore((state) => state.isSidebarCollapsed);
  const toggleSidebar = useStudioStore((state) => state.toggleSidebar);
  const activeChannel = useStudioStore((state) => state.activeChannel);

  const navItems = [
    { href: "/", label: t.nav.dashboard, icon: LayoutDashboard },
    { href: "/automation", label: "Automation", icon: Workflow },
    { href: "/projects", label: t.nav.projects, icon: Film, badge: "Active" },
    { href: "/research", label: t.nav.researchStudio, icon: Search },
    { href: "/scripts", label: t.nav.scriptStudio, icon: FileText },
    { href: "/voice", label: t.nav.voiceStudio, icon: Mic },
    { href: "/images", label: t.nav.imageStudio, icon: ImageIcon },
    { href: "/subtitles", label: t.nav.subtitleStudio, icon: Subtitles },
    { href: "/editor", label: t.nav.videoEditor, icon: Video },
    { href: "/thumbnails", label: t.nav.thumbnailStudio, icon: Palette },
    { href: "/seo", label: t.nav.seoStudio, icon: Sparkles },
    { href: "/channels", label: t.nav.channelManager, icon: Radio },
    { href: "/upload", label: t.nav.uploadScheduling, icon: UploadCloud },
    { href: "/analytics", label: t.nav.analytics, icon: BarChart3 },
    { href: "/settings", label: t.nav.settings, icon: Settings },
    { href: "/logs", label: t.nav.historyLogs, icon: History },
  ];

  return (
    <aside
      className={cn(
        "hidden md:flex flex-col border-r border-slate-200 dark:border-studio-800/80 bg-white dark:bg-studio-950 transition-all duration-300 select-none z-30 shrink-0",
        isCollapsed ? "w-20" : "w-64"
      )}
    >
      {/* Brand Header */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-slate-200 dark:border-studio-800/80">
        <Link href="/" className="flex items-center space-x-3 overflow-hidden">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-red-600 to-rose-500 flex items-center justify-center text-white shadow-md shadow-red-500/20 shrink-0">
            <Youtube className="w-6 h-6" />
          </div>
          {!isCollapsed && (
            <div className="flex flex-col">
              <span className="font-bold text-sm tracking-tight text-slate-900 dark:text-white leading-tight">
                AI YOUTUBE
              </span>
              <span className="text-[10px] font-semibold text-red-600 uppercase tracking-widest">
                Studio Suite
              </span>
            </div>
          )}
        </Link>
        <button
          onClick={toggleSidebar}
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-studio-800/80 transition-colors"
          title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
        >
          {isCollapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <ChevronLeft className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center space-x-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all group",
                isActive
                  ? "bg-red-50 text-red-600 dark:bg-red-950/30 dark:text-red-400 font-semibold"
                  : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-studio-900 hover:text-slate-900 dark:hover:text-slate-200"
              )}
              title={isCollapsed ? item.label : undefined}
            >
              <Icon
                className={cn(
                  "w-5 h-5 shrink-0 transition-colors",
                  isActive
                    ? "text-red-600 dark:text-red-400"
                    : "text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-300"
                )}
              />
              {!isCollapsed && (
                <span className="truncate flex-1">{item.label}</span>
              )}
              {!isCollapsed && item.badge && (
                <span className="px-1.5 py-0.5 text-[10px] font-bold uppercase rounded bg-slate-200 dark:bg-studio-800 text-slate-700 dark:text-slate-300">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </div>

      {/* Active Channel Badge (Bottom) */}
      {!isCollapsed && activeChannel && (
        <div className="p-4 border-t border-slate-200 dark:border-studio-800/80">
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-studio-900/60 border border-slate-200/80 dark:border-studio-800 flex items-center space-x-3">
            <div className="w-8 h-8 rounded-full bg-red-600/10 text-red-600 flex items-center justify-center font-bold text-xs shrink-0">
              YT
            </div>
            <div className="overflow-hidden flex-1">
              <p className="text-xs font-semibold text-slate-900 dark:text-slate-200 truncate">
                {activeChannel.channel_name}
              </p>
              <div className="flex items-center space-x-1.5 mt-0.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-[10px] text-slate-500 dark:text-slate-400">
                  {activeChannel.quota_units_used_today} / 10,000 Quota
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
};
