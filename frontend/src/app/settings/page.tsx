"use client";

import React, { useEffect, useState } from "react";
import { HardDrive, Globe, RefreshCw, Cpu, Activity, ShieldCheck, Sparkles } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { ProviderCard, ProviderData } from "@/components/settings/ProviderCard";
import { useTranslation } from "@/lib/i18n";
import { fetchApi } from "@/lib/api";

export default function SettingsPage() {
  const { t } = useTranslation();
  const [providers, setProviders] = useState<ProviderData[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadSettingsData = async () => {
    try {
      setIsLoading(true);
      const [provData, statsData] = await Promise.all([
        fetchApi<ProviderData[]>("/providers").catch(() => []),
        fetchApi<any>("/stats").catch(() => null),
      ]);
      setProviders(provData);
      setStats(statsData);
    } catch (err) {
      console.error("Failed to load settings data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSettingsData();
  }, []);

  const localProviders = providers.filter((p) => p.execution_mode === "local");
  const cloudProviders = providers.filter((p) => p.execution_mode === "cloud");

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            {t.providers.title}
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            {t.providers.subtitle}
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={loadSettingsData}
          isLoading={isLoading}
          className="flex items-center space-x-1.5 self-start sm:self-auto text-xs"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>{t.common.refresh}</span>
        </Button>
      </div>

      {/* Hardware Diagnostic Banner */}
      <Card className="bg-gradient-to-r from-slate-900 via-studio-950 to-studio-900 text-white border-studio-800 p-6">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="space-y-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 flex items-center space-x-1">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Hardware Execution Profile</span>
            </span>
            <h3 className="text-lg font-bold">
              Windows 11 Sequential Processing Engine
            </h3>
            <p className="text-xs text-slate-400 max-w-xl">
              Strict memory guard enabled: Only one AI inference model executes in RAM at any moment. Large models are never downloaded without explicit approval.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="px-3 py-2 rounded-xl bg-studio-800/80 border border-studio-700 text-center">
              <span className="text-[10px] text-slate-400 uppercase font-semibold block">Total RAM</span>
              <span className="text-sm font-bold text-white">{stats?.system_memory_total_gb || 16.0} GB</span>
            </div>
            <div className="px-3 py-2 rounded-xl bg-studio-800/80 border border-studio-700 text-center">
              <span className="text-[10px] text-emerald-400 uppercase font-semibold block">Free RAM</span>
              <span className="text-sm font-bold text-emerald-400">{stats?.system_memory_free_gb || 4.5} GB</span>
            </div>
            <div className="px-3 py-2 rounded-xl bg-studio-800/80 border border-studio-700 text-center">
              <span className="text-[10px] text-slate-400 uppercase font-semibold block">Platform</span>
              <span className="text-sm font-bold text-white">{stats?.system_platform || "Windows 11"}</span>
            </div>
          </div>
        </div>
      </Card>

      {/* Section 1: Local AI Engines */}
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <div className="w-7 h-7 rounded-lg bg-emerald-100 text-emerald-600 dark:bg-emerald-950/60 dark:text-emerald-400 flex items-center justify-center">
            <HardDrive className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              {t.providers.localEngines}
            </h3>
            <p className="text-xs text-slate-500">
              Low-footprint local inference daemons running directly on this workstation
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {localProviders.map((provider) => (
            <ProviderCard
              key={provider.provider_key}
              provider={provider}
              onRefresh={loadSettingsData}
            />
          ))}
        </div>
      </div>

      {/* Section 2: Cloud Fallback Providers */}
      <div className="space-y-4 pt-4 border-t border-slate-200 dark:border-studio-800/80">
        <div className="flex items-center space-x-2">
          <div className="w-7 h-7 rounded-lg bg-blue-100 text-blue-600 dark:bg-blue-950/60 dark:text-blue-400 flex items-center justify-center">
            <Globe className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              {t.providers.cloudProviders}
            </h3>
            <p className="text-xs text-slate-500">
              Optional cloud APIs for high-speed fallback and production distribution
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {cloudProviders.map((provider) => (
            <ProviderCard
              key={provider.provider_key}
              provider={provider}
              onRefresh={loadSettingsData}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
