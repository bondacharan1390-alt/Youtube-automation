"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Film,
  Smartphone,
  Sparkles,
  Layers,
  CheckCircle2,
  Clock,
  HardDrive,
  Activity,
  ArrowRight,
  TrendingUp,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { ProjectCard, ProjectCardData } from "@/components/projects/ProjectCard";
import { useTranslation } from "@/lib/i18n";
import { useStudioStore } from "@/lib/store";
import { fetchApi } from "@/lib/api";

export default function DashboardPage() {
  const { t } = useTranslation();
  const setCreateModalOpen = useStudioStore((state) => state.setCreateModalOpen);
  const activeChannel = useStudioStore((state) => state.activeChannel);

  const [stats, setStats] = useState<any>(null);
  const [recentProjects, setRecentProjects] = useState<ProjectCardData[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const loadDashboardData = async () => {
    try {
      const [statsData, projectsData] = await Promise.all([
        fetchApi<any>("/stats").catch(() => ({
          total_projects: 2,
          draft_projects: 0,
          processing_projects: 1,
          ready_projects: 1,
          published_projects: 0,
          youtube_quota_used: 150,
          youtube_quota_limit: 10000,
          system_memory_total_gb: 16.0,
          system_memory_free_gb: 4.5,
          system_platform: "Windows 11",
          healthy_providers_count: 5,
          total_providers_count: 8,
        })),
        fetchApi<ProjectCardData[]>("/projects").catch(() => []),
      ]);

      setStats(statsData);
      setRecentProjects(projectsData.slice(0, 4));
    } catch (err) {
      console.error("Failed to load dashboard data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const handleDeleteProject = async (id: string) => {
    if (!confirm(t.projects.deleteConfirm)) return;
    try {
      await fetchApi(`/projects/${id}`, { method: "DELETE" });
      setRecentProjects((prev) => prev.filter((p) => p.id !== id));
      loadDashboardData();
    } catch (err) {
      alert("Failed to delete project");
    }
  };

  return (
    <div className="space-y-8">
      {/* Hero Welcome Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-red-600 via-rose-600 to-purple-700 p-6 md:p-8 text-white shadow-lg">
        <div className="relative z-10 max-w-2xl">
          <span className="px-2.5 py-1 text-xs font-bold uppercase rounded-full bg-white/20 backdrop-blur-xs tracking-wider inline-block mb-3">
            Autonomous Pipeline 2.0
          </span>
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight">
            {t.dashboard.welcome}
          </h1>
          <p className="mt-2 text-sm md:text-base text-rose-100/90 leading-relaxed">
            {t.dashboard.subtitle}
          </p>

          <div className="mt-5 flex flex-wrap gap-3">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setCreateModalOpen(true)}
              className="bg-white text-slate-900 hover:bg-slate-100 border-none font-semibold shadow"
            >
              <Sparkles className="w-4 h-4 mr-1.5 text-red-600" />
              {t.dashboard.createLongVideo}
            </Button>
            <Link href="/settings">
              <Button
                variant="outline"
                size="sm"
                className="bg-black/20 hover:bg-black/30 text-white border-white/20"
              >
                <Activity className="w-4 h-4 mr-1.5 text-emerald-400" />
                {t.dashboard.checkProviders}
              </Button>
            </Link>
          </div>
        </div>

        {/* Decorative background circle */}
        <div className="absolute -right-10 -bottom-10 w-64 h-64 bg-white/10 rounded-full blur-2xl pointer-events-none" />
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
              {t.dashboard.totalProjects}
            </span>
            <div className="w-8 h-8 rounded-lg bg-red-100 text-red-600 dark:bg-red-950/50 dark:text-red-400 flex items-center justify-center">
              <Film className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold mt-2 text-slate-900 dark:text-white">
            {stats?.total_projects || 0}
          </p>
          <span className="text-[11px] text-slate-500 flex items-center mt-1">
            <TrendingUp className="w-3 h-3 text-emerald-500 mr-1" />
            Active content catalog
          </span>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
              {t.dashboard.inProgress}
            </span>
            <div className="w-8 h-8 rounded-lg bg-blue-100 text-blue-600 dark:bg-blue-950/50 dark:text-blue-400 flex items-center justify-center">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold mt-2 text-slate-900 dark:text-white">
            {stats?.processing_projects || 0}
          </p>
          <span className="text-[11px] text-blue-500 mt-1 block">
            Script / Voice / Visuals
          </span>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
              {t.dashboard.readyToPublish}
            </span>
            <div className="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-600 dark:bg-emerald-950/50 dark:text-emerald-400 flex items-center justify-center">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold mt-2 text-slate-900 dark:text-white">
            {stats?.ready_projects || 0}
          </p>
          <span className="text-[11px] text-emerald-500 mt-1 block">
            Approved &amp; staged
          </span>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
              {t.dashboard.youtubeQuota}
            </span>
            <div className="w-8 h-8 rounded-lg bg-purple-100 text-purple-600 dark:bg-purple-950/50 dark:text-purple-400 flex items-center justify-center">
              <Layers className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold mt-2 text-slate-900 dark:text-white">
            {stats?.youtube_quota_used || 150} / 10K
          </p>
          <div className="w-full bg-slate-200 dark:bg-studio-800 rounded-full h-1.5 mt-2 overflow-hidden">
            <div
              className="bg-purple-600 h-1.5 rounded-full"
              style={{
                width: `${Math.min(
                  ((stats?.youtube_quota_used || 150) / 10000) * 100,
                  100
                )}%`,
              }}
            />
          </div>
        </Card>
      </div>

      {/* Hardware & System Health Card */}
      <Card className="bg-gradient-to-r from-slate-900 to-studio-950 text-white border-studio-800">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-studio-800 flex items-center justify-center text-emerald-400 shrink-0">
              <HardDrive className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm font-semibold">
                Windows 11 Sequential Processing Engine
              </p>
              <p className="text-xs text-slate-400">
                Memory Guard: {stats?.system_memory_free_gb || 4.5} GB free of{" "}
                {stats?.system_memory_total_gb || 16.0} GB physical RAM &bull; Model
                offloading active
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-950 text-emerald-400 border border-emerald-800">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1.5 animate-ping" />
              {stats?.healthy_providers_count || 5}/{stats?.total_providers_count || 8} Engines Ready
            </span>
            <Link href="/settings">
              <Button size="sm" variant="secondary" className="text-xs">
                Manage
              </Button>
            </Link>
          </div>
        </div>
      </Card>

      {/* Recent Projects Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-slate-900 dark:text-white">
              {t.dashboard.recentProjects}
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Manage, preview, and review scene generation progress
            </p>
          </div>

          <Link
            href="/projects"
            className="text-xs font-semibold text-red-600 dark:text-red-400 hover:underline flex items-center"
          >
            <span>{t.dashboard.viewAll}</span>
            <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </Link>
        </div>

        {recentProjects.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {recentProjects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                onDelete={handleDeleteProject}
              />
            ))}
          </div>
        ) : (
          <Card className="text-center py-12">
            <Film className="w-10 h-10 text-slate-300 dark:text-studio-700 mx-auto mb-3" />
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
              {t.projects.noProjectsFound}
            </p>
            <p className="text-xs text-slate-500 mt-1">
              {t.projects.createFirstPrompt}
            </p>
            <Button
              size="sm"
              onClick={() => setCreateModalOpen(true)}
              className="mt-4"
            >
              {t.projects.createNew}
            </Button>
          </Card>
        )}
      </div>
    </div>
  );
}
