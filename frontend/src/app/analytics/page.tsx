"use client";

import React, { useState, useEffect } from "react";
import {
  BarChart3,
  Users,
  Eye,
  Video,
  Activity,
  CheckCircle2,
  Info,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { useTranslation } from "@/lib/i18n";
import { fetchApi } from "@/lib/api";

interface ChannelItem {
  id: string;
  channel_name: string;
}

interface AnalyticsData {
  channel_id: string;
  channel_name: string;
  subscriber_count: number | null;
  view_count: number | null;
  video_count: number;
  quota_units_used: number;
  is_live_data: boolean;
  metrics_notes: string;
  top_videos: Array<{
    title: string;
    aspect_ratio: string;
    status: string;
  }>;
  data_mode?: string;
  earliest_available_date?: string | null;
}

interface HistoryRow {
  date: string;
  views: number;
  estimated_minutes_watched: number;
  average_view_duration: number | null;
  subscribers_gained: number;
  subscribers_lost: number;
}

interface HistoryData {
  is_live_data: boolean;
  data_mode: string;
  start_date: string;
  end_date: string;
  earliest_available_date?: string | null;
  rows: HistoryRow[];
  error?: string | null;
  requires?: string[];
}

export default function AnalyticsDashboardPage() {
  const { t } = useTranslation();
  const [channels, setChannels] = useState<ChannelItem[]>([]);
  const [selectedChannelId, setSelectedChannelId] = useState("");
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<HistoryData | null>(null);
  const [insights, setInsights] = useState<any>(null);
  const [startDate, setStartDate] = useState(() => {
    const date = new Date();
    date.setDate(date.getDate() - 28);
    return date.toISOString().slice(0, 10);
  });
  const [endDate, setEndDate] = useState(() => new Date().toISOString().slice(0, 10));

  useEffect(() => {
    fetchApi("/youtube/channels")
      .then((d: unknown) => {
        if (Array.isArray(d)) {
          setChannels(d as ChannelItem[]);
          if (d.length > 0) {
            setSelectedChannelId(d[0].id);
          }
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!selectedChannelId) return;
    setLoading(true);
    fetchApi(`/youtube/analytics/${selectedChannelId}`)
      .then((d: unknown) => setAnalytics(d as AnalyticsData))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [selectedChannelId]);

  useEffect(() => {
    if (!selectedChannelId || !startDate || !endDate) return;
    fetchApi<HistoryData>(`/youtube/analytics/${selectedChannelId}/history?start_date=${startDate}&end_date=${endDate}`)
      .then(setHistory)
      .catch(() => setHistory(null));
  }, [selectedChannelId, startDate, endDate]);

  const generateInsights = async () => {
    if (!selectedChannelId) return;
    try {
      const data = await fetchApi<any>(
        `/youtube/analytics/${selectedChannelId}/insights?start_date=${startDate}&end_date=${endDate}`,
        { method: "POST" }
      );
      setInsights(data);
    } catch (error) {
      console.error(error);
    }
  };

  const downloadReport = async (format: "csv" | "pdf") => {
    if (!selectedChannelId) return;
    const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
    const token = localStorage.getItem("studio_token");
    const response = await fetch(
      `${base}/youtube/analytics/${selectedChannelId}/export/${format}?start_date=${startDate}&end_date=${endDate}`,
      { headers: token ? { Authorization: `Bearer ${token}` } : {} }
    );
    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: "Export failed" }));
      alert(body.detail || "Export failed");
      return;
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `channel-${selectedChannelId}-${startDate}-to-${endDate}.${format}`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-4 md:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-indigo-500" />
            {t.analyticsDashboard.title}
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {t.analyticsDashboard.subtitle}
          </p>
        </div>

        {channels.length > 0 && (
          <div className="flex flex-wrap gap-2">
            <select
              value={selectedChannelId}
              onChange={(e) => setSelectedChannelId(e.target.value)}
              className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-3 py-2 text-sm outline-none font-medium"
            >
              {channels.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.channel_name}
                </option>
              ))}
            </select>
            <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="rounded-lg border px-3 py-2 text-sm dark:bg-gray-800" />
            <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="rounded-lg border px-3 py-2 text-sm dark:bg-gray-800" />
            <button onClick={() => downloadReport("csv")} className="rounded-lg border px-3 py-2 text-sm font-medium">CSV</button>
            <button onClick={() => downloadReport("pdf")} className="rounded-lg border px-3 py-2 text-sm font-medium">PDF</button>
          </div>
        )}
      </div>

      {/* Honest Data Notice Banner */}
      <div className="p-3.5 rounded-xl bg-slate-900 text-white border border-slate-800 flex items-center gap-3 text-xs">
        <Info className="w-4 h-4 text-indigo-400 shrink-0" />
        <span className="text-slate-300">
          {analytics?.is_live_data
            ? t.analyticsDashboard.liveNotice
            : analytics?.metrics_notes || t.analyticsDashboard.localNotice}
        </span>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-5 space-y-2">
          <div className="flex items-center justify-between text-gray-500 text-xs font-semibold">
            <span>{t.analyticsDashboard.subscribers}</span>
            <Users className="w-4 h-4 text-indigo-500" />
          </div>
          <p className="text-2xl font-extrabold text-gray-900 dark:text-white">
            {analytics?.subscriber_count == null ? "Not available" : analytics.subscriber_count.toLocaleString()}
          </p>
          <span className="text-[11px] text-gray-500">
            {analytics?.subscriber_count === null ? "Live subscribers unavailable" : "YouTube Data API value"}
          </span>
        </Card>

        <Card className="p-5 space-y-2">
          <div className="flex items-center justify-between text-gray-500 text-xs font-semibold">
            <span>{t.analyticsDashboard.totalViews}</span>
            <Eye className="w-4 h-4 text-blue-500" />
          </div>
          <p className="text-2xl font-extrabold text-gray-900 dark:text-white">
            {analytics?.view_count == null ? "Not available" : analytics.view_count.toLocaleString()}
          </p>
          <span className="text-[11px] text-gray-500">
            {analytics?.view_count === null ? "Live views unavailable" : "YouTube Data API value"}
          </span>
        </Card>

        <Card className="p-5 space-y-2">
          <div className="flex items-center justify-between text-gray-500 text-xs font-semibold">
            <span>{t.analyticsDashboard.videosPublished}</span>
            <Video className="w-4 h-4 text-rose-500" />
          </div>
          <p className="text-2xl font-extrabold text-gray-900 dark:text-white">
            {analytics ? analytics.video_count : "..."}
          </p>
          <span className="text-[11px] text-gray-400">Total studio pipelines</span>
        </Card>

        <Card className="p-5 space-y-2">
          <div className="flex items-center justify-between text-gray-500 text-xs font-semibold">
            <span>{t.analyticsDashboard.quotaStatus}</span>
            <Activity className="w-4 h-4 text-amber-500" />
          </div>
          <p className="text-2xl font-extrabold text-gray-900 dark:text-white">
            {analytics ? `${analytics.quota_units_used.toLocaleString()} / 10,000` : "..."}
          </p>
          <span className="text-[11px] text-amber-600 font-medium">
            YouTube API units today
          </span>
        </Card>
      </div>

      <Card className="p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold text-gray-900 dark:text-white">Historical Analytics</h3>
          <button onClick={generateInsights} className="rounded-lg border px-3 py-2 text-sm font-medium">
            Generate AI Insights
          </button>
        </div>
        {history?.earliest_available_date && (
          <p className="text-xs text-gray-500">Earliest retrieved date: {history.earliest_available_date}</p>
        )}
        {history?.error && (
          <p className="text-xs text-amber-600">{history.error}</p>
        )}
        {history?.rows && history.rows.length > 0 ? (
          <div className="space-y-4">
            <div className="h-28 flex items-end gap-1 rounded bg-slate-50 dark:bg-gray-900 p-2" aria-label="Daily views chart">
              {history.rows.map((row) => {
                const maxViews = Math.max(...history.rows.map((item) => item.views), 1);
                return (
                  <div
                    key={row.date}
                    title={`${row.date}: ${row.views} views`}
                    className="flex-1 min-w-1 rounded-t bg-indigo-500"
                    style={{ height: `${Math.max(4, (row.views / maxViews) * 100)}%` }}
                  />
                );
              })}
            </div>
            <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-left text-gray-500">
                  <th className="py-2">Date</th>
                  <th className="py-2">Views</th>
                  <th className="py-2">Watch minutes</th>
                  <th className="py-2">Avg. duration</th>
                  <th className="py-2">Subscribers gained/lost</th>
                </tr>
              </thead>
              <tbody>
                {history.rows.map((row) => (
                  <tr key={row.date} className="border-t border-gray-100 dark:border-gray-800">
                    <td className="py-2">{row.date}</td>
                    <td className="py-2">{row.views.toLocaleString()}</td>
                    <td className="py-2">{row.estimated_minutes_watched.toLocaleString()}</td>
                    <td className="py-2">{row.average_view_duration == null ? "Not available" : `${row.average_view_duration.toFixed(1)} sec`}</td>
                    <td className="py-2">{row.subscribers_gained}/{row.subscribers_lost}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
          </div>
        ) : (
          <p className="text-xs text-gray-500 py-3">No authorized historical Analytics API data retrieved for this range.</p>
        )}
      </Card>

      {insights && (
        <Card className="p-5 space-y-3">
          <h3 className="text-base font-bold text-gray-900 dark:text-white">AI-Generated Recommendations</h3>
          {insights.message && <p className="text-xs text-amber-600">{insights.message}</p>}
          {insights.recommendations && (
            <pre className="whitespace-pre-wrap text-xs text-gray-700 dark:text-gray-300">
              {JSON.stringify(insights.recommendations, null, 2)}
            </pre>
          )}
          {insights.disclaimer && <p className="text-xs text-gray-500">{insights.disclaimer}</p>}
        </Card>
      )}

      {/* Top Videos Section */}
      <Card className="p-5 space-y-4">
        <h3 className="text-base font-bold text-gray-900 dark:text-white">
          {t.analyticsDashboard.topVideos}
        </h3>

        {analytics && analytics.top_videos.length > 0 ? (
          <div className="divide-y divide-gray-200 dark:divide-gray-800">
            {analytics.top_videos.map((vid, idx) => (
              <div
                key={idx}
                className="py-3 flex items-center justify-between text-sm"
              >
                <div className="flex items-center gap-3">
                  <span className="text-xs font-bold text-gray-400">
                    #{idx + 1}
                  </span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {vid.title}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="info">{vid.aspect_ratio}</Badge>
                  <Badge variant="success">{vid.status}</Badge>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-gray-500 py-4 text-center">
            No videos uploaded yet. Generate and publish videos to track analytics.
          </p>
        )}
      </Card>
    </div>
  );
}
