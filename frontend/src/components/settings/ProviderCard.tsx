"use client";

import React, { useState } from "react";
import { CheckCircle2, AlertCircle, Key, Activity, Globe, HardDrive } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { fetchApi } from "@/lib/api";

export interface ProviderData {
  id: string;
  provider_key: string;
  name: string;
  category: string;
  execution_mode: "local" | "cloud";
  is_active: boolean;
  is_healthy: boolean;
  has_api_key: boolean;
  base_url?: string;
  health_status_message?: string;
  settings_json?: Record<string, any>;
}

interface ProviderCardProps {
  provider: ProviderData;
  onRefresh: () => void;
}

export const ProviderCard: React.FC<ProviderCardProps> = ({ provider, onRefresh }) => {
  const [isEditingKey, setIsEditingKey] = useState(false);
  const [apiKey, setApiKey] = useState("");
  const [isPinging, setIsPinging] = useState(false);
  const [pingMessage, setPingMessage] = useState<string | null>(null);
  const [modelPath, setModelPath] = useState(
    provider.settings_json?.model_path || "kling-video/v4.0/image-to-video"
  );
  const [prompt, setPrompt] = useState("");
  const [imageUrl, setImageUrl] = useState("");
  const [generation, setGeneration] = useState<any>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const handlePing = async () => {
    setIsPinging(true);
    setPingMessage(null);
    try {
      const res = await fetchApi<any>(`/providers/${provider.provider_key}/check-health`, {
        method: "POST",
      });
      setPingMessage(`${res.message} (${res.latency_ms}ms)`);
      onRefresh();
    } catch (err: any) {
      setPingMessage(`Check failed: ${err.message}`);
    } finally {
      setIsPinging(false);
    }
  };

  const handleSaveKey = async () => {
    try {
      await fetchApi(`/providers/${provider.provider_key}`, {
        method: "PUT",
        body: JSON.stringify({ api_key: apiKey }),
      });
      setIsEditingKey(false);
      setApiKey("");
      onRefresh();
    } catch (err: any) {
      alert(`Failed to save key: ${err.message}`);
    }
  };

  const handleToggleActive = async () => {
    try {
      await fetchApi(`/providers/${provider.provider_key}`, {
        method: "PUT",
        body: JSON.stringify({ is_active: !provider.is_active }),
      });
      onRefresh();
    } catch (err: any) {
      alert(`Failed to update provider: ${err.message}`);
    }
  };

  const handleSaveModel = async () => {
    try {
      await fetchApi(`/providers/${provider.provider_key}`, {
        method: "PUT",
        body: JSON.stringify({
          settings_json: { ...(provider.settings_json || {}), model_path: modelPath.trim() },
        }),
      });
      onRefresh();
    } catch (err: any) {
      alert(`Failed to save model: ${err.message}`);
    }
  };

  const handleGenerate = async () => {
    if (!imageUrl.trim()) {
      alert("Enter a publicly reachable image URL for the first frame.");
      return;
    }
    setIsGenerating(true);
    try {
      const result = await fetchApi<any>("/higgsfield/generations", {
        method: "POST",
        body: JSON.stringify({
          model_path: modelPath.trim(),
          operation: "image_to_video",
          payload: { image_url: imageUrl.trim(), prompt: prompt.trim() || undefined, duration: 5, resolution: "720p" },
        }),
      });
      setGeneration(result);
    } catch (err: any) {
      alert(`Higgsfield submission failed: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const refreshGeneration = async () => {
    if (!generation?.id) return;
    try {
      const result = await fetchApi<any>(`/higgsfield/generations/${generation.id}`);
      setGeneration(result);
    } catch (err: any) {
      setPingMessage(`Status check failed: ${err.message}`);
    }
  };

  const cancelGeneration = async () => {
    if (!generation?.id) return;
    try {
      const result = await fetchApi<any>(`/higgsfield/generations/${generation.id}/cancel`, { method: "POST" });
      setGeneration(result);
    } catch (err: any) {
      setPingMessage(`Cancellation failed: ${err.message}`);
    }
  };

  const isLocal = provider.execution_mode === "local";

  return (
    <Card className="flex flex-col justify-between">
      <div>
        {/* Header: Mode, Category, Health */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <span
              className={`p-1 rounded-md text-xs font-semibold flex items-center space-x-1 ${
                isLocal
                  ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300"
                  : "bg-blue-50 text-blue-700 dark:bg-blue-950/50 dark:text-blue-300"
              }`}
            >
              {isLocal ? <HardDrive className="w-3.5 h-3.5" /> : <Globe className="w-3.5 h-3.5" />}
              <span>{isLocal ? "Local Engine" : "Cloud API"}</span>
            </span>
            <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
              {provider.category}
            </span>
          </div>

          {provider.is_healthy ? (
            <Badge variant="success" className="flex items-center space-x-1">
              <CheckCircle2 className="w-3 h-3" />
              <span>Healthy</span>
            </Badge>
          ) : (
            <Badge variant="warning" className="flex items-center space-x-1">
              <AlertCircle className="w-3 h-3" />
              <span>Pending</span>
            </Badge>
          )}
        </div>

        {/* Title */}
        <h4 className="text-base font-semibold text-slate-900 dark:text-white">
          {provider.name}
        </h4>

        {/* Health status message or latency */}
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 min-h-[32px]">
          {pingMessage || provider.health_status_message || "Ready for operation"}
        </p>

        {/* Endpoint info */}
        {provider.base_url && (
          <p className="text-[11px] font-mono text-slate-400 truncate mt-2 bg-slate-50 dark:bg-studio-950/60 p-1.5 rounded border border-slate-200/60 dark:border-studio-800">
            {provider.base_url}
          </p>
        )}
        {provider.provider_key === "higgsfield" && (
          <div className="mt-3 space-y-1.5">
            <label className="text-[11px] font-semibold text-slate-500">Documented model path</label>
            <div className="flex gap-2">
              <Input value={modelPath} onChange={(e) => setModelPath(e.target.value)} />
              <Button size="sm" variant="outline" onClick={handleSaveModel}>Save</Button>
            </div>
            <p className="text-[10px] text-amber-600 dark:text-amber-400">Generation may consume prepaid API balance.</p>
            <div className="pt-2 border-t border-slate-200 dark:border-studio-800 space-y-2">
              <label className="text-[11px] font-semibold text-slate-500">Image-to-video test input</label>
              <Input value={imageUrl} onChange={(e) => setImageUrl(e.target.value)} placeholder="Public first-frame image URL" />
              <Input value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="Optional motion prompt" />
              <div className="flex items-center gap-2">
                <Button size="sm" onClick={handleGenerate} isLoading={isGenerating}>Submit billable job</Button>
                {generation && <Button size="sm" variant="outline" onClick={refreshGeneration}>Refresh status</Button>}
                {generation && !["completed", "failed", "nsfw", "canceled"].includes(generation.status) && (
                  <Button size="sm" variant="ghost" onClick={cancelGeneration}>Cancel</Button>
                )}
              </div>
              {generation && (
                <p className="text-[10px] text-slate-500 break-all">
                  Status: {generation.status}{generation.output_url ? ` • ${generation.output_url}` : ""}
                </p>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Action footer */}
      <div className="mt-4 pt-3 border-t border-slate-100 dark:border-studio-800/80 space-y-2">
        {isEditingKey ? (
          <div className="space-y-2">
            <Input
              type="password"
              placeholder="Paste API Key..."
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
            />
            <div className="flex items-center justify-end space-x-2">
              <Button size="sm" variant="ghost" onClick={() => setIsEditingKey(false)}>
                Cancel
              </Button>
              <Button size="sm" onClick={handleSaveKey}>
                Save Key
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-between">
            {!isLocal ? (
              <button
                onClick={() => setIsEditingKey(true)}
                className="text-xs text-slate-500 hover:text-slate-900 dark:hover:text-slate-200 flex items-center space-x-1"
              >
                <Key className="w-3.5 h-3.5" />
                <span>{provider.has_api_key ? "Update Key" : "Set API Key"}</span>
              </button>
            ) : (
              <span className="text-[11px] text-slate-400">Zero-API-Key Local</span>
            )}

            <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={handleToggleActive}
              className="text-xs"
            >
              {provider.is_active ? "Disable" : "Enable"}
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={handlePing}
              isLoading={isPinging}
              className="text-xs flex items-center space-x-1"
            >
              <Activity className="w-3.5 h-3.5" />
              <span>Ping</span>
            </Button>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};
