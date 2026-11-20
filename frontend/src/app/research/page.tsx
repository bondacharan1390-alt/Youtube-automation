"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  Sparkles,
  TrendingUp,
  Target,
  Key,
  Film,
  Smartphone,
  ArrowRight,
  Lightbulb,
  CheckCircle2,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { useTranslation } from "@/lib/i18n";
import { fetchApi } from "@/lib/api";

interface TopicAnalysisData {
  topic: string;
  language: string;
  virality_score: number;
  audience_persona: string;
  search_intent: string;
  hook_angles: string[];
  primary_keywords: string[];
  long_tail_keywords: string[];
  recommended_video_length: string;
}

interface VideoIdeaItem {
  title: string;
  angle: string;
  hook: string;
  estimated_ctr: string;
  format: string;
}

export default function ResearchStudioPage() {
  const router = useRouter();
  const { t, language } = useTranslation();

  const [topicInput, setTopicInput] = useState("");
  const [selectedLang, setSelectedLang] = useState<"en" | "te">(language);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<TopicAnalysisData | null>(null);
  const [ideas, setIdeas] = useState<VideoIdeaItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!topicInput.trim()) return;

    setIsAnalyzing(true);
    setError(null);

    try {
      const [analysisRes, ideasRes] = await Promise.all([
        fetchApi<TopicAnalysisData>("/research/analyze", {
          method: "POST",
          body: JSON.stringify({ topic: topicInput, language: selectedLang }),
        }),
        fetchApi<{ ideas: VideoIdeaItem[] }>("/research/ideas", {
          method: "POST",
          body: JSON.stringify({ seed_keyword: topicInput, language: selectedLang }),
        }),
      ]);

      setAnalysis(analysisRes);
      setIdeas(ideasRes.ideas || []);
    } catch (err: any) {
      setError(err.message || "Analysis failed");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSendToScript = (title: string, format: string) => {
    const query = new URLSearchParams({
      title,
      topic: topicInput,
      language: selectedLang,
      aspect_ratio: format === "9:16" ? "9:16" : "16:9",
    });
    router.push(`/scripts?${query.toString()}`);
  };

  return (
    <div className="space-y-8">
      {/* Studio Header */}
      <div>
        <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-red-600 dark:text-red-400">
          <Search className="w-4 h-4" />
          <span>Module 2 &bull; Intelligence Studio</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white mt-1">
          {t.research.title}
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
          {t.research.subtitle}
        </p>
      </div>

      {/* Search & Topic Input Bar */}
      <Card className="p-4 sm:p-5 shadow-sm">
        <form onSubmit={handleAnalyze} className="space-y-3">
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            <div className="relative flex-1">
              <Search className="w-5 h-5 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={topicInput}
                onChange={(e) => setTopicInput(e.target.value)}
                placeholder={t.research.topicInputPlaceholder}
                className="w-full pl-11 pr-4 py-2.5 text-sm rounded-xl bg-slate-50 dark:bg-studio-950/80 border border-slate-300 dark:border-studio-700 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-red-500"
              />
            </div>

            {/* Language Selector */}
            <div className="flex bg-slate-100 dark:bg-studio-950 p-1 rounded-xl border border-slate-200 dark:border-studio-800 text-xs font-semibold shrink-0">
              <button
                type="button"
                onClick={() => setSelectedLang("en")}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  selectedLang === "en"
                    ? "bg-white dark:bg-studio-800 text-slate-900 dark:text-white shadow-xs font-bold"
                    : "text-slate-500 hover:text-slate-900 dark:hover:text-slate-200"
                }`}
              >
                English
              </button>
              <button
                type="button"
                onClick={() => setSelectedLang("te")}
                className={`px-3 py-1.5 rounded-lg transition-all ${
                  selectedLang === "te"
                    ? "bg-white dark:bg-studio-800 text-red-600 dark:text-red-400 shadow-xs font-bold"
                    : "text-slate-500 hover:text-slate-900 dark:hover:text-slate-200"
                }`}
              >
                తెలుగు
              </button>
            </div>

            {/* Analyze Trigger */}
            <Button
              type="submit"
              isLoading={isAnalyzing}
              className="flex items-center space-x-1.5 shrink-0"
            >
              <Sparkles className="w-4 h-4" />
              <span>{isAnalyzing ? t.research.generating : t.research.analyzeButton}</span>
            </Button>
          </div>

          {/* Quick preset chips */}
          <div className="flex flex-wrap items-center gap-2 pt-1 text-xs text-slate-500">
            <span className="font-semibold text-slate-400">Trending Prompts:</span>
            {[
              "5 Mind-Blowing AI Inventions in 2026",
              "జేమ్స్ వెబ్ టెలిస్కోప్ తాజా రహస్యాలు",
              "Quantum Computing Explained Simply",
              "భవిష్యత్తును మార్చే సూపర్ రోబోట్స్",
            ].map((preset, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setTopicInput(preset);
                  setSelectedLang(idx % 2 === 1 ? "te" : "en");
                }}
                className="px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-studio-800 hover:bg-slate-200 dark:hover:bg-studio-700 text-slate-700 dark:text-slate-300 transition-colors"
              >
                {preset}
              </button>
            ))}
          </div>
        </form>
      </Card>

      {error && (
        <div className="p-3 text-xs bg-rose-50 text-rose-600 dark:bg-rose-950/40 dark:text-rose-400 border border-rose-200 dark:border-rose-900 rounded-lg">
          {error}
        </div>
      )}

      {/* Analysis Results Display */}
      {analysis && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Virality Score Card */}
            <Card className="flex items-center space-x-4 p-5">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-red-600 to-amber-500 text-white flex flex-col items-center justify-center font-extrabold shadow-md shrink-0">
                <span className="text-xl leading-none">{analysis.virality_score}</span>
                <span className="text-[10px] uppercase font-bold opacity-80">/ 100</span>
              </div>
              <div>
                <span className="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400">
                  {t.research.viralityScore}
                </span>
                <p className="text-sm font-bold text-slate-900 dark:text-white mt-0.5">
                  {analysis.virality_score >= 80 ? "High Algorithmic Velocity" : "Moderate Virality"}
                </p>
                <span className="text-[11px] text-slate-500">
                  Optimal format: {analysis.recommended_video_length}
                </span>
              </div>
            </Card>

            {/* Target Persona Card */}
            <Card className="p-5 space-y-1">
              <span className="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400 flex items-center space-x-1">
                <Target className="w-3.5 h-3.5 text-blue-500" />
                <span>{t.research.audiencePersona}</span>
              </span>
              <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed pt-1">
                {analysis.audience_persona}
              </p>
            </Card>

            {/* Search Intent Card */}
            <Card className="p-5 space-y-1">
              <span className="text-xs font-semibold uppercase text-slate-500 dark:text-slate-400 flex items-center space-x-1">
                <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />
                <span>{t.research.searchIntent}</span>
              </span>
              <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed pt-1">
                {analysis.search_intent}
              </p>
            </Card>
          </div>

          {/* Hooks & Keywords Dual Column */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Hook Angles */}
            <Card className="space-y-3 p-5">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center space-x-2">
                <Lightbulb className="w-4 h-4 text-amber-500" />
                <span>{t.research.hookAngles}</span>
              </h3>
              <div className="space-y-2">
                {analysis.hook_angles.map((hook, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-slate-50 dark:bg-studio-950/60 border border-slate-200/60 dark:border-studio-800 text-xs text-slate-800 dark:text-slate-200 flex items-start space-x-2"
                  >
                    <span className="font-bold text-red-600 mt-0.5">#{idx + 1}</span>
                    <span className="leading-relaxed font-medium">&ldquo;{hook}&rdquo;</span>
                  </div>
                ))}
              </div>
            </Card>

            {/* Keywords Cloud */}
            <Card className="space-y-4 p-5">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center space-x-2">
                <Key className="w-4 h-4 text-purple-500" />
                <span>Keyword Clusters &amp; SEO Tags</span>
              </h3>

              <div className="space-y-2">
                <span className="text-[11px] font-semibold uppercase text-slate-400 block">
                  {t.research.primaryKeywords}
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {analysis.primary_keywords.map((kw, idx) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 rounded-md text-xs font-semibold bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-400 border border-red-200 dark:border-red-900"
                    >
                      #{kw}
                    </span>
                  ))}
                </div>
              </div>

              <div className="space-y-2 pt-2 border-t border-slate-100 dark:border-studio-800">
                <span className="text-[11px] font-semibold uppercase text-slate-400 block">
                  {t.research.longTailKeywords}
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {analysis.long_tail_keywords.map((kw, idx) => (
                    <span
                      key={idx}
                      className="px-2.5 py-1 rounded-md text-xs bg-slate-100 text-slate-700 dark:bg-studio-800 dark:text-slate-300"
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            </Card>
          </div>

          {/* 5 Video Idea Concepts */}
          <div className="space-y-4">
            <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center space-x-2">
              <Sparkles className="w-5 h-5 text-red-600" />
              <span>{t.research.videoIdeasTitle}</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {ideas.map((idea, idx) => (
                <Card key={idx} hoverable className="flex flex-col justify-between p-5 space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Badge variant="purple">{idea.angle}</Badge>
                      <span className="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">
                        Est. CTR: {idea.estimated_ctr}
                      </span>
                    </div>

                    <h4 className="text-sm font-bold text-slate-900 dark:text-white leading-snug">
                      {idea.title}
                    </h4>

                    <p className="text-xs text-slate-500 dark:text-slate-400 italic">
                      &ldquo;{idea.hook}&rdquo;
                    </p>
                  </div>

                  <div className="pt-3 border-t border-slate-100 dark:border-studio-800 flex items-center justify-between">
                    <span className="text-[11px] font-semibold text-slate-400 flex items-center space-x-1">
                      {idea.format === "9:16" ? (
                        <Smartphone className="w-3.5 h-3.5" />
                      ) : (
                        <Film className="w-3.5 h-3.5" />
                      )}
                      <span>{idea.format}</span>
                    </span>

                    <Button
                      size="sm"
                      onClick={() => handleSendToScript(idea.title, idea.format)}
                      className="text-xs flex items-center space-x-1"
                    >
                      <span>{t.research.sendToScript}</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
