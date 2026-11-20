"use client";

import React, { useState, useEffect } from "react";
import {
  Mic,
  Volume2,
  Play,
  Pause,
  Download,
  Sparkles,
  CheckCircle2,
  Clock,
  Layers,
  Settings,
  HardDrive,
  RefreshCw,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useTranslation } from "@/lib/i18n";
import { fetchApi } from "@/lib/api";

interface VoiceItem {
  id: string;
  name: string;
  gender: string;
  language: string;
  engine: string;
}

interface SceneItem {
  id: string;
  scene_order: number;
  script_text: string;
  narration_text: string;
  duration_seconds: number;
  voice_asset_id?: string;
  audio_url?: string;
}

interface ProjectSummary {
  id: string;
  title: string;
  language: string;
}

export default function VoiceStudioPage() {
  const { t, language } = useTranslation();

  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [scenes, setScenes] = useState<SceneItem[]>([]);
  const [voices, setVoices] = useState<VoiceItem[]>([]);

  // Filters & Parameters
  const [selectedVoice, setSelectedVoice] = useState<string>("te-IN-MohanNeural");
  const [genderFilter, setGenderFilter] = useState<string>("all");
  const [speed, setSpeed] = useState<number>(1.0);
  const [pitch, setPitch] = useState<number>(0.0);
  const [audioFormat, setAudioFormat] = useState<"mp3" | "wav">("mp3");

  // Playback & Loading States
  const [loadingSceneId, setLoadingSceneId] = useState<string | null>(null);
  const [isBatchSynthesizing, setIsBatchSynthesizing] = useState(false);
  const [playingAudioUrl, setPlayingAudioUrl] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  // Load Voices & Projects on Mount
  useEffect(() => {
    fetchApi<VoiceItem[]>("/voice/voices")
      .then((data) => {
        setVoices(data);
        if (data.length > 0) {
          const defaultV = data.find((v) => v.id === "te-IN-MohanNeural") || data[0];
          setSelectedVoice(defaultV.id);
        }
      })
      .catch((err) => console.error("Failed to load voices:", err));

    fetchApi<ProjectSummary[]>("/projects")
      .then((data) => {
        setProjects(data);
        if (data.length > 0) {
          setSelectedProjectId(data[0].id);
        }
      })
      .catch((err) => console.error("Failed to load projects:", err));
  }, []);

  // Load scenes when selectedProjectId changes
  useEffect(() => {
    if (selectedProjectId) {
      fetchApi<any>(`/projects/${selectedProjectId}`)
        .then((data) => {
          setScenes(data.scenes || []);
          if (data.language === "te") {
            setSelectedVoice("te-IN-MohanNeural");
          } else {
            setSelectedVoice("en-US-ChristopherNeural");
          }
        })
        .catch((err) => console.error("Failed to load project details:", err));
    }
  }, [selectedProjectId]);

  const handleSynthesizeSingle = async (scene: SceneItem) => {
    setLoadingSceneId(scene.id);
    setStatusMessage(null);
    try {
      const res = await fetchApi<any>("/voice/synthesize", {
        method: "POST",
        body: JSON.stringify({
          scene_id: scene.id,
          text: scene.narration_text || scene.script_text || `Scene ${scene.scene_order}`,
          voice_id: selectedVoice,
          speed,
          pitch,
          output_format: audioFormat,
        }),
      });

      // Update local scene audio url
      setScenes((prev) =>
        prev.map((s) => (s.id === scene.id ? { ...s, audio_url: res.audio_url } : s))
      );
      setStatusMessage(`Synthesized audio for Scene ${scene.scene_order}`);
    } catch (err: any) {
      alert(`Synthesis failed: ${err.message}`);
    } finally {
      setLoadingSceneId(null);
    }
  };

  const handleSynthesizeAll = async () => {
    if (!selectedProjectId) return;
    setIsBatchSynthesizing(true);
    setStatusMessage("Sequential synthesis in progress...");
    try {
      const results = await fetchApi<any[]>(`/voice/synthesize-all/${selectedProjectId}`, {
        method: "POST",
        body: JSON.stringify({
          voice_id: selectedVoice,
          speed,
          pitch,
        }),
      });

      // Map generated audio URLs back to scenes
      setScenes((prev) =>
        prev.map((s) => {
          const match = results.find((r) => r.scene_id === s.id);
          return match ? { ...s, audio_url: match.audio_url } : s;
        })
      );
      setStatusMessage("All scenes synthesized successfully!");
    } catch (err: any) {
      alert(`Batch synthesis failed: ${err.message}`);
    } finally {
      setIsBatchSynthesizing(false);
    }
  };

  const filteredVoices = voices.filter((v) => {
    if (genderFilter !== "all" && v.gender !== genderFilter) return false;
    return true;
  });

  return (
    <div className="space-y-8">
      {/* Studio Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-red-600 dark:text-red-400">
            <Mic className="w-4 h-4" />
            <span>Module 4 &bull; Audio Synthesis Studio</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white mt-1">
            {t.voiceStudio.title}
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            {t.voiceStudio.subtitle}
          </p>
        </div>

        {/* Global Batch Synthesize Button */}
        <Button
          onClick={handleSynthesizeAll}
          isLoading={isBatchSynthesizing}
          disabled={scenes.length === 0}
          className="flex items-center space-x-1.5 self-start sm:self-auto font-semibold text-xs"
        >
          <Sparkles className="w-4 h-4" />
          <span>
            {isBatchSynthesizing ? t.voiceStudio.synthesizing : t.voiceStudio.synthesizeAll}
          </span>
        </Button>
      </div>

      {/* Hardware Memory Guard Notice */}
      <div className="p-3.5 rounded-xl bg-slate-900 text-white border border-studio-800 flex items-center space-x-3 text-xs">
        <HardDrive className="w-4 h-4 text-emerald-400 shrink-0" />
        <span className="text-slate-300">{t.voiceStudio.sequentialNotice}</span>
      </div>

      {/* Control Panel: Project Selection & Voice Parameters */}
      <Card className="p-5 space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Project Selector */}
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold uppercase text-slate-400">
              {t.voiceStudio.selectProject}
            </label>
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-lg bg-slate-50 dark:bg-studio-950/80 border border-slate-300 dark:border-studio-700 text-slate-900 dark:text-slate-100 font-semibold"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.title} ({p.language === "te" ? "తెలుగు" : "English"})
                </option>
              ))}
            </select>
          </div>

          {/* Voice Actor Selector */}
          <div className="space-y-1.5">
            <div className="flex justify-between items-center">
              <label className="block text-xs font-semibold uppercase text-slate-400">
                {t.voiceStudio.voiceSelector}
              </label>
              {/* Gender Filter Buttons */}
              <div className="flex space-x-1 text-[11px]">
                <button
                  type="button"
                  onClick={() => setGenderFilter("all")}
                  className={`px-2 py-0.5 rounded ${
                    genderFilter === "all" ? "bg-red-600 text-white font-bold" : "text-slate-400"
                  }`}
                >
                  All
                </button>
                <button
                  type="button"
                  onClick={() => setGenderFilter("male")}
                  className={`px-2 py-0.5 rounded ${
                    genderFilter === "male" ? "bg-red-600 text-white font-bold" : "text-slate-400"
                  }`}
                >
                  Male
                </button>
                <button
                  type="button"
                  onClick={() => setGenderFilter("female")}
                  className={`px-2 py-0.5 rounded ${
                    genderFilter === "female" ? "bg-red-600 text-white font-bold" : "text-slate-400"
                  }`}
                >
                  Female
                </button>
              </div>
            </div>

            <select
              value={selectedVoice}
              onChange={(e) => setSelectedVoice(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-lg bg-slate-50 dark:bg-studio-950/80 border border-slate-300 dark:border-studio-700 text-slate-900 dark:text-slate-100 font-semibold"
            >
              {filteredVoices.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.name} ({v.engine.toUpperCase()})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Sliders: Speed, Pitch & Format */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-3 border-t border-slate-100 dark:border-studio-800">
          {/* Speed Slider */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs font-semibold">
              <span className="text-slate-400 uppercase">{t.voiceStudio.speed}</span>
              <span className="text-red-600 font-bold">{speed.toFixed(1)}x</span>
            </div>
            <input
              type="range"
              min="0.7"
              max="1.5"
              step="0.05"
              value={speed}
              onChange={(e) => setSpeed(parseFloat(e.target.value))}
              className="w-full accent-red-600 cursor-pointer"
            />
          </div>

          {/* Pitch Slider */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs font-semibold">
              <span className="text-slate-400 uppercase">{t.voiceStudio.pitch}</span>
              <span className="text-red-600 font-bold">{pitch > 0 ? `+${pitch}` : pitch} Hz</span>
            </div>
            <input
              type="range"
              min="-20"
              max="20"
              step="1"
              value={pitch}
              onChange={(e) => setPitch(parseFloat(e.target.value))}
              className="w-full accent-red-600 cursor-pointer"
            />
          </div>

          {/* Audio Format Selector */}
          <div className="space-y-1.5">
            <span className="block text-xs font-semibold uppercase text-slate-400">
              {t.voiceStudio.format}
            </span>
            <div className="flex bg-slate-100 dark:bg-studio-950 p-1 rounded-lg border border-slate-200 dark:border-studio-800 text-xs">
              <button
                type="button"
                onClick={() => setAudioFormat("mp3")}
                className={`flex-1 py-1 rounded text-center transition-all ${
                  audioFormat === "mp3"
                    ? "bg-white dark:bg-studio-800 font-bold text-red-600 dark:text-red-400 shadow-xs"
                    : "text-slate-500"
                }`}
              >
                MP3 (High Quality)
              </button>
              <button
                type="button"
                onClick={() => setAudioFormat("wav")}
                className={`flex-1 py-1 rounded text-center transition-all ${
                  audioFormat === "wav"
                    ? "bg-white dark:bg-studio-800 font-bold text-red-600 dark:text-red-400 shadow-xs"
                    : "text-slate-500"
                }`}
              >
                WAV (Lossless PCM)
              </button>
            </div>
          </div>
        </div>
      </Card>

      {/* Status banner */}
      {statusMessage && (
        <div className="p-3 text-xs bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900 rounded-lg flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>{statusMessage}</span>
        </div>
      )}

      {/* Scene Audio Table / Cards */}
      <div className="space-y-4">
        <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center space-x-2">
          <Layers className="w-4 h-4 text-red-600" />
          <span>Scene Voiceovers ({scenes.length} Scenes)</span>
        </h3>

        <div className="space-y-3">
          {scenes.map((scene, idx) => (
            <Card key={scene.id || idx} className="p-4 sm:p-5 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="w-6 h-6 rounded-md bg-red-100 dark:bg-red-950/60 text-red-600 dark:text-red-400 font-bold text-xs flex items-center justify-center">
                    {scene.scene_order}
                  </span>
                  <span className="text-xs font-bold text-slate-900 dark:text-white">
                    Scene {scene.scene_order} Audio
                  </span>
                </div>

                <div className="flex items-center space-x-2">
                  <span className="text-xs text-slate-400 flex items-center space-x-1">
                    <Clock className="w-3.5 h-3.5" />
                    <span>~{scene.duration_seconds}s</span>
                  </span>
                  {scene.audio_url ? (
                    <Badge variant="success">Audio Ready</Badge>
                  ) : (
                    <Badge variant="default">Pending Voice</Badge>
                  )}
                </div>
              </div>

              {/* Spoken Text */}
              <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-200 bg-slate-50 dark:bg-studio-950/60 p-3 rounded-lg border border-slate-200/60 dark:border-studio-800 leading-relaxed font-medium">
                {scene.narration_text || scene.script_text}
              </p>

              {/* Audio Player and Action Controls */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
                {scene.audio_url ? (
                  <div className="flex items-center space-x-3 w-full sm:w-auto">
                    <audio
                      controls
                      src={`http://localhost:8000${scene.audio_url}`}
                      className="h-9 w-full sm:w-80"
                    />
                    <a
                      href={`http://localhost:8000${scene.audio_url}`}
                      download={`scene_${scene.scene_order}.${audioFormat}`}
                      className="p-2 rounded-lg bg-slate-100 dark:bg-studio-800 text-slate-600 dark:text-slate-300 hover:text-red-600 transition-colors"
                      title="Download Audio File"
                    >
                      <Download className="w-4 h-4" />
                    </a>
                  </div>
                ) : (
                  <span className="text-xs text-slate-400 italic">
                    Audio not synthesized yet for this scene
                  </span>
                )}

                <Button
                  size="sm"
                  variant={scene.audio_url ? "secondary" : "primary"}
                  onClick={() => handleSynthesizeSingle(scene)}
                  isLoading={loadingSceneId === scene.id}
                  className="text-xs flex items-center space-x-1.5 self-end sm:self-auto shrink-0"
                >
                  <Mic className="w-3.5 h-3.5" />
                  <span>{scene.audio_url ? "Re-synthesize" : t.voiceStudio.synthesizeSingle}</span>
                </Button>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
