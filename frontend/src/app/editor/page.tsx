"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  Film,
  Download,
  Clock,
  Layers,
  AlertCircle,
  Sliders,
  Image as ImageIcon,
  Mic,
  ChevronRight,
  Loader2,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useTranslation } from "@/lib/i18n";
import { fetchApi } from "@/lib/api";

interface ProjectItem {
  id: string;
  title: string;
  aspect_ratio: string;
  target_resolution: string;
  language: string;
  status: string;
}

interface TimelineScene {
  scene_id: string;
  scene_order: number;
  script_text: string | null;
  narration_text: string | null;
  visual_prompt: string | null;
  duration_seconds: number;
  image_url: string | null;
  audio_url: string | null;
  transition: string;
}

interface TimelineData {
  project_id: string;
  title: string;
  language: string;
  aspect_ratio: string;
  target_resolution: string;
  scenes: TimelineScene[];
}

interface RenderStatus {
  job_id: string;
  status: string;
  progress_percentage: number;
  output_url: string | null;
  error_log: string | null;
}

export default function EditorPage() {
  const { t } = useTranslation();
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [timeline, setTimeline] = useState<TimelineData | null>(null);
  const [selectedScene, setSelectedScene] = useState<TimelineScene | null>(null);
  const [inspectorDuration, setInspectorDuration] = useState(5);
  const [inspectorNarration, setInspectorNarration] = useState("");
  const [inspectorTransition, setInspectorTransition] = useState("fade");
  const [includeSubtitles, setIncludeSubtitles] = useState(true);
  const [resolution, setResolution] = useState("1080p");
  const [renderStatus, setRenderStatus] = useState<RenderStatus | null>(null);
  const [isRendering, setIsRendering] = useState(false);
  const [isSavingScene, setIsSavingScene] = useState(false);
  const [loading, setLoading] = useState(false);
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    fetchApi("/projects/")
      .then((d: unknown) => {
        const arr = Array.isArray(d) ? d : (d as Record<string, unknown>).items || [];
        setProjects(arr as ProjectItem[]);
      })
      .catch(() => {});
  }, []);

  const loadTimeline = useCallback(async (projectId: string) => {
    if (!projectId) return;
    setLoading(true);
    setTimeline(null);
    setSelectedScene(null);
    try {
      const data = await fetchApi(`/editor/timeline/${projectId}`);
      setTimeline(data as TimelineData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedProjectId) loadTimeline(selectedProjectId);
  }, [selectedProjectId, loadTimeline]);

  const handleSceneClick = (scene: TimelineScene) => {
    setSelectedScene(scene);
    setInspectorDuration(scene.duration_seconds);
    setInspectorNarration(scene.narration_text || scene.script_text || "");
    setInspectorTransition(scene.transition || "fade");
  };

  const handleSaveScene = async () => {
    if (!selectedScene) return;
    setIsSavingScene(true);
    try {
      await fetchApi(`/editor/scenes/${selectedScene.scene_id}`, {
        method: "PATCH",
        body: JSON.stringify({
          duration_seconds: inspectorDuration,
          narration_text: inspectorNarration,
        }),
      });
      await loadTimeline(selectedProjectId);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSavingScene(false);
    }
  };

  const startRender = async () => {
    if (!selectedProjectId) return;
    setIsRendering(true);
    setRenderStatus(null);
    try {
      const job = (await fetchApi("/editor/render", {
        method: "POST",
        body: JSON.stringify({
          project_id: selectedProjectId,
          resolution,
          include_subtitles: includeSubtitles,
          bgm_volume: 0.15,
        }),
      })) as RenderStatus;
      setRenderStatus(job);
      pollRef.current = setInterval(async () => {
        try {
          const status = (await fetchApi(
            `/editor/render-status/${job.job_id}`
          )) as RenderStatus;
          setRenderStatus(status);
          if (status.status === "completed" || status.status === "failed") {
            if (pollRef.current) clearInterval(pollRef.current);
            setIsRendering(false);
          }
        } catch {
          /* ignore poll errors */
        }
      }, 2000);
    } catch {
      setIsRendering(false);
    }
  };

  useEffect(
    () => () => {
      if (pollRef.current) clearInterval(pollRef.current);
    },
    []
  );

  const totalDuration =
    timeline?.scenes.reduce((acc, s) => acc + s.duration_seconds, 0) || 0;
  const isPortrait = timeline?.aspect_ratio === "9:16";

  return (
    <div className="p-4 md:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Film className="w-6 h-6 text-purple-500" />
            {t.editorStudio.title}
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {t.editorStudio.subtitle}
          </p>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          {timeline && (
            <>
              <Badge variant="info">{timeline.aspect_ratio}</Badge>
              <Badge variant="success">{timeline.target_resolution}</Badge>
              <Badge variant="warning">
                {timeline.language === "te" ? "తెలుగు" : "English"}
              </Badge>
            </>
          )}
        </div>
      </div>

      {/* Project Selector */}
      <Card className="p-4">
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap">
            {t.editorStudio.selectProject}
          </label>
          <select
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            className="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-3 py-2 text-sm focus:ring-2 focus:ring-purple-500 outline-none"
          >
            <option value="">— {t.editorStudio.selectProject} —</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.title} [{p.aspect_ratio} · {p.status}]
              </option>
            ))}
          </select>
          {timeline && (
            <div className="flex gap-2 text-sm text-gray-500 dark:text-gray-400">
              <span>
                {timeline.scenes.length} {t.editorStudio.sceneCount}
              </span>
              <span>·</span>
              <span>
                {t.editorStudio.totalDuration}: {totalDuration.toFixed(1)}s
              </span>
            </div>
          )}
        </div>
      </Card>

      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
        </div>
      )}

      {timeline && (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Timeline — 2/3 width */}
          <div className="xl:col-span-2 space-y-4">
            <Card className="p-4">
              <h2 className="text-base font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
                <Layers className="w-4 h-4 text-purple-400" />
                {t.editorStudio.timeline}
              </h2>
              <div className="space-y-3">
                {timeline.scenes.map((scene) => (
                  <button
                    key={scene.scene_id}
                    onClick={() => handleSceneClick(scene)}
                    className={`w-full text-left rounded-xl border-2 transition-all p-3 flex gap-3 items-start ${
                      selectedScene?.scene_id === scene.scene_id
                        ? "border-purple-500 bg-purple-50 dark:bg-purple-900/20"
                        : "border-gray-200 dark:border-gray-700 hover:border-purple-300 bg-white dark:bg-gray-800"
                    }`}
                  >
                    <div
                      className={`flex-shrink-0 rounded-lg overflow-hidden bg-gray-900 ${
                        isPortrait ? "w-10 h-16" : "w-20 h-12"
                      } flex items-center justify-center`}
                    >
                      {scene.image_url ? (
                        <img
                          src={scene.image_url}
                          alt={`Scene ${scene.scene_order}`}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <ImageIcon className="w-5 h-5 text-gray-500" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-bold text-purple-500">
                          Scene {scene.scene_order}
                        </span>
                        <span className="text-xs text-gray-400 flex items-center gap-1">
                          <Clock className="w-3 h-3" /> {scene.duration_seconds}s
                        </span>
                        {scene.audio_url && (
                          <Mic className="w-3 h-3 text-green-500" />
                        )}
                        {scene.image_url && (
                          <ImageIcon className="w-3 h-3 text-blue-500" />
                        )}
                      </div>
                      <p className="text-xs text-gray-700 dark:text-gray-300 line-clamp-2">
                        {scene.narration_text || scene.script_text || "No text"}
                      </p>
                    </div>
                    <ChevronRight
                      className={`w-4 h-4 text-gray-400 flex-shrink-0 mt-1 transition-transform ${
                        selectedScene?.scene_id === scene.scene_id
                          ? "rotate-90 text-purple-500"
                          : ""
                      }`}
                    />
                  </button>
                ))}
              </div>
            </Card>

            {/* Render Controls */}
            <Card className="p-4 space-y-4">
              <h2 className="text-base font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-2">
                <Film className="w-4 h-4 text-purple-400" />
                Render Controls
              </h2>
              <div className="flex flex-wrap gap-4 items-center">
                <div className="flex items-center gap-2">
                  <label className="text-sm text-gray-600 dark:text-gray-400">
                    {t.editorStudio.resolution}:
                  </label>
                  <select
                    value={resolution}
                    onChange={(e) => setResolution(e.target.value)}
                    className="rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm px-2 py-1 text-gray-900 dark:text-white"
                  >
                    <option value="1080p">1080p</option>
                    <option value="720p">720p</option>
                  </select>
                </div>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeSubtitles}
                    onChange={(e) => setIncludeSubtitles(e.target.checked)}
                    className="rounded accent-purple-500"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    {t.editorStudio.includeSubtitles}
                  </span>
                </label>
                <Button
                  variant="primary"
                  disabled={isRendering}
                  onClick={startRender}
                  className="ml-auto"
                >
                  {isRendering ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      {t.editorStudio.renderProgress}
                    </>
                  ) : (
                    <>
                      <Film className="w-4 h-4 mr-2" />
                      {t.editorStudio.renderButton}
                    </>
                  )}
                </Button>
              </div>

              {renderStatus && (
                <div className="mt-2 space-y-2">
                  <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
                    <span>{renderStatus.error_log || renderStatus.status}</span>
                    <span>{renderStatus.progress_percentage}%</span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all duration-500 ${
                        renderStatus.status === "failed"
                          ? "bg-red-500"
                          : renderStatus.status === "completed"
                          ? "bg-green-500"
                          : "bg-purple-500"
                      }`}
                      style={{ width: `${renderStatus.progress_percentage}%` }}
                    />
                  </div>
                  {renderStatus.status === "completed" &&
                    renderStatus.output_url && (
                      <a
                        href={`${
                          process.env.NEXT_PUBLIC_API_URL ||
                          "http://localhost:8000"
                        }${renderStatus.output_url}`}
                        download
                        className="inline-flex items-center gap-2 text-sm text-green-600 dark:text-green-400 font-medium hover:underline"
                      >
                        <Download className="w-4 h-4" />
                        {t.editorStudio.downloadMp4}
                      </a>
                    )}
                  {renderStatus.status === "failed" && (
                    <p className="text-xs text-red-500 flex items-center gap-1">
                      <AlertCircle className="w-3 h-3" />{" "}
                      {t.editorStudio.renderFailed}
                    </p>
                  )}
                </div>
              )}
            </Card>
          </div>

          {/* Scene Inspector — 1/3 */}
          <div>
            <Card className="p-4 sticky top-4">
              <h2 className="text-base font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
                <Sliders className="w-4 h-4 text-purple-400" />
                {t.editorStudio.sceneInspector}
              </h2>
              {selectedScene ? (
                <div className="space-y-4">
                  <div>
                    <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">
                      Scene {selectedScene.scene_order}
                    </p>
                    {selectedScene.image_url && (
                      <img
                        src={selectedScene.image_url}
                        alt="Scene preview"
                        className={`rounded-lg object-cover mb-3 ${
                          isPortrait ? "h-32 w-20" : "w-full h-24"
                        }`}
                      />
                    )}
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                      {t.editorStudio.duration}
                    </label>
                    <input
                      type="number"
                      min={1}
                      max={30}
                      step={0.5}
                      value={inspectorDuration}
                      onChange={(e) =>
                        setInspectorDuration(parseFloat(e.target.value))
                      }
                      className="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-2 py-1 text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                      {t.editorStudio.transition}
                    </label>
                    <select
                      value={inspectorTransition}
                      onChange={(e) => setInspectorTransition(e.target.value)}
                      className="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-2 py-1 text-sm"
                    >
                      <option value="fade">
                        {t.editorStudio.transitionFade}
                      </option>
                      <option value="cut">
                        {t.editorStudio.transitionCut}
                      </option>
                      <option value="slide">
                        {t.editorStudio.transitionSlide}
                      </option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                      Narration
                    </label>
                    <textarea
                      value={inspectorNarration}
                      onChange={(e) => setInspectorNarration(e.target.value)}
                      rows={4}
                      className="w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-2 py-1 text-sm resize-none"
                    />
                  </div>
                  <Button
                    variant="primary"
                    className="w-full"
                    disabled={isSavingScene}
                    onClick={handleSaveScene}
                  >
                    {isSavingScene ? (
                      <Loader2 className="w-4 h-4 animate-spin mr-2" />
                    ) : null}
                    {t.editorStudio.saveChanges}
                  </Button>
                  {selectedScene.audio_url && (
                    <div>
                      <p className="text-xs text-gray-400 mb-1 flex items-center gap-1">
                        <Mic className="w-3 h-3" /> Audio
                      </p>
                      <audio
                        controls
                        src={`${
                          process.env.NEXT_PUBLIC_API_URL ||
                          "http://localhost:8000"
                        }${selectedScene.audio_url}`}
                        className="w-full"
                      />
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-sm text-gray-400 text-center py-8">
                  Click a scene in the timeline to inspect and edit it.
                </p>
              )}
            </Card>
          </div>
        </div>
      )}

      {!timeline && !loading && selectedProjectId && (
        <Card className="p-8 text-center">
          <Film className="w-10 h-10 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-500 dark:text-gray-400">
            Loading timeline...
          </p>
        </Card>
      )}

      {!selectedProjectId && (
        <Card className="p-12 text-center">
          <Film className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-600 dark:text-gray-400 mb-2">
            {t.editorStudio.noProject}
          </h3>
          <p className="text-sm text-gray-400 dark:text-gray-500">
            {t.editorStudio.subtitle}
          </p>
        </Card>
      )}
    </div>
  );
}
