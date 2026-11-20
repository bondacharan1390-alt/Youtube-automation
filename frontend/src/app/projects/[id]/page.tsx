"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Film,
  Smartphone,
  Save,
  Clock,
  Sparkles,
  Layers,
  Plus,
  Play,
  CheckCircle,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { useTranslation } from "@/lib/i18n";
import { fetchApi } from "@/lib/api";
import { formatDuration } from "@/lib/utils";

interface SceneItem {
  id: string;
  scene_order: number;
  script_text: string;
  narration_text: string;
  visual_prompt: string;
  duration_seconds: number;
}

interface ProjectDetail {
  id: string;
  title: string;
  topic?: string;
  language: string;
  aspect_ratio: string;
  target_resolution: string;
  status: string;
  estimated_duration_seconds: number;
  scenes: SceneItem[];
}

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { t } = useTranslation();
  const projectId = params?.id as string;

  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [scenes, setScenes] = useState<SceneItem[]>([]);
  const [activeTab, setActiveTab] = useState<"timeline" | "settings">("timeline");
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  useEffect(() => {
    if (projectId) {
      fetchApi<ProjectDetail>(`/projects/${projectId}`)
        .then((data) => {
          setProject(data);
          setScenes(data.scenes || []);
        })
        .catch((err) => {
          console.error("Failed to load project:", err);
        });
    }
  }, [projectId]);

  const handleSceneChange = (
    index: number,
    field: keyof SceneItem,
    value: string | number
  ) => {
    setScenes((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  };

  const handleAddScene = async () => {
    if (!project) return;
    const newOrder = scenes.length + 1;
    try {
      const createdScene = await fetchApi<SceneItem>(`/projects/${project.id}/scenes`, {
        method: "POST",
        body: JSON.stringify({
          scene_order: newOrder,
          script_text: `Scene ${newOrder} outline`,
          narration_text: "",
          visual_prompt: `Visual concept for scene ${newOrder}`,
          duration_seconds: 6.0,
        }),
      });
      setScenes((prev) => [...prev, createdScene]);
    } catch (err) {
      alert("Failed to add scene");
    }
  };

  const handleSave = async () => {
    if (!project) return;
    setIsSaving(true);
    setSaveMessage(null);
    try {
      const totalDuration = scenes.reduce((acc, s) => acc + (s.duration_seconds || 6), 0);
      await fetchApi(`/projects/${project.id}`, {
        method: "PUT",
        body: JSON.stringify({
          title: project.title,
          topic: project.topic,
          estimated_duration_seconds: totalDuration,
        }),
      });
      setSaveMessage("Saved changes successfully");
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (err: any) {
      alert(`Save failed: ${err.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  if (!project) {
    return (
      <div className="py-20 text-center">
        <p className="text-sm text-slate-500 animate-pulse">{t.common.loading}</p>
      </div>
    );
  }

  const isShort = project.aspect_ratio === "9:16";
  const totalDuration = scenes.reduce((acc, s) => acc + (s.duration_seconds || 6), 0);

  return (
    <div className="space-y-6">
      {/* Top Header & Breadcrumb */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-studio-800/80 pb-4">
        <div className="flex items-center space-x-3">
          <Link
            href="/projects"
            className="p-2 rounded-lg bg-slate-100 dark:bg-studio-900 text-slate-600 dark:text-slate-300 hover:bg-slate-200 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center space-x-2">
              <span
                className={`p-1 rounded text-xs font-semibold flex items-center space-x-1 ${
                  isShort
                    ? "bg-purple-100 text-purple-700 dark:bg-purple-950/50 dark:text-purple-300"
                    : "bg-red-100 text-red-700 dark:bg-red-950/50 dark:text-red-300"
                }`}
              >
                {isShort ? <Smartphone className="w-3 h-3" /> : <Film className="w-3 h-3" />}
                <span>{isShort ? "9:16 Short" : "16:9 Long"}</span>
              </span>

              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 dark:bg-studio-900 text-slate-600 dark:text-slate-300">
                {project.language === "te" ? "తెలుగు" : "English"}
              </span>

              <Badge variant="default">{project.status}</Badge>
            </div>

            <h1 className="text-xl font-bold text-slate-900 dark:text-white mt-1">
              {project.title}
            </h1>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-3">
          {saveMessage && (
            <span className="text-xs text-emerald-500 flex items-center space-x-1">
              <CheckCircle className="w-3.5 h-3.5" />
              <span>{saveMessage}</span>
            </span>
          )}
          <Button
            size="sm"
            variant="secondary"
            onClick={handleSave}
            isLoading={isSaving}
            className="flex items-center space-x-1.5"
          >
            <Save className="w-4 h-4" />
            <span>{t.common.save}</span>
          </Button>
        </div>
      </div>

      {/* Stepper Workflow Status */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-xs font-semibold select-none">
        {[
          { label: "1. Research & Script", active: true },
          { label: "2. Voice Narration", active: false },
          { label: "3. AI Visuals", active: false },
          { label: "4. Assembly & Subtitles", active: false },
          { label: "5. Publish Review", active: false },
        ].map((step, idx) => (
          <div
            key={idx}
            className={`p-2.5 rounded-xl border text-center transition-all ${
              step.active
                ? "bg-red-50 text-red-700 border-red-300 dark:bg-red-950/30 dark:text-red-400 dark:border-red-900 font-bold"
                : "bg-slate-100 text-slate-400 border-transparent dark:bg-studio-900/60 dark:text-slate-500"
            }`}
          >
            {step.label}
          </div>
        ))}
      </div>

      {/* Main Content Layout: Timeline & Preview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Scene-by-scene editing studio */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-slate-900 dark:text-white flex items-center space-x-2">
              <Layers className="w-4 h-4 text-red-600" />
              <span>{t.scenes.sceneBreakdown}</span>
              <span className="text-xs text-slate-400 font-normal">
                ({scenes.length} {t.projects.scenes} &bull; {formatDuration(totalDuration)})
              </span>
            </h3>

            <Button
              size="sm"
              variant="outline"
              onClick={handleAddScene}
              className="text-xs flex items-center space-x-1"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>{t.scenes.addScene}</span>
            </Button>
          </div>

          {/* Scene Cards List */}
          <div className="space-y-4">
            {scenes.map((scene, idx) => (
              <Card key={scene.id || idx} className="space-y-3">
                <div className="flex items-center justify-between border-b border-slate-100 dark:border-studio-800 pb-2">
                  <span className="text-xs font-bold uppercase text-red-600 dark:text-red-400">
                    {t.scenes.scene} {scene.scene_order}
                  </span>
                  <div className="flex items-center space-x-2">
                    <span className="text-[11px] text-slate-400 flex items-center space-x-1">
                      <Clock className="w-3 h-3" />
                      <span>{scene.duration_seconds}s</span>
                    </span>
                  </div>
                </div>

                {/* Script Outline */}
                <div>
                  <label className="block text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                    {t.scenes.scriptText}
                  </label>
                  <input
                    type="text"
                    value={scene.script_text || ""}
                    onChange={(e) => handleSceneChange(idx, "script_text", e.target.value)}
                    className="w-full px-3 py-1.5 text-xs rounded-lg bg-slate-50 dark:bg-studio-950/70 border border-slate-200 dark:border-studio-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-red-500"
                    placeholder="Enter scene concept..."
                  />
                </div>

                {/* Narration Voice Text */}
                <div>
                  <label className="block text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                    {t.scenes.narrationText}
                  </label>
                  <textarea
                    rows={2}
                    value={scene.narration_text || ""}
                    onChange={(e) => handleSceneChange(idx, "narration_text", e.target.value)}
                    className="w-full px-3 py-1.5 text-xs rounded-lg bg-slate-50 dark:bg-studio-950/70 border border-slate-200 dark:border-studio-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-red-500 resize-none"
                    placeholder="Exact voiceover lines to be spoken..."
                  />
                </div>

                {/* Visual Prompt */}
                <div>
                  <label className="block text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                    {t.scenes.visualPrompt}
                  </label>
                  <input
                    type="text"
                    value={scene.visual_prompt || ""}
                    onChange={(e) => handleSceneChange(idx, "visual_prompt", e.target.value)}
                    className="w-full px-3 py-1.5 text-xs rounded-lg bg-slate-50 dark:bg-studio-950/70 border border-slate-200 dark:border-studio-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-red-500"
                    placeholder="Visual generation prompt for image/video synthesis..."
                  />
                </div>
              </Card>
            ))}
          </div>
        </div>

        {/* Right 1 Col: Preview Shell & Metadata */}
        <div className="space-y-4">
          <Card className="text-center p-6 space-y-4">
            <h4 className="text-sm font-semibold text-slate-900 dark:text-white">
              Video Player Preview
            </h4>

            {/* Aspect Frame Simulator */}
            <div
              className={`mx-auto rounded-xl bg-slate-900 border border-studio-800 flex flex-col items-center justify-center p-4 text-slate-400 shadow-inner relative overflow-hidden ${
                isShort ? "w-44 h-80" : "w-full aspect-video"
              }`}
            >
              <Play className="w-10 h-10 text-red-500 mb-2 opacity-80" />
              <p className="text-xs text-center font-medium px-2">
                {project.title}
              </p>
              <span className="text-[10px] text-slate-500 mt-1">
                {project.aspect_ratio} &bull; {project.target_resolution}
              </span>
            </div>

            <p className="text-xs text-slate-500 dark:text-slate-400">
              Remotion Real-Time Preview will render live scene compositions here during Phase 4.
            </p>
          </Card>

          {/* Quick Specifications */}
          <Card className="space-y-3 text-xs">
            <h4 className="font-semibold text-slate-900 dark:text-white uppercase tracking-wider text-[11px]">
              Project Specifications
            </h4>
            <div className="flex justify-between py-1 border-b border-slate-100 dark:border-studio-800">
              <span className="text-slate-500">Language:</span>
              <span className="font-semibold">{project.language === "te" ? "Telugu" : "English"}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100 dark:border-studio-800">
              <span className="text-slate-500">Aspect Ratio:</span>
              <span className="font-semibold">{project.aspect_ratio}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100 dark:border-studio-800">
              <span className="text-slate-500">Resolution:</span>
              <span className="font-semibold">{project.target_resolution}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Est. Total Duration:</span>
              <span className="font-semibold">{formatDuration(totalDuration)}</span>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
