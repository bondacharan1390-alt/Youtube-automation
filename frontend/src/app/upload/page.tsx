"use client";

import React, { useState, useEffect } from "react";
import {
  UploadCloud,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ShieldAlert,
  Loader2,
  ExternalLink,
  Film,
  ListPlus,
  Image as ImageIcon,
  RotateCw,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useTranslation } from "@/lib/i18n";
import { fetchApi } from "@/lib/api";

interface ProjectItem {
  id: string;
  title: string;
  status: string;
  language: string;
  topic?: string;
}

interface PlaylistItem {
  id: string;
  youtube_playlist_id: string;
  title: string;
  privacy_status: string;
  video_count: number;
}

interface PublishResult {
  job_id: string;
  project_id: string;
  upload_status: string;
  privacy_status: string;
  youtube_video_id: string | null;
  scheduled_publish_time: string | null;
  manual_approval_granted: boolean;
  youtube_watch_url: string | null;
  error_message?: string;
  bytes_uploaded?: number;
  total_bytes?: number;
  retry_count?: number;
  thumbnail_attached?: boolean;
  playlist_id?: string | null;
}

export default function UploadStudioPage() {
  const { t } = useTranslation();
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [playlists, setPlaylists] = useState<PlaylistItem[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [tags, setTags] = useState("");
  const [privacyStatus, setPrivacyStatus] = useState("private");
  const [scheduleTime, setScheduleTime] = useState("");
  const [selectedPlaylistId, setSelectedPlaylistId] = useState("");
  const [attachThumbnail, setAttachThumbnail] = useState(true);
  const [manualApproval, setManualApproval] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);
  const [result, setResult] = useState<PublishResult | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchApi("/projects/")
      .then((d: unknown) => {
        const arr = Array.isArray(d) ? d : (d as Record<string, unknown>).items || [];
        setProjects(arr as ProjectItem[]);
      })
      .catch(() => {});

    fetchApi("/youtube/playlists")
      .then((d: unknown) => {
        if (Array.isArray(d)) {
          setPlaylists(d as PlaylistItem[]);
        }
      })
      .catch(() => {});
  }, []);

  const handleProjectSelect = (projId: string) => {
    setSelectedProjectId(projId);
    setResult(null);
    setError("");
    const p = projects.find((x) => x.id === projId);
    if (p) {
      setTitle(p.title);
      setDescription(
        `Automated video generated with AI YouTube Studio.\n\nTopic: ${
          p.topic || p.title
        }\n\n#YouTubeAutomation #AI2026`
      );
      setTags("AI, Technology, Robotics, Innovation");
    }
  };

  const handleUpload = async () => {
    if (!selectedProjectId) return;
    if (privacyStatus === "public" && !manualApproval) {
      setError(
        "Security Rule: Explicit manual approval is required before publishing public videos."
      );
      return;
    }

    setIsUploading(true);
    setResult(null);
    setError("");

    try {
      const tagList = tags
        .split(",")
        .map((x) => x.trim())
        .filter(Boolean);
      const res = (await fetchApi("/youtube/upload", {
        method: "POST",
        body: JSON.stringify({
          project_id: selectedProjectId,
          title,
          description,
          tags: tagList,
          privacy_status: privacyStatus,
          scheduled_publish_time: scheduleTime ? new Date(scheduleTime).toISOString() : null,
          manual_approval_granted: manualApproval,
          attach_thumbnail: attachThumbnail,
          playlist_id: selectedPlaylistId || null,
        }),
      })) as PublishResult;
      setResult(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to upload video";
      setError(msg);
    } finally {
      setIsUploading(false);
    }
  };

  const handleRetry = async () => {
    if (!result?.job_id) return;
    setIsRetrying(true);
    setError("");
    try {
      const res = (await fetchApi(`/youtube/retry/${result.job_id}`, {
        method: "POST",
      })) as PublishResult;
      setResult(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Retry failed";
      setError(msg);
    } finally {
      setIsRetrying(false);
    }
  };

  return (
    <div className="p-4 md:p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <UploadCloud className="w-6 h-6 text-red-500" />
          {t.uploadScheduling.title}
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          {t.uploadScheduling.subtitle}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Upload Form */}
        <div className="lg:col-span-2 space-y-4">
          <Card className="p-5 space-y-4">
            <div>
              <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                {t.uploadScheduling.selectProject}
              </label>
              <select
                value={selectedProjectId}
                onChange={(e) => handleProjectSelect(e.target.value)}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-3 py-2 text-sm outline-none"
              >
                <option value="">— {t.uploadScheduling.selectProject} —</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.title} [{p.status}]
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                {t.uploadScheduling.videoTitle}
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                maxLength={100}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-3 py-2 text-sm outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                {t.uploadScheduling.description}
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={4}
                className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-3 py-2 text-sm outline-none resize-none"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                  {t.uploadScheduling.tags}
                </label>
                <input
                  type="text"
                  value={tags}
                  onChange={(e) => setTags(e.target.value)}
                  placeholder="tag1, tag2, tag3"
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-3 py-2 text-sm outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1 flex items-center gap-1.5">
                  <ListPlus className="w-3.5 h-3.5 text-red-500" />
                  YouTube Playlist
                </label>
                <select
                  value={selectedPlaylistId}
                  onChange={(e) => setSelectedPlaylistId(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-3 py-2 text-sm outline-none"
                >
                  <option value="">— None (No Playlist) —</option>
                  {playlists.map((pl) => (
                    <option key={pl.id} value={pl.youtube_playlist_id}>
                      {pl.title} ({pl.video_count} videos)
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                  {t.uploadScheduling.privacyStatus}
                </label>
                <select
                  value={privacyStatus}
                  onChange={(e) => setPrivacyStatus(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-3 py-2 text-sm outline-none"
                >
                  <option value="private">{t.uploadScheduling.privateOption}</option>
                  <option value="unlisted">{t.uploadScheduling.unlistedOption}</option>
                  <option value="public">{t.uploadScheduling.publicOption}</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                  {t.uploadScheduling.schedulePublish}
                </label>
                <input
                  type="datetime-local"
                  value={scheduleTime}
                  onChange={(e) => setScheduleTime(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white px-3 py-2 text-sm outline-none"
                />
              </div>
            </div>

            {/* Thumbnail toggle */}
            <div className="p-3 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/40 text-xs">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={attachThumbnail}
                  onChange={(e) => setAttachThumbnail(e.target.checked)}
                  className="rounded accent-red-600"
                />
                <ImageIcon className="w-4 h-4 text-amber-500" />
                <span className="font-semibold text-gray-800 dark:text-gray-200">
                  Automatically attach project custom thumbnail (thumbnails.set)
                </span>
              </label>
            </div>

            {/* Mandatory Approval Checkbox */}
            <div className="p-3.5 rounded-lg border border-amber-300 bg-amber-50 dark:bg-amber-950/20 text-xs space-y-2">
              <label className="flex items-start gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={manualApproval}
                  onChange={(e) => setManualApproval(e.target.checked)}
                  className="mt-0.5 rounded accent-red-600"
                />
                <span className="font-semibold text-amber-900 dark:text-amber-200">
                  {t.uploadScheduling.manualApproval}
                </span>
              </label>
              <p className="text-[11px] text-amber-700 dark:text-amber-300 pl-6">
                Guarantees human-in-the-loop oversight before publishing publicly. Private uploads default to safe sandbox.
              </p>
            </div>

            {error && (
              <div className="p-3 rounded-lg bg-red-50 dark:bg-red-950/20 border border-red-300 text-xs text-red-600">
                {error}
              </div>
            )}

            <Button
              variant="primary"
              disabled={!selectedProjectId || isUploading}
              onClick={handleUpload}
              className="w-full flex items-center justify-center gap-2"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Uploading via Resumable Protocol...
                </>
              ) : (
                <>
                  <UploadCloud className="w-4 h-4" />
                  {t.uploadScheduling.publishButton}
                </>
              )}
            </Button>
          </Card>
        </div>

        {/* Upload Status & Result */}
        <div>
          <Card className="p-5 space-y-4">
            <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200 flex items-center gap-2">
              <Film className="w-4 h-4 text-red-500" />
              Upload Summary
            </h3>

            {result ? (
              <div className="space-y-3 text-xs">
                {result.upload_status === "uploaded" ? (
                  <div className="p-3 bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-300 rounded-lg flex items-center gap-2 text-emerald-700 dark:text-emerald-300 font-medium">
                    <CheckCircle2 className="w-4 h-4 shrink-0" />
                    {t.uploadScheduling.uploadSuccess}
                  </div>
                ) : (
                  <div className="p-3 bg-red-50 dark:bg-red-950/20 border border-red-300 rounded-lg flex items-center gap-2 text-red-700 dark:text-red-300 font-medium">
                    <AlertTriangle className="w-4 h-4 shrink-0" />
                    Status: {result.upload_status}
                  </div>
                )}

                <div className="space-y-1 py-1">
                  <span className="text-gray-500">Video ID:</span>
                  <p className="font-mono text-gray-900 dark:text-white font-semibold">
                    {result.youtube_video_id || "Pending"}
                  </p>
                </div>

                <div className="space-y-1 py-1">
                  <span className="text-gray-500">Privacy Mode:</span>
                  <p className="font-semibold uppercase text-gray-900 dark:text-white">
                    {result.privacy_status}
                  </p>
                </div>

                <div className="space-y-1 py-1">
                  <span className="text-gray-500">Thumbnail:</span>
                  <p className="font-medium text-gray-900 dark:text-white">
                    {result.thumbnail_attached ? "Attached via API" : "Default YouTube"}
                  </p>
                </div>

                {result.upload_status === "failed" && (
                  <div className="pt-2">
                    <Button
                      variant="outline"
                      onClick={handleRetry}
                      disabled={isRetrying}
                      className="w-full text-xs flex items-center justify-center gap-1.5"
                    >
                      {isRetrying ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <RotateCw className="w-3.5 h-3.5" />
                      )}
                      Retry Upload ({result.retry_count || 0}/3)
                    </Button>
                  </div>
                )}

                {result.youtube_watch_url && (
                  <a
                    href={result.youtube_watch_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-2 text-red-600 hover:underline font-semibold pt-2"
                  >
                    <ExternalLink className="w-4 h-4" />
                    Open on YouTube
                  </a>
                )}
              </div>
            ) : (
              <p className="text-xs text-gray-400 py-8 text-center">
                Configure your video parameters and click Publish to upload.
              </p>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
