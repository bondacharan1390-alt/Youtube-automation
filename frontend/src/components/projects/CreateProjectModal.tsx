"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Film, Smartphone, Sparkles } from "lucide-react";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { useStudioStore } from "@/lib/store";
import { useTranslation } from "@/lib/i18n";
import { fetchApi } from "@/lib/api";

export const CreateProjectModal: React.FC = () => {
  const router = useRouter();
  const { t } = useTranslation();
  const isOpen = useStudioStore((state) => state.isCreateModalOpen);
  const setOpen = useStudioStore((state) => state.setCreateModalOpen);

  const [title, setTitle] = useState("");
  const [topic, setTopic] = useState("");
  const [language, setLanguage] = useState<"en" | "te">("en");
  const [aspectRatio, setAspectRatio] = useState<"16:9" | "9:16">("16:9");
  const [targetResolution, setTargetResolution] = useState<"720p" | "1080p">("1080p");
  const [targetSceneCount, setTargetSceneCount] = useState<number>(5);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError("Please provide a project title");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const created = await fetchApi<any>("/projects", {
        method: "POST",
        body: JSON.stringify({
          title,
          topic,
          language,
          aspect_ratio: aspectRatio,
          target_resolution: targetResolution,
          target_scene_count: targetSceneCount,
        }),
      });

      setOpen(false);
      // Reset form
      setTitle("");
      setTopic("");
      router.push(`/projects/${created.id}`);
      router.refresh();
    } catch (err: any) {
      setError(err.message || "Failed to create project");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={() => setOpen(false)}
      title={t.projects.createNew}
      className="max-w-xl"
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        {error && (
          <div className="p-3 text-xs bg-rose-50 text-rose-600 dark:bg-rose-950/40 dark:text-rose-400 border border-rose-200 dark:border-rose-900 rounded-lg">
            {error}
          </div>
        )}

        {/* Video Format Selection: 16:9 Long vs 9:16 Short */}
        <div className="space-y-1.5">
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
            {t.projects.aspectRatio}
          </label>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => {
                setAspectRatio("16:9");
                if (targetSceneCount < 5) setTargetSceneCount(5);
              }}
              className={`p-3.5 rounded-xl border flex items-center space-x-3 text-left transition-all ${
                aspectRatio === "16:9"
                  ? "border-red-600 bg-red-50/50 dark:bg-red-950/20 text-slate-900 dark:text-white ring-1 ring-red-500"
                  : "border-slate-200 dark:border-studio-800 hover:border-slate-300 dark:hover:border-studio-700"
              }`}
            >
              <div className="w-10 h-10 rounded-lg bg-slate-100 dark:bg-studio-800 flex items-center justify-center shrink-0">
                <Film className="w-5 h-5 text-red-600" />
              </div>
              <div>
                <p className="text-sm font-semibold">{t.projects.longForm}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400">1920x1080 Landscape</p>
              </div>
            </button>

            <button
              type="button"
              onClick={() => {
                setAspectRatio("9:16");
                if (targetSceneCount > 5) setTargetSceneCount(4);
              }}
              className={`p-3.5 rounded-xl border flex items-center space-x-3 text-left transition-all ${
                aspectRatio === "9:16"
                  ? "border-red-600 bg-red-50/50 dark:bg-red-950/20 text-slate-900 dark:text-white ring-1 ring-red-500"
                  : "border-slate-200 dark:border-studio-800 hover:border-slate-300 dark:hover:border-studio-700"
              }`}
            >
              <div className="w-10 h-10 rounded-lg bg-slate-100 dark:bg-studio-800 flex items-center justify-center shrink-0">
                <Smartphone className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <p className="text-sm font-semibold">{t.projects.shorts}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400">1080x1920 Vertical</p>
              </div>
            </button>
          </div>
        </div>

        {/* Title Input */}
        <Input
          label={t.projects.projectTitle}
          placeholder="e.g. 5 Mind-Blowing AI Inventions or తెలుగు చారిత్రక రహస్యాలు"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />

        {/* Topic / Idea Input */}
        <div className="space-y-1.5">
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
            {t.projects.topic}
          </label>
          <textarea
            className="w-full px-3.5 py-2 text-sm rounded-lg bg-slate-50 dark:bg-studio-950/70 border border-slate-300 dark:border-studio-700 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-red-500 transition-colors h-20 resize-none"
            placeholder="Describe the premise, core facts, or key narrative points..."
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
          />
        </div>

        {/* Language Selection & Resolution */}
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
              {t.projects.filterLanguage}
            </label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value as "en" | "te")}
              className="w-full px-3.5 py-2 text-sm rounded-lg bg-slate-50 dark:bg-studio-950/70 border border-slate-300 dark:border-studio-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-red-500"
            >
              <option value="en">English (Kokoro TTS 82M)</option>
              <option value="te">తెలుగు / Telugu (Edge-TTS Mohan/Shruti)</option>
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
              {t.projects.resolution}
            </label>
            <select
              value={targetResolution}
              onChange={(e) => setTargetResolution(e.target.value as "720p" | "1080p")}
              className="w-full px-3.5 py-2 text-sm rounded-lg bg-slate-50 dark:bg-studio-950/70 border border-slate-300 dark:border-studio-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-red-500"
            >
              <option value="1080p">1080p (Full HD)</option>
              <option value="720p">720p (Fast Draft)</option>
            </select>
          </div>
        </div>

        {/* Scene Count Slider */}
        <div className="space-y-1.5">
          <div className="flex justify-between items-center">
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
              {t.projects.targetScenes}: <span className="text-red-600 font-bold">{targetSceneCount}</span>
            </label>
            <span className="text-xs text-slate-500">
              ~{targetSceneCount * 6}s {t.scenes.estimatedTotalDuration}
            </span>
          </div>
          <input
            type="range"
            min={2}
            max={aspectRatio === "9:16" ? 8 : 15}
            value={targetSceneCount}
            onChange={(e) => setTargetSceneCount(parseInt(e.target.value, 10))}
            className="w-full accent-red-600 cursor-pointer"
          />
        </div>

        {/* Modal Action Buttons */}
        <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-200 dark:border-studio-800">
          <Button
            type="button"
            variant="ghost"
            onClick={() => setOpen(false)}
            disabled={isLoading}
          >
            {t.common.cancel}
          </Button>
          <Button
            type="submit"
            isLoading={isLoading}
            className="flex items-center space-x-1.5"
          >
            <Sparkles className="w-4 h-4" />
            <span>{t.common.create}</span>
          </Button>
        </div>
      </form>
    </Modal>
  );
};
