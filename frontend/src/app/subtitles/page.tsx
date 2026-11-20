"use client";

import React, { useState, useEffect } from "react";
import {
  Download,
  Sparkles,
  CheckCircle2,
  Loader2,
  FileText,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useTranslation } from "@/lib/i18n";
import { fetchApi } from "@/lib/api";

interface ProjectItem {
  id: string;
  title: string;
  language: string;
  status: string;
}

interface SubtitleResult {
  project_id: string;
  srt_url: string;
  vtt_url: string;
  cue_count: number;
  message: string;
}

export default function SubtitlesPage() {
  const { t } = useTranslation();
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [result, setResult] = useState<SubtitleResult | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState("");
  const [fontSize, setFontSize] = useState(20);
  const [position, setPosition] = useState("bottom");
  const [bgOpacity, setBgOpacity] = useState(0.6);
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    fetchApi("/projects/")
      .then((d: unknown) => {
        const arr = Array.isArray(d) ? d : (d as Record<string, unknown>).items || [];
        setProjects(arr as ProjectItem[]);
      })
      .catch(() => {});
  }, []);

  const handleGenerate = async () => {
    if (!selectedProjectId) return;
    setIsGenerating(true);
    setResult(null);
    setError("");
    try {
      const data = await fetchApi(
        `/subtitles/generate/${selectedProjectId}`,
        { method: "POST" }
      );
      setResult(data as SubtitleResult);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to generate subtitles";
      setError(msg);
    } finally {
      setIsGenerating(false);
    }
  };

  const selectedProject = projects.find((p) => p.id === selectedProjectId);

  return (
    <div className="p-4 md:p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <FileText className="w-6 h-6 text-blue-500" />
          {t.subtitleStudio.title}
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {t.subtitleStudio.subtitle}
        </p>
      </div>

      {/* Controls */}
      <Card className="p-4 space-y-4">
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap">
            {t.subtitleStudio.selectProject}
          </label>
          <select
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            className="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
          >
            <option value="">
              — {t.subtitleStudio.selectProject} —
            </option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.title} [{p.language === "te" ? "తెలుగు" : "English"}]
              </option>
            ))}
          </select>
          <Button
            variant="primary"
            disabled={!selectedProjectId || isGenerating}
            onClick={handleGenerate}
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-2" />
                {t.subtitleStudio.generateSubtitles}
              </>
            )}
          </Button>
        </div>

        {/* Style Options */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2 border-t border-gray-200 dark:border-gray-700">
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
              {t.subtitleStudio.fontSize}: {fontSize}px
            </label>
            <input
              type="range"
              min={14}
              max={36}
              value={fontSize}
              onChange={(e) => setFontSize(parseInt(e.target.value))}
              className="w-full accent-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
              {t.subtitleStudio.position}
            </label>
            <select
              value={position}
              onChange={(e) => setPosition(e.target.value)}
              className="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm px-2 py-1 text-gray-900 dark:text-white"
            >
              <option value="bottom">
                {t.subtitleStudio.positionBottom}
              </option>
              <option value="top">{t.subtitleStudio.positionTop}</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
              {t.subtitleStudio.bgOpacity}: {Math.round(bgOpacity * 100)}%
            </label>
            <input
              type="range"
              min={0}
              max={1}
              step={0.1}
              value={bgOpacity}
              onChange={(e) => setBgOpacity(parseFloat(e.target.value))}
              className="w-full accent-blue-500"
            />
          </div>
        </div>
      </Card>

      {error && (
        <Card className="p-4 border-red-300 dark:border-red-700 bg-red-50 dark:bg-red-900/20">
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        </Card>
      )}

      {result && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle2 className="w-5 h-5 text-green-500" />
              <span className="font-medium text-gray-800 dark:text-gray-200">
                {t.subtitleStudio.subtitlesReady}
              </span>
              <Badge variant="success">
                {result.cue_count} {t.subtitleStudio.cueCount}
              </Badge>
            </div>
            <div className="flex gap-3 flex-wrap">
              <a
                href={`${API_BASE}${result.srt_url}`}
                download="subtitles.srt"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium transition-colors"
              >
                <Download className="w-4 h-4" />{" "}
                {t.subtitleStudio.downloadSrt}
              </a>
              <a
                href={`${API_BASE}${result.vtt_url}`}
                download="subtitles.vtt"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 text-white text-sm font-medium transition-colors"
              >
                <Download className="w-4 h-4" />{" "}
                {t.subtitleStudio.downloadVtt}
              </a>
            </div>
          </Card>

          <Card className="p-4">
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
              <FileText className="w-4 h-4 text-blue-400" />
              {t.subtitleStudio.previewPane}
            </h3>
            <div
              className="bg-black rounded-lg p-4 min-h-24 flex items-end justify-center relative"
              style={{ aspectRatio: "16/5" }}
            >
              <div
                className="text-white text-center px-3 py-1 rounded"
                style={{
                  fontSize: `${fontSize}px`,
                  backgroundColor: `rgba(0,0,0,${bgOpacity})`,
                  position: position === "top" ? "absolute" : "relative",
                  top: position === "top" ? "8px" : "auto",
                }}
              >
                {selectedProject?.language === "te"
                  ? "మీ సబ్‌టైటిల్ టెక్స్ట్ ఇక్కడ ప్రదర్శించబడుతుంది"
                  : "Your subtitle text will appear here"}
              </div>
            </div>
            <p className="text-xs text-gray-400 mt-2">
              Preview uses selected font size and position settings.
            </p>
          </Card>
        </div>
      )}

      {!result && !isGenerating && selectedProjectId && (
        <Card className="p-8 text-center">
          <FileText className="w-10 h-10 text-gray-400 mx-auto mb-3" />
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {t.subtitleStudio.noSubtitles}
          </p>
        </Card>
      )}

      {!selectedProjectId && (
        <Card className="p-12 text-center">
          <FileText className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-600 dark:text-gray-400 mb-2">
            {t.subtitleStudio.title}
          </h3>
          <p className="text-sm text-gray-400 dark:text-gray-500">
            {t.subtitleStudio.subtitle}
          </p>
        </Card>
      )}
    </div>
  );
}
