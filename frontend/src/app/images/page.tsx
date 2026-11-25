"use client";

import React, { useState, useEffect } from "react";
import {
  Image as ImageIcon,
  Sparkles,
  RefreshCw,
  Download,
  Film,
  Smartphone,
  CheckCircle2,
  HardDrive,
  Users,
  Eye,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { useTranslation } from "@/lib/i18n";
import { fetchApi, getMediaUrl } from "@/lib/api";

interface SceneItem {
  id: string;
  scene_order: number;
  script_text: string;
  visual_prompt: string;
  visual_asset_id?: string;
  image_url?: string;
  seed?: number;
}

interface ProjectSummary {
  id: string;
  title: string;
  aspect_ratio: string;
}

export default function ImageStudioPage() {
  const { t } = useTranslation();

  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [scenes, setScenes] = useState<SceneItem[]>([]);
  const [aspectRatio, setAspectRatio] = useState<string>("16:9");

  // Character Consistency & Prompt Settings (Arjun)
  const [characterTokens, setCharacterTokens] = useState<string>("Arjun, 25-year-old Indian male, oval face, dark brown eyes, short black hair, black futuristic jacket with glowing blue lines");
  const [negativePrompt, setNegativePrompt] = useState<string>("blurry, deformed, bad anatomy, text watermark, low quality");

  // Loading States
  const [loadingSceneId, setLoadingSceneId] = useState<string | null>(null);
  const [isBatchRendering, setIsBatchRendering] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  // Load Projects on Mount
  useEffect(() => {
    fetchApi<ProjectSummary[]>("/projects")
      .then((data) => {
        setProjects(data);
        if (data.length > 0) {
          setSelectedProjectId(data[0].id);
        }
      })
      .catch((err) => console.error("Failed to load projects:", err));
  }, []);

  // Load Scenes when Project changes
  useEffect(() => {
    if (selectedProjectId) {
      fetchApi<any>(`/projects/${selectedProjectId}`)
        .then((data) => {
          setScenes(data.scenes || []);
          setAspectRatio(data.aspect_ratio || "16:9");
        })
        .catch((err) => console.error("Failed to load project details:", err));
    }
  }, [selectedProjectId]);

  const handleGenerateSingle = async (scene: SceneItem) => {
    setLoadingSceneId(scene.id);
    setStatusMessage(null);
    try {
      const res = await fetchApi<any>("/images/generate", {
        method: "POST",
        body: JSON.stringify({
          scene_id: scene.id,
          prompt: scene.visual_prompt || `Scene ${scene.scene_order}`,
          aspect_ratio: aspectRatio,
          character_tokens: characterTokens,
          negative_prompt: negativePrompt,
        }),
      });

      setScenes((prev) =>
        prev.map((s) =>
          s.id === scene.id
            ? { ...s, image_url: res.image_url, seed: res.seed }
            : s
        )
      );
      setStatusMessage(`Rendered frame for Scene ${scene.scene_order}`);
    } catch (err: any) {
      alert(`Render failed: ${err.message}`);
    } finally {
      setLoadingSceneId(null);
    }
  };

  const handleRegenerate = async (scene: SceneItem) => {
    setLoadingSceneId(scene.id);
    try {
      const res = await fetchApi<any>(`/images/regenerate/${scene.id}`, {
        method: "POST",
        body: JSON.stringify({
          custom_prompt: scene.visual_prompt,
        }),
      });
      setScenes((prev) =>
        prev.map((s) =>
          s.id === scene.id
            ? { ...s, image_url: res.image_url, seed: res.seed }
            : s
        )
      );
      setStatusMessage(`Regenerated Scene ${scene.scene_order} with new seed #${res.seed}`);
    } catch (err: any) {
      alert(`Regeneration failed: ${err.message}`);
    } finally {
      setLoadingSceneId(null);
    }
  };

  const handleGenerateAll = async () => {
    if (!selectedProjectId) return;
    setIsBatchRendering(true);
    setStatusMessage("Sequential frame rendering in progress...");
    try {
      const results = await fetchApi<any[]>(`/images/generate-all/${selectedProjectId}`, {
        method: "POST",
        body: JSON.stringify({
          character_tokens: characterTokens,
          negative_prompt: negativePrompt,
        }),
      });

      setScenes((prev) =>
        prev.map((s) => {
          const match = results.find((r) => r.scene_id === s.id);
          return match ? { ...s, image_url: match.image_url, seed: match.seed } : s;
        })
      );
      setStatusMessage("All scene visual frames rendered successfully!");
    } catch (err: any) {
      alert(`Batch render failed: ${err.message}`);
    } finally {
      setIsBatchRendering(false);
    }
  };

  const isShort = aspectRatio === "9:16";

  return (
    <div className="space-y-8">
      {/* Studio Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-red-600 dark:text-red-400">
            <ImageIcon className="w-4 h-4" />
            <span>Module 5 &bull; Visual Synthesis Studio</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white mt-1">
            {t.imageStudio.title}
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            {t.imageStudio.subtitle}
          </p>
        </div>

        {/* Global Batch Render Button */}
        <Button
          onClick={handleGenerateAll}
          isLoading={isBatchRendering}
          disabled={scenes.length === 0}
          className="flex items-center space-x-1.5 self-start sm:self-auto font-semibold text-xs"
        >
          <Sparkles className="w-4 h-4" />
          <span>
            {isBatchRendering ? t.imageStudio.generating : t.imageStudio.generateAll}
          </span>
        </Button>
      </div>

      {/* Hardware Memory Guard Notice */}
      <div className="p-3.5 rounded-xl bg-slate-900 text-white border border-studio-800 flex items-center space-x-3 text-xs">
        <HardDrive className="w-4 h-4 text-emerald-400 shrink-0" />
        <span className="text-slate-300">{t.imageStudio.sequentialNotice}</span>
      </div>

      {/* Control Panel: Project Selection & Character Consistency */}
      <Card className="p-5 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Project Selector */}
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold uppercase text-slate-400">
              {t.imageStudio.selectProject}
            </label>
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-lg bg-slate-50 dark:bg-studio-950/80 border border-slate-300 dark:border-studio-700 text-slate-900 dark:text-slate-100 font-semibold"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.title} ({p.aspect_ratio})
                </option>
              ))}
            </select>
          </div>

          {/* Aspect Ratio Framing */}
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold uppercase text-slate-400">
              {t.imageStudio.aspectRatio}
            </label>
            <div className="flex bg-slate-100 dark:bg-studio-950 p-1 rounded-lg border border-slate-200 dark:border-studio-800 text-xs font-semibold">
              <button
                type="button"
                onClick={() => setAspectRatio("16:9")}
                className={`flex-1 py-1.5 rounded flex items-center justify-center space-x-1.5 transition-all ${
                  aspectRatio === "16:9"
                    ? "bg-white dark:bg-studio-800 text-red-600 dark:text-red-400 font-bold shadow-xs"
                    : "text-slate-500"
                }`}
              >
                <Film className="w-3.5 h-3.5" />
                <span>16:9 Landscape</span>
              </button>
              <button
                type="button"
                onClick={() => setAspectRatio("9:16")}
                className={`flex-1 py-1.5 rounded flex items-center justify-center space-x-1.5 transition-all ${
                  aspectRatio === "9:16"
                    ? "bg-white dark:bg-studio-800 text-purple-600 dark:text-purple-400 font-bold shadow-xs"
                    : "text-slate-500"
                }`}
              >
                <Smartphone className="w-3.5 h-3.5" />
                <span>9:16 Vertical Short</span>
              </button>
            </div>
          </div>
        </div>

        {/* Character Consistency Master Prompt */}
        <div className="space-y-1.5 pt-2 border-t border-slate-100 dark:border-studio-800">
          <label className="block text-xs font-semibold uppercase text-slate-400 flex items-center space-x-1.5">
            <Users className="w-3.5 h-3.5 text-purple-500" />
            <span>{t.imageStudio.characterConsistency}</span>
          </label>
          <Input
            value={characterTokens}
            onChange={(e) => setCharacterTokens(e.target.value)}
            placeholder={t.imageStudio.characterTokensPlaceholder}
          />
        </div>
      </Card>

      {/* Status Banner */}
      {statusMessage && (
        <div className="p-3 text-xs bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900 rounded-lg flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>{statusMessage}</span>
        </div>
      )}

      {/* Scene Visuals Gallery Grid */}
      <div className="space-y-4">
        <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center space-x-2">
          <ImageIcon className="w-4 h-4 text-red-600" />
          <span>Storyboard Frames ({scenes.length} Scenes)</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {scenes.map((scene, idx) => (
            <Card key={scene.id || idx} className="flex flex-col justify-between p-4 space-y-3">
              <div>
                {/* Scene Header */}
                <div className="flex items-center justify-between mb-2">
                  <span className="w-6 h-6 rounded-md bg-red-100 dark:bg-red-950/60 text-red-600 dark:text-red-400 font-bold text-xs flex items-center justify-center">
                    {scene.scene_order}
                  </span>
                  <div className="flex items-center space-x-2">
                    {scene.seed && (
                      <span className="text-[10px] font-mono text-slate-400">
                        Seed: #{scene.seed}
                      </span>
                    )}
                    {scene.image_url ? (
                      <Badge variant="success">Rendered</Badge>
                    ) : (
                      <Badge variant="default">Pending</Badge>
                    )}
                  </div>
                </div>

                {/* Visual Image Container */}
                <div
                  className={`w-full rounded-xl bg-slate-900 border border-slate-200 dark:border-studio-800 overflow-hidden relative flex items-center justify-center ${
                    isShort ? "aspect-[9/16] max-h-96 mx-auto" : "aspect-video"
                  }`}
                >
                  {scene.image_url ? (
                    <img
                      src={getMediaUrl(scene.image_url)}
                      alt={`Scene ${scene.scene_order}`}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="text-center p-4 space-y-2 text-slate-500">
                      <ImageIcon className="w-8 h-8 mx-auto opacity-50" />
                      <p className="text-xs font-medium">No frame rendered yet</p>
                      <span className="text-[10px] text-slate-600 block">{aspectRatio}</span>
                    </div>
                  )}
                </div>

                {/* Prompt Preview */}
                <p className="text-xs text-slate-600 dark:text-slate-300 font-mono mt-3 line-clamp-2 min-h-[32px]">
                  {scene.visual_prompt || scene.script_text}
                </p>
              </div>

              {/* Action Buttons */}
              <div className="pt-2 border-t border-slate-100 dark:border-studio-800 flex items-center justify-between gap-2">
                {scene.image_url ? (
                  <a
                    href={getMediaUrl(scene.image_url)}
                    download={`scene_${scene.scene_order}.png`}
                    className="p-1.5 rounded-lg bg-slate-100 dark:bg-studio-800 text-slate-600 dark:text-slate-300 hover:text-red-600 transition-colors flex items-center space-x-1 text-xs"
                    title="Download Frame PNG"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>PNG</span>
                  </a>
                ) : (
                  <div />
                )}

                <div className="flex items-center space-x-2">
                  {scene.image_url && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleRegenerate(scene)}
                      isLoading={loadingSceneId === scene.id}
                      className="text-xs flex items-center space-x-1"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                      <span>{t.imageStudio.regenerate}</span>
                    </Button>
                  )}

                  <Button
                    size="sm"
                    onClick={() => handleGenerateSingle(scene)}
                    isLoading={loadingSceneId === scene.id}
                    className="text-xs flex items-center space-x-1"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>{scene.image_url ? "Re-render" : t.imageStudio.generateSingle}</span>
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
