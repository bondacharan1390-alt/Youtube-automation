"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  FileText,
  Sparkles,
  Film,
  Smartphone,
  Download,
  Save,
  Clock,
  Layers,
  Users,
  MessageSquare,
  Plus,
  Trash2,
  CheckCircle2,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { useTranslation } from "@/lib/i18n";
import { fetchApi } from "@/lib/api";
import { formatDuration } from "@/lib/utils";

interface SceneItem {
  scene_order: number;
  script_text: string;
  narration_text: string;
  visual_prompt: string;
  duration_seconds: number;
  character_name?: string;
}

interface CharacterItem {
  name: string;
  role: string;
  voice_style: string;
  visual_prompt: string;
}

function ScriptStudioContent() {
  const searchParams = useSearchParams();
  const { t, language } = useTranslation();

  const [activeTab, setActiveTab] = useState<"storyboard" | "dialogue">("storyboard");

  // Script Generator State
  const [title, setTitle] = useState(searchParams?.get("title") || "5 Mind-Blowing AI Breakthroughs in 2026");
  const [topic, setTopic] = useState(searchParams?.get("topic") || "Autonomous AI video agents");
  const [scriptLang, setScriptLang] = useState<"en" | "te">((searchParams?.get("language") as any) || language);
  const [aspectRatio, setAspectRatio] = useState<"16:9" | "9:16">((searchParams?.get("aspect_ratio") as any) || "16:9");
  const [targetSceneCount, setTargetSceneCount] = useState<number>(aspectRatio === "9:16" ? 3 : 5);
  const [tone, setTone] = useState("engaging");

  // Output States
  const [scenes, setScenes] = useState<SceneItem[]>([]);
  const [characters, setCharacters] = useState<CharacterItem[]>([
    {
      name: "Narrator",
      role: "Host / Storyteller",
      voice_style: "Dynamic, cinematic, and authoritative",
      visual_prompt: "Professional YouTuber in high-tech studio with moody cyan lighting, 8k",
    },
  ]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  // Initial auto-generation on mount if query params present
  useEffect(() => {
    if (searchParams?.get("title")) {
      handleGenerateStoryboard();
    } else {
      // Default initial starter scenes
      setScenes([
        {
          scene_order: 1,
          script_text: "Cold Hook: The 2026 AI Revolution",
          narration_text: scriptLang === "te" 
            ? "మీరు ఎప్పుడైనా ఆలోచించారా? కేవలం కొన్ని సెకన్లలో మీ జీవితాన్ని మార్చే సరికొత్త సాంకేతికత ఏమిటో?" 
            : "What if everything you thought you knew about automated creation changed in a single weekend?",
          visual_prompt: "Cinematic establishing shot of a lone creator silhouette standing before massive panoramic displays, 16:9, 8k",
          duration_seconds: 6.5,
        },
        {
          scene_order: 2,
          script_text: "The Breakdown: How it operates",
          narration_text: scriptLang === "te"
            ? "పరిశోధకులు అభివృద్ధి చేసిన ఈ కొత్త ఆర్కిటెక్చర్ సహాయంతో వీడియో నిర్మాణం పది రెట్లు వేగవంతం అయ్యింది."
            : "Autonomous AI pipelines can now orchestrate scriptwriting, voiceover, and visual montage in minutes.",
          visual_prompt: "Holographic video timeline assembling itself with glowing cyan and gold UI elements, photorealistic",
          duration_seconds: 7.5,
        },
        {
          scene_order: 3,
          script_text: "Outro: Call to action",
          narration_text: scriptLang === "te"
            ? "ఈ వీడియో మీకు నచ్చితే వెంటనే లైక్ చేయండి, మరిన్ని అద్భుతమైన వీడియోల కోసం ఇప్పుడే సబ్‌స్క్రైబ్ చేసుకోండి!"
            : "Hit that subscribe button right now to stay ahead of the future.",
          visual_prompt: "Modern glowing YouTube outro card with subscribe button and dynamic particle ripples, 16:9",
          duration_seconds: 5.5,
        },
      ]);
    }
  }, [searchParams]);

  const handleGenerateStoryboard = async () => {
    setIsGenerating(true);
    setSaveMessage(null);
    try {
      if (activeTab === "storyboard") {
        const res = await fetchApi<any>("/scripts/generate", {
          method: "POST",
          body: JSON.stringify({
            title,
            topic,
            language: scriptLang,
            aspect_ratio: aspectRatio,
            target_scene_count: targetSceneCount,
            tone,
          }),
        });
        setScenes(res.scenes || []);
      } else {
        const res = await fetchApi<any>("/scripts/story", {
          method: "POST",
          body: JSON.stringify({
            premise: topic || title,
            language: scriptLang,
            character_count: 2,
            tone,
          }),
        });
        setCharacters(res.characters || []);
        // Transform dialogue scenes to storyboard scenes
        const converted: SceneItem[] = (res.dialogue_scenes || []).map((d: any, idx: number) => ({
          scene_order: idx + 1,
          script_text: `${d.speaker} Dialogue`,
          narration_text: d.line,
          visual_prompt: d.visual_prompt,
          duration_seconds: d.duration_seconds || 5.5,
          character_name: d.speaker,
        }));
        setScenes(converted);
      }
    } catch (err: any) {
      alert(`Generation failed: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSceneChange = (index: number, field: keyof SceneItem, value: any) => {
    setScenes((prev) => {
      const copy = [...prev];
      copy[index] = { ...copy[index], [field]: value };
      return copy;
    });
  };

  const handleAddScene = () => {
    const nextOrder = scenes.length + 1;
    setScenes((prev) => [
      ...prev,
      {
        scene_order: nextOrder,
        script_text: `Scene ${nextOrder} outline`,
        narration_text: "",
        visual_prompt: `Visual frame for scene ${nextOrder}, ${aspectRatio}, cinematic 8k`,
        duration_seconds: 6.0,
      },
    ]);
  };

  const handleRemoveScene = (index: number) => {
    setScenes((prev) => prev.filter((_, idx) => idx !== index));
  };

  // Export JSON Storyboard
  const handleExportJson = () => {
    const exportData = {
      title,
      topic,
      language: scriptLang,
      aspect_ratio: aspectRatio,
      total_scenes: scenes.length,
      estimated_total_duration: scenes.reduce((a, b) => a + (b.duration_seconds || 6), 0),
      scenes,
      exported_at: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `storyboard_${title.toLowerCase().replace(/[^a-z0-9]/g, "_")}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const totalDuration = scenes.reduce((a, b) => a + (b.duration_seconds || 6), 0);

  return (
    <div className="space-y-8">
      {/* Studio Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-red-600 dark:text-red-400">
            <FileText className="w-4 h-4" />
            <span>Module 3 &bull; Creative Studio</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white mt-1">
            {t.scriptsStudio.title}
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            {t.scriptsStudio.subtitle}
          </p>
        </div>

        {/* Global Action Buttons */}
        <div className="flex items-center space-x-2">
          {saveMessage && (
            <span className="text-xs text-emerald-500 font-semibold flex items-center space-x-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>{saveMessage}</span>
            </span>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportJson}
            disabled={scenes.length === 0}
            className="text-xs flex items-center space-x-1"
          >
            <Download className="w-3.5 h-3.5" />
            <span>{t.scriptsStudio.exportJson}</span>
          </Button>
        </div>
      </div>

      {/* Mode Selector Tabs (Storyboard vs Character Dialogue) */}
      <div className="flex border-b border-slate-200 dark:border-studio-800">
        <button
          onClick={() => setActiveTab("storyboard")}
          className={`px-4 py-2.5 text-sm font-semibold border-b-2 flex items-center space-x-2 transition-all ${
            activeTab === "storyboard"
              ? "border-red-600 text-red-600 dark:text-red-400"
              : "border-transparent text-slate-500 hover:text-slate-900 dark:hover:text-slate-300"
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>{t.scriptsStudio.modeStoryboard}</span>
        </button>

        <button
          onClick={() => setActiveTab("dialogue")}
          className={`px-4 py-2.5 text-sm font-semibold border-b-2 flex items-center space-x-2 transition-all ${
            activeTab === "dialogue"
              ? "border-red-600 text-red-600 dark:text-red-400"
              : "border-transparent text-slate-500 hover:text-slate-900 dark:hover:text-slate-300"
          }`}
        >
          <Users className="w-4 h-4" />
          <span>{t.scriptsStudio.modeDialogue}</span>
        </button>
      </div>

      {/* Script Generation Control Card */}
      <Card className="p-5 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label={t.projects.projectTitle}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. 5 Mind-Blowing AI Breakthroughs or అంతరిక్ష రహస్యాలు"
          />

          <Input
            label={t.projects.topic}
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Key narrative premise or topic outline..."
          />
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {/* Format */}
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
              Format
            </label>
            <div className="flex bg-slate-100 dark:bg-studio-950 p-1 rounded-lg border border-slate-200 dark:border-studio-800 text-xs">
              <button
                type="button"
                onClick={() => {
                  setAspectRatio("16:9");
                  if (targetSceneCount < 5) setTargetSceneCount(5);
                }}
                className={`flex-1 py-1 rounded text-center transition-all ${
                  aspectRatio === "16:9"
                    ? "bg-white dark:bg-studio-800 font-bold text-red-600 dark:text-red-400 shadow-xs"
                    : "text-slate-500"
                }`}
              >
                16:9 Long
              </button>
              <button
                type="button"
                onClick={() => {
                  setAspectRatio("9:16");
                  if (targetSceneCount > 5) setTargetSceneCount(3);
                }}
                className={`flex-1 py-1 rounded text-center transition-all ${
                  aspectRatio === "9:16"
                    ? "bg-white dark:bg-studio-800 font-bold text-purple-600 dark:text-purple-400 shadow-xs"
                    : "text-slate-500"
                }`}
              >
                9:16 Short
              </button>
            </div>
          </div>

          {/* Language */}
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
              {t.projects.filterLanguage}
            </label>
            <select
              value={scriptLang}
              onChange={(e) => setScriptLang(e.target.value as "en" | "te")}
              className="w-full px-3 py-2 text-xs rounded-lg bg-slate-50 dark:bg-studio-950/80 border border-slate-300 dark:border-studio-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-red-500"
            >
              <option value="en">English (Kokoro TTS)</option>
              <option value="te">తెలుగు / Telugu (Edge-TTS)</option>
            </select>
          </div>

          {/* Tone */}
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
              Tone Style
            </label>
            <select
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-lg bg-slate-50 dark:bg-studio-950/80 border border-slate-300 dark:border-studio-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-red-500"
            >
              <option value="engaging">Cinematic &amp; Engaging</option>
              <option value="dramatic">Dramatic &amp; Mysterious</option>
              <option value="urgent">Urgent &amp; Fast-Paced (Shorts)</option>
              <option value="educational">Educational &amp; Clear</option>
            </select>
          </div>

          {/* Target Scene Count */}
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
              Scenes: <span className="text-red-600 font-bold">{targetSceneCount}</span>
            </label>
            <input
              type="range"
              min={2}
              max={aspectRatio === "9:16" ? 6 : 10}
              value={targetSceneCount}
              onChange={(e) => setTargetSceneCount(parseInt(e.target.value, 10))}
              className="w-full accent-red-600 cursor-pointer mt-2"
            />
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <Button
            onClick={handleGenerateStoryboard}
            isLoading={isGenerating}
            className="flex items-center space-x-1.5 font-semibold text-xs"
          >
            <Sparkles className="w-4 h-4" />
            <span>
              {isGenerating ? t.scriptsStudio.generating : t.scriptsStudio.generateButton}
            </span>
          </Button>
        </div>
      </Card>

      {/* Character Cast Display (If in Dialogue mode or characters generated) */}
      {activeTab === "dialogue" && characters.length > 0 && (
        <Card className="p-5 space-y-3">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center space-x-2">
            <Users className="w-4 h-4 text-purple-500" />
            <span>{t.scriptsStudio.charactersTitle}</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {characters.map((char, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl bg-slate-50 dark:bg-studio-950/60 border border-slate-200 dark:border-studio-800 space-y-1"
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-slate-900 dark:text-white">
                    {char.name}
                  </span>
                  <Badge variant="purple">{char.role}</Badge>
                </div>
                <p className="text-xs text-slate-500">{char.voice_style}</p>
                <p className="text-[11px] font-mono text-slate-400 pt-1 line-clamp-1">
                  Prompt: {char.visual_prompt}
                </p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Scene-by-Scene Timeline & Storyboard Editor */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center space-x-2">
              <Layers className="w-4 h-4 text-red-600" />
              <span>{t.scenes.sceneBreakdown}</span>
            </h3>
            <span className="px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 dark:bg-studio-800 text-slate-600 dark:text-slate-300">
              {scenes.length} {t.projects.scenes} &bull; {formatDuration(totalDuration)}
            </span>
          </div>

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

        {/* Scene Cards Stack */}
        <div className="space-y-4">
          {scenes.map((scene, idx) => (
            <Card key={idx} className="space-y-3 p-4 sm:p-5">
              <div className="flex items-center justify-between border-b border-slate-100 dark:border-studio-800 pb-2.5">
                <div className="flex items-center space-x-2">
                  <span className="w-6 h-6 rounded-md bg-red-100 dark:bg-red-950/60 text-red-600 dark:text-red-400 font-bold text-xs flex items-center justify-center">
                    {scene.scene_order || idx + 1}
                  </span>
                  <span className="text-xs font-bold text-slate-900 dark:text-white">
                    {scene.character_name ? `${scene.character_name} Shot` : `${t.scenes.scene} ${idx + 1}`}
                  </span>
                </div>

                <div className="flex items-center space-x-3">
                  <div className="flex items-center space-x-1.5 text-xs text-slate-500">
                    <Clock className="w-3.5 h-3.5" />
                    <input
                      type="number"
                      step="0.5"
                      min="2"
                      max="30"
                      value={scene.duration_seconds}
                      onChange={(e) =>
                        handleSceneChange(idx, "duration_seconds", parseFloat(e.target.value) || 6.0)
                      }
                      className="w-14 px-1.5 py-0.5 text-xs rounded border border-slate-200 dark:border-studio-700 bg-slate-50 dark:bg-studio-950 text-center font-semibold"
                    />
                    <span>sec</span>
                  </div>

                  <button
                    onClick={() => handleRemoveScene(idx)}
                    className="p-1 text-slate-400 hover:text-rose-500 transition-colors"
                    title="Remove Scene"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Script Outline */}
              <div>
                <label className="block text-[11px] font-semibold uppercase text-slate-400 mb-1">
                  {t.scenes.scriptText}
                </label>
                <input
                  type="text"
                  value={scene.script_text}
                  onChange={(e) => handleSceneChange(idx, "script_text", e.target.value)}
                  className="w-full px-3 py-1.5 text-xs rounded-lg bg-slate-50 dark:bg-studio-950/70 border border-slate-200 dark:border-studio-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-red-500"
                />
              </div>

              {/* Spoken Voiceover Narration */}
              <div>
                <label className="block text-[11px] font-semibold uppercase text-slate-400 mb-1">
                  {t.scenes.narrationText} ({scriptLang === "te" ? "తెలుగు వాయిస్" : "English Audio"})
                </label>
                <textarea
                  rows={2}
                  value={scene.narration_text}
                  onChange={(e) => handleSceneChange(idx, "narration_text", e.target.value)}
                  className="w-full px-3 py-1.5 text-xs rounded-lg bg-slate-50 dark:bg-studio-950/70 border border-slate-200 dark:border-studio-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-red-500 resize-none font-medium"
                />
              </div>

              {/* Visual Prompt in English */}
              <div>
                <label className="block text-[11px] font-semibold uppercase text-slate-400 mb-1">
                  {t.scenes.visualPrompt} (English Image Generator Description)
                </label>
                <input
                  type="text"
                  value={scene.visual_prompt}
                  onChange={(e) => handleSceneChange(idx, "visual_prompt", e.target.value)}
                  className="w-full px-3 py-1.5 text-xs rounded-lg bg-slate-50 dark:bg-studio-950/70 border border-slate-200 dark:border-studio-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-red-500 font-mono text-[11px]"
                />
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function ScriptStudioPage() {
  return (
    <Suspense fallback={<div className="py-20 text-center text-xs text-slate-500">Loading Script Studio...</div>}>
      <ScriptStudioContent />
    </Suspense>
  );
}
