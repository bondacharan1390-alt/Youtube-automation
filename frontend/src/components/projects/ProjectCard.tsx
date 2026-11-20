"use client";

import React from "react";
import Link from "next/link";
import { Film, Smartphone, Clock, Layers, ArrowRight, Trash2 } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { formatDuration, formatDate } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n";

export interface ProjectCardData {
  id: string;
  title: string;
  topic?: string;
  language: string;
  aspect_ratio: string;
  target_resolution: string;
  status: string;
  estimated_duration_seconds: number;
  scenes_count?: number;
  created_at: string;
}

interface ProjectCardProps {
  project: ProjectCardData;
  onDelete?: (id: string) => void;
}

export const ProjectCard: React.FC<ProjectCardProps> = ({ project, onDelete }) => {
  const { t } = useTranslation();
  const isShort = project.aspect_ratio === "9:16";

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "ready":
        return <Badge variant="success">Ready</Badge>;
      case "published":
        return <Badge variant="purple">Published</Badge>;
      case "scripted":
      case "voiced":
      case "rendered":
        return <Badge variant="info">In Progress</Badge>;
      default:
        return <Badge variant="default">Draft</Badge>;
    }
  };

  return (
    <Card hoverable className="flex flex-col justify-between group">
      <div>
        {/* Top Header: Aspect preview icon & badges */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <span
              className={`p-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1 ${
                isShort
                  ? "bg-purple-100 text-purple-700 dark:bg-purple-950/50 dark:text-purple-300"
                  : "bg-red-100 text-red-700 dark:bg-red-950/50 dark:text-red-300"
              }`}
            >
              {isShort ? <Smartphone className="w-3.5 h-3.5" /> : <Film className="w-3.5 h-3.5" />}
              <span>{isShort ? "Shorts 9:16" : "Video 16:9"}</span>
            </span>

            <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-600 dark:bg-studio-800 dark:text-slate-300">
              {project.language === "te" ? "తెలుగు" : "EN"}
            </span>
          </div>

          {getStatusBadge(project.status)}
        </div>

        {/* Project Title */}
        <h4 className="text-base font-semibold text-slate-900 dark:text-white line-clamp-1 group-hover:text-red-600 dark:group-hover:text-red-400 transition-colors">
          {project.title}
        </h4>

        {/* Topic Preview */}
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-2 min-h-[32px]">
          {project.topic || "Autonomous video generation project"}
        </p>
      </div>

      {/* Meta Footer */}
      <div className="mt-4 pt-3 border-t border-slate-100 dark:border-studio-800/80 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
        <div className="flex items-center space-x-3">
          <span className="flex items-center space-x-1">
            <Layers className="w-3.5 h-3.5 text-slate-400" />
            <span>{project.scenes_count || 5} {t.projects.scenes}</span>
          </span>
          <span className="flex items-center space-x-1">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            <span>{formatDuration(project.estimated_duration_seconds)}</span>
          </span>
        </div>

        <div className="flex items-center space-x-2">
          {onDelete && (
            <button
              onClick={() => onDelete(project.id)}
              className="p-1 rounded text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 transition-colors"
              title="Delete Project"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
          <Link
            href={`/projects/${project.id}`}
            className="p-1 text-slate-400 hover:text-red-600 dark:hover:text-red-400 transition-colors flex items-center"
          >
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </Card>
  );
};
