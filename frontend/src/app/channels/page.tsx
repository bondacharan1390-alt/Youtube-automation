"use client";

import React, { useState, useEffect } from "react";
import {
  Radio,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  ShieldCheck,
  RefreshCw,
  HardDrive,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useTranslation } from "@/lib/i18n";
import { fetchApi } from "@/lib/api";

interface ChannelItem {
  id: string;
  channel_name: string;
  youtube_channel_id: string | null;
  custom_url: string | null;
  thumbnail_url: string | null;
  is_connected: boolean;
  quota_units_used_today: number;
  quota_limit_daily: number;
  created_at: string;
}

interface OAuthInfo {
  auth_url: string;
  client_id_configured: boolean;
  instructions: string;
}

export default function ChannelManagerPage() {
  const { t } = useTranslation();
  const [channels, setChannels] = useState<ChannelItem[]>([]);
  const [oauthInfo, setOauthInfo] = useState<OAuthInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchApi("/youtube/channels"),
      fetchApi("/youtube/oauth/url"),
    ])
      .then(([chans, auth]: [unknown, unknown]) => {
        if (Array.isArray(chans)) setChannels(chans as ChannelItem[]);
        if (auth && typeof auth === "object") setOauthInfo(auth as OAuthInfo);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-4 md:p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <Radio className="w-6 h-6 text-red-500" />
          {t.channelManager.title}
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {t.channelManager.subtitle}
        </p>
      </div>

      {/* Security & Token Banner */}
      <Card className="p-4 bg-slate-900 text-white border-slate-800">
        <div className="flex items-start gap-3">
          <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
          <div className="text-xs space-y-1">
            <p className="font-semibold text-emerald-400">
              Zero-Exposure OAuth 2.0 Security
            </p>
            <p className="text-slate-300">
              Refresh tokens and access credentials are never sent to the browser.
              All credentials are encrypted with server-side Fernet AES-256 ciphers.
            </p>
          </div>
        </div>
      </Card>

      {/* Connected Channels List */}
      <div className="space-y-4">
        <h2 className="text-base font-semibold text-gray-900 dark:text-white">
          {t.channelManager.connectedChannels}
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {channels.map((ch) => (
            <Card key={ch.id} className="p-5 space-y-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-red-600 flex items-center justify-center text-white font-bold text-lg">
                    {ch.channel_name.charAt(0)}
                  </div>
                  <div>
                    <h3 className="font-bold text-gray-900 dark:text-white text-base">
                      {ch.channel_name}
                    </h3>
                    <p className="text-xs text-gray-500">
                      ID: {ch.youtube_channel_id || "Linked Studio Channel"}
                    </p>
                  </div>
                </div>
                <Badge variant={ch.is_connected ? "success" : "warning"}>
                  {ch.is_connected
                    ? t.channelManager.statusConnected
                    : t.channelManager.statusDisconnected}
                </Badge>
              </div>

              {/* Quota Progress */}
              <div className="space-y-1.5 pt-2 border-t border-gray-200 dark:border-gray-800">
                <div className="flex justify-between text-xs text-gray-500">
                  <span>{t.channelManager.quotaUsed}:</span>
                  <span className="font-semibold text-gray-800 dark:text-gray-200">
                    {ch.quota_units_used_today.toLocaleString()} /{" "}
                    {ch.quota_limit_daily.toLocaleString()} units
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-red-500 h-full rounded-full transition-all"
                    style={{
                      width: `${Math.min(
                        100,
                        (ch.quota_units_used_today / ch.quota_limit_daily) * 100
                      )}%`,
                    }}
                  />
                </div>
              </div>
            </Card>
          ))}
        </div>

        {/* OAuth Link Card */}
        <Card className="p-6 border-dashed border-2 text-center space-y-3">
          <Radio className="w-10 h-10 text-gray-400 mx-auto" />
          <h3 className="text-base font-bold text-gray-800 dark:text-gray-200">
            {t.channelManager.connectNewChannel}
          </h3>
          <p className="text-xs text-gray-500 max-w-md mx-auto">
            {oauthInfo?.instructions ||
              "Authorize access to your YouTube channel to enable 1-click uploads and analytics."}
          </p>

          {oauthInfo?.client_id_configured ? (
            <a
              href={oauthInfo.auth_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-red-600 hover:bg-red-700 text-white font-medium text-sm transition-colors"
            >
              <ExternalLink className="w-4 h-4" />
              Sign in with Google OAuth
            </a>
          ) : (
            <Badge variant="warning">
              Configure YOUTUBE_CLIENT_ID in Settings to enable live OAuth link
            </Badge>
          )}
        </Card>
      </div>
    </div>
  );
}
