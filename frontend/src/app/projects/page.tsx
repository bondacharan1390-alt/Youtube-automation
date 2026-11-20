"use client";

import React, { useEffect, useState } from "react";
import { Search, Plus, Film, Smartphone, Filter } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ProjectCard, ProjectCardData } from "@/components/projects/ProjectCard";
import { useTranslation } from "@/lib/i18n";
import { useStudioStore } from "@/lib/store";
import { fetchApi } from "@/lib/api";

export default function ProjectsPage() {
  const { t } = useTranslation();
  const setCreateModalOpen = useStudioStore((state) => state.setCreateModalOpen);

  const [projects, setProjects] = useState<ProjectCardData[]>([]);
  const [search, setSearch] = useState("");
  const [formatFilter, setFormatFilter] = useState<string>("all");
  const [languageFilter, setLanguageFilter] = useState<string>("all");
  const [isLoading, setIsLoading] = useState(true);

  const loadProjects = async () => {
    try {
      setIsLoading(true);
      const data = await fetchApi<ProjectCardData[]>("/projects");
      setProjects(data);
    } catch (err) {
      console.error("Failed to fetch projects:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm(t.projects.deleteConfirm)) return;
    try {
      await fetchApi(`/projects/${id}`, { method: "DELETE" });
      setProjects((prev) => prev.filter((p) => p.id !== id));
    } catch (err) {
      alert("Failed to delete project");
    }
  };

  const filteredProjects = projects.filter((project) => {
    const matchesSearch =
      project.title.toLowerCase().includes(search.toLowerCase()) ||
      (project.topic && project.topic.toLowerCase().includes(search.toLowerCase()));

    const matchesFormat =
      formatFilter === "all" || project.aspect_ratio === formatFilter;

    const matchesLanguage =
      languageFilter === "all" || project.language === languageFilter;

    return matchesSearch && matchesFormat && matchesLanguage;
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            {t.projects.title}
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            {t.projects.subtitle}
          </p>
        </div>

        <Button
          onClick={() => setCreateModalOpen(true)}
          className="flex items-center space-x-1.5 self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>{t.projects.createNew}</span>
        </Button>
      </div>

      {/* Filter and Search Bar */}
      <Card className="p-4">
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
          {/* Search Input */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder={t.common.search}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-sm rounded-lg bg-slate-50 dark:bg-studio-950/80 border border-slate-200 dark:border-studio-700 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-red-500"
            />
          </div>

          {/* Filters */}
          <div className="flex items-center space-x-2">
            {/* Format Toggle */}
            <div className="flex bg-slate-100 dark:bg-studio-950 p-1 rounded-lg border border-slate-200 dark:border-studio-800 text-xs">
              <button
                onClick={() => setFormatFilter("all")}
                className={`px-3 py-1.5 rounded-md transition-all ${
                  formatFilter === "all"
                    ? "bg-white dark:bg-studio-800 text-slate-900 dark:text-white font-semibold shadow-xs"
                    : "text-slate-500 hover:text-slate-900 dark:hover:text-slate-200"
                }`}
              >
                {t.projects.allFormats}
              </button>
              <button
                onClick={() => setFormatFilter("16:9")}
                className={`px-3 py-1.5 rounded-md flex items-center space-x-1 transition-all ${
                  formatFilter === "16:9"
                    ? "bg-white dark:bg-studio-800 text-red-600 dark:text-red-400 font-semibold shadow-xs"
                    : "text-slate-500 hover:text-slate-900 dark:hover:text-slate-200"
                }`}
              >
                <Film className="w-3.5 h-3.5" />
                <span>16:9</span>
              </button>
              <button
                onClick={() => setFormatFilter("9:16")}
                className={`px-3 py-1.5 rounded-md flex items-center space-x-1 transition-all ${
                  formatFilter === "9:16"
                    ? "bg-white dark:bg-studio-800 text-purple-600 dark:text-purple-400 font-semibold shadow-xs"
                    : "text-slate-500 hover:text-slate-900 dark:hover:text-slate-200"
                }`}
              >
                <Smartphone className="w-3.5 h-3.5" />
                <span>9:16</span>
              </button>
            </div>

            {/* Language Selector */}
            <select
              value={languageFilter}
              onChange={(e) => setLanguageFilter(e.target.value)}
              className="px-3 py-2 text-xs rounded-lg bg-slate-100 dark:bg-studio-950 border border-slate-200 dark:border-studio-800 text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-2 focus:ring-red-500"
            >
              <option value="all">{t.projects.allLanguages}</option>
              <option value="en">English</option>
              <option value="te">తెలుగు (Telugu)</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Projects Grid */}
      {filteredProjects.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredProjects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onDelete={handleDelete}
            />
          ))}
        </div>
      ) : (
        <Card className="text-center py-16">
          <Film className="w-12 h-12 text-slate-300 dark:text-studio-700 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-700 dark:text-slate-300">
            {t.projects.noProjectsFound}
          </h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
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
  );
}
