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
        )}
      </div>
    </Card>
  );
};
