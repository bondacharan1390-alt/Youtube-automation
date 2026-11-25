"use client";

import React, { useState, useEffect } from "react";
import {
  Palette,
  Download,
  Sparkles,
  CheckCircle2,
  Loader2,
  Sliders,
  Image as ImageIcon,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useTranslation } from "@/lib/i18n";
import { fetchApi, getMediaUrl } from "@/lib/api";

interface ProjectItem {
  id: string;
  title: string;
  language: string;
  aspect_ratio: string;
}

interface ThumbnailTheme {
  id: string;
  name: string;
  description: string;
  accent_color: string;
}

interface ThumbnailData {
  project_id: string;
  thumbnail_url: string;
  width: number;
  height: number;
  aspect_ratio: string;
  theme: string;
  file_size_bytes: number;
}

export default function ThumbnailStudioPage() {
  const { t } = useTranslation();
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [themes, setThemes] = useState<ThumbnailTheme[]>([]);
  const [selectedTheme, setSelectedTheme] = useState("viral_punch");
  const [headline, setHeadline] = useState("");
  const [subtitle, setSubtitle] = useState("");
  const [badgeText, setBadgeText] = useState("NEW");
  const [thumbnailData, setThumbnailData] = useState<ThumbnailData | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState("");
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    fetchApi("/projects/")
      .then((d: unknown) => {
        const arr = Array.isArray(d) ? d : (d as Record<string, unknown>).items || [];
        setProjects(arr as ProjectItem[]);
      })
      .catch(() => {});

    fetchApi("/thumbnails/themes")
      .then((d: unknown) => {
        if (Array.isArray(d)) setThemes(d as ThumbnailTheme[]);
      })
      .catch(() => {});
  }, []);

  const handleProjectSelect = (projId: string) => {
    setSelectedProjectId(projId);
    setThumbnailData(null);
    const p = projects.find((x) => x.id === projId);
    if (p) {
      setHeadline(p.title);
      setBadgeText(p.language === "te" ? "రహస్యం" : "2026 AI");
      fetchApi(`/thumbnails/${projId}`)
        .then((res: unknown) => setThumbnailData(res as ThumbnailData))
        .catch(() => {});
    }
  };

  const handleGenerate = async () => {
    if (!selectedProjectId) return;
    setIsGenerating(true);
    setError("");
    try {
      const res = (await fetchApi("/thumbnails/generate", {
        method: "POST",
        body: JSON.stringify({
          project_id: selectedProjectId,
          headline,
          subtitle: subtitle || undefined,
          badge_text: badgeText || undefined,
          theme_name: selectedTheme,
        }),
      })) as ThumbnailData;
      setThumbnailData(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to generate thumbnail";
      setError(msg);
    } finally {
      setIsGenerating(false);
    }
  };

  const selectedProj = projects.find((p) => p.id === selectedProjectId);
  const isPortrait = selectedProj?.aspect_ratio === "9:16";

  return (
    <div className="p-4 md:p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <Palette className="w-6 h-6 text-rose-500" />
          {t.thumbnailStudio.title}
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {t.thumbnailStudio.subtitle}
        </p>
      </div>

      {/* Control Card */}
      <Card className="p-5 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
              {t.thumbnailStudio.selectProject}
            </label>
            <select
              value={selectedProjectId}
              onChange={(e) => handleProjectSelect(e.target.value)}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-3 py-2 text-sm focus:ring-2 focus:ring-rose-500 outline-none"
            >
              <option value="">— {t.thumbnailStudio.selectProject} —</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.title} [{p.aspect_ratio}]
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
              {t.thumbnailStudio.theme}
            </label>
            <select
              value={selectedTheme}
              onChange={(e) => setSelectedTheme(e.target.value)}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-3 py-2 text-sm focus:ring-2 focus:ring-rose-500 outline-none"
            >
              {themes.map((th) => (
                <option key={th.id} value={th.id}>
                  {th.name} — {th.description}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          <div className="md:col-span-2">
            <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
              {t.thumbnailStudio.headline}
            </label>
            <input
              type="text"
              value={headline}
              onChange={(e) => setHeadline(e.target.value)}
              placeholder="Bold Catchy Headline..."
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-3 py-2 text-sm outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
              {t.thumbnailStudio.badgeText}
            </label>
            <input
              type="text"
              value={badgeText}
              onChange={(e) => setBadgeText(e.target.value)}
              placeholder="e.g. 2026 / NEW"
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-3 py-2 text-sm outline-none"
            />
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <Button
            variant="primary"
            disabled={!selectedProjectId || !headline || isGenerating}
            onClick={handleGenerate}
            className="flex items-center gap-2"
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                {t.thumbnailStudio.generateThumbnail}
              </>
            )}
          </Button>
        </div>
      </Card>

      {error && (
        <Card className="p-4 border-red-300 bg-red-50 dark:bg-red-950/20 text-red-600 text-sm">
          {error}
        </Card>
      )}

      {/* Preview Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card className="p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-2 text-sm">
                <ImageIcon className="w-4 h-4 text-rose-500" />
                {t.thumbnailStudio.thumbnailPreview}
              </h3>
              {thumbnailData && (
                <Badge variant="success">
                  {thumbnailData.width}x{thumbnailData.height} ·{" "}
                  {(thumbnailData.file_size_bytes / 1024).toFixed(1)} KB
                </Badge>
              )}
            </div>

            {thumbnailData ? (
              <div
                className={`overflow-hidden rounded-xl bg-black border border-gray-700 mx-auto flex items-center justify-center ${
                  isPortrait ? "max-w-xs aspect-[9/16]" : "w-full aspect-[16/9]"
                }`}
              >
                <img
                  src={getMediaUrl(thumbnailData.thumbnail_url)}
                  alt="Generated YouTube Thumbnail"
                  className="w-full h-full object-cover"
                />
              </div>
            ) : (
              <div className="aspect-[16/9] w-full rounded-xl bg-slate-100 dark:bg-slate-900 border-2 border-dashed border-gray-300 dark:border-gray-700 flex flex-col items-center justify-center p-6 text-center">
                <ImageIcon className="w-12 h-12 text-gray-400 mb-2" />
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {t.thumbnailStudio.noThumbnailYet}
                </p>
              </div>
            )}
          </Card>
        </div>

        {/* Details & Download Side Panel */}
        <div>
          <Card className="p-5 space-y-4">
            <h3 className="font-semibold text-gray-800 dark:text-gray-200 text-sm flex items-center gap-2">
              <Sliders className="w-4 h-4 text-rose-500" />
              Thumbnail Info
            </h3>

            {thumbnailData ? (
              <div className="space-y-3 text-sm">
                <div className="flex justify-between py-1 border-b border-gray-200 dark:border-gray-800 text-gray-600 dark:text-gray-400">
                  <span>Format:</span>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    PNG (Lossless 4K-Ready)
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-gray-200 dark:border-gray-800 text-gray-600 dark:text-gray-400">
                  <span>Dimensions:</span>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {thumbnailData.width} × {thumbnailData.height}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-gray-200 dark:border-gray-800 text-gray-600 dark:text-gray-400">
                  <span>Aspect Ratio:</span>
                  <span className="font-semibold text-gray-900 dark:text-white">
                    {thumbnailData.aspect_ratio}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-gray-200 dark:border-gray-800 text-gray-600 dark:text-gray-400">
                  <span>Active Theme:</span>
                  <span className="font-semibold text-gray-900 dark:text-white capitalize">
                    {thumbnailData.theme.replace("_", " ")}
                  </span>
                </div>

                <div className="pt-3">
                  <a
                    href={`${API_BASE}/thumbnails/download/${thumbnailData.project_id}`}
                    download
                    className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-rose-600 hover:bg-rose-700 text-white font-medium text-sm transition-colors shadow-md"
                  >
                    <Download className="w-4 h-4" />
                    {t.thumbnailStudio.downloadThumbnail}
                  </a>
                </div>
              </div>
            ) : (
              <p className="text-xs text-gray-500 py-6 text-center">
                Select a project and click Generate to see thumbnail metrics and download options.
              </p>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
