"use client";

import React, { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { fetchApi } from "@/lib/api";

interface ProjectItem {
  id: string;
  title: string;
  topic?: string;
}

interface WorkflowTask {
  id: string;
  task_key: string;
  name: string;
  status: string;
  progress_percentage: number;
  error?: string;
}

interface WorkflowItem {
  id: string;
  project_id: string;
  name: string;
  status: string;
  progress_percentage: number;
  tasks: WorkflowTask[];
}

interface HardwareStatus {
  total_ram_gb: number;
  free_ram_gb: number;
  is_memory_safe: boolean;
  queue_locked: boolean;
}

export default function AutomationPage() {
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [workflows, setWorkflows] = useState<WorkflowItem[]>([]);
  const [projectId, setProjectId] = useState("");
  const [privacy, setPrivacy] = useState("private");
  const [scheduledAt, setScheduledAt] = useState("");
  const [hardware, setHardware] = useState<HardwareStatus | null>(null);

  const load = async () => {
    const [projectData, workflowData, hwData] = await Promise.all([
      fetchApi<ProjectItem[]>("/projects"),
      fetchApi<WorkflowItem[]>("/automation/workflows"),
      fetchApi<HardwareStatus>("/automation/hardware/status").catch(() => null),
    ]);
    setProjects(projectData);
    setWorkflows(workflowData);
    if (hwData) setHardware(hwData);
    if (!projectId && projectData.length) setProjectId(projectData[0].id);
  };

  useEffect(() => {
    load().catch(console.error);
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => {
      fetchApi<WorkflowItem[]>("/automation/workflows")
        .then(setWorkflows)
        .catch(() => undefined);
      fetchApi<HardwareStatus>("/automation/hardware/status")
        .then(setHardware)
        .catch(() => undefined);
    }, 3000);
    return () => window.clearInterval(timer);
  }, []);

  const createAndStart = async () => {
    if (!projectId) return;
    const workflow = await fetchApi<WorkflowItem>("/automation/workflows", {
      method: "POST",
      body: JSON.stringify({ project_id: projectId, settings: {} }),
    });
    await fetchApi(`/automation/workflows/${workflow.id}/start`, { method: "POST" });
    await load();
  };

  const control = async (workflowId: string, action: "pause" | "resume" | "cancel") => {
    await fetchApi(`/automation/workflows/${workflowId}/${action}`, { method: "POST" });
    await load();
  };

  const retry = async (taskId: string) => {
    await fetchApi(`/automation/tasks/${taskId}/retry`, { method: "POST" });
    await load();
  };

  const regenerate = async (taskId: string) => {
    await fetchApi(`/automation/tasks/${taskId}/regenerate`, { method: "POST" });
    await load();
  };

  const approve = async (workflowId: string) => {
    await fetchApi(`/automation/workflows/${workflowId}/approve`, {
      method: "POST",
      body: JSON.stringify({
        privacy_status: privacy,
        scheduled_at: scheduledAt ? new Date(scheduledAt).toISOString() : null,
        timezone_name: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
      }),
    });
    await load();
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Automation Dashboard</h1>
          <p className="text-sm text-slate-500 mt-1">End-to-end research through publishing workflow.</p>
        </div>
        {hardware && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-slate-200 dark:border-studio-800 bg-slate-50 dark:bg-studio-900 text-xs">
            <span className={`w-2 h-2 rounded-full ${hardware.is_memory_safe ? "bg-emerald-500" : "bg-amber-500"}`} />
            <span className="text-slate-600 dark:text-slate-300">
              Hardware Guard: {hardware.free_ram_gb.toFixed(1)} GB / {hardware.total_ram_gb.toFixed(1)} GB RAM Free
            </span>
            {hardware.queue_locked && (
              <span className="ml-1 px-1.5 py-0.5 rounded bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-200 text-[10px] font-semibold">
                BUSY (LOCKED)
              </span>
            )}
          </div>
        )}
      </div>

      <Card className="p-4">
        <div className="flex flex-col sm:flex-row gap-3">
          <select
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
            className="flex-1 px-3 py-2 rounded-lg border border-slate-200 dark:border-studio-700 bg-white dark:bg-studio-950 text-slate-900 dark:text-white"
          >
            {projects.map((project) => (
              <option key={project.id} value={project.id}>{project.title}</option>
            ))}
          </select>
          <Button onClick={createAndStart}>Start Automation</Button>
        </div>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        {workflows.map((workflow) => {
          const approvalTask = workflow.tasks.find((t) => t.task_key === "approval");
          const qualityTask = workflow.tasks.find((t) => t.task_key === "quality_check");
          const isAwaitingApproval = approvalTask?.status === "waiting_approval";
          const qualityPassed = qualityTask?.status === "completed";

          return (
            <Card key={workflow.id} className="p-4 space-y-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="font-semibold text-slate-900 dark:text-white">{workflow.name}</h2>
                  <p className="text-xs text-slate-500">Status: <span className="font-medium uppercase text-slate-700 dark:text-slate-300">{workflow.status}</span> · {workflow.progress_percentage}%</p>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => control(workflow.id, "pause")}>Pause</Button>
                  <Button size="sm" variant="outline" onClick={() => control(workflow.id, "resume")}>Resume</Button>
                  <Button size="sm" variant="danger" onClick={() => control(workflow.id, "cancel")}>Cancel</Button>
                </div>
              </div>

              <div className="h-2 rounded bg-slate-100 dark:bg-studio-900 overflow-hidden">
                <div className="h-2 bg-red-600 transition-all duration-300" style={{ width: `${workflow.progress_percentage}%` }} />
              </div>

              <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                {workflow.tasks.map((task) => (
                  <div key={task.id} className="flex items-center justify-between rounded border border-slate-100 dark:border-studio-800 px-3 py-2 bg-white dark:bg-studio-900/50">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${
                          task.status === "completed" ? "bg-emerald-500" :
                          task.status === "running" ? "bg-blue-500 animate-pulse" :
                          task.status === "waiting_approval" ? "bg-amber-500" :
                          task.status === "failed" ? "bg-red-500" : "bg-slate-300 dark:bg-slate-700"
                        }`} />
                        <p className="text-xs font-medium text-slate-700 dark:text-slate-200">{task.name}</p>
                      </div>
                      <p className="text-[11px] text-slate-500 truncate ml-4">
                        {task.status}{task.error ? ` — ${task.error}` : ""}
                      </p>
                    </div>
                    <div className="flex gap-1 shrink-0">
                      {task.status === "failed" && (
                        <Button size="sm" variant="outline" onClick={() => retry(task.id)}>Retry</Button>
                      )}
                      {!["approval", "upload", "quality_check"].includes(task.task_key) &&
                        ["completed", "failed"].includes(task.status) && (
                          <Button size="sm" variant="outline" onClick={() => regenerate(task.id)}>Regenerate</Button>
                        )}
                    </div>
                  </div>
                ))}
              </div>

              {isAwaitingApproval && (
                <Card className="p-3 border-amber-300 dark:border-amber-900 bg-amber-50/50 dark:bg-amber-950/20 space-y-3">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-semibold text-amber-900 dark:text-amber-200">
                      Mandatory Human Approval Gate
                    </p>
                    {qualityPassed && (
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-200">
                        Quality Check Passed
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-600 dark:text-slate-400">
                    Review generated MP4, thumbnail, and metadata. By default, videos are published as Private for safety.
                  </p>
                  <div className="grid sm:grid-cols-3 gap-2">
                    <select
                      value={privacy}
                      onChange={(e) => setPrivacy(e.target.value)}
                      className="px-3 py-1.5 rounded border border-slate-300 dark:border-studio-700 text-xs bg-white dark:bg-studio-950"
                    >
                      <option value="private">Private (Default)</option>
                      <option value="unlisted">Unlisted</option>
                      <option value="public">Public (Requires confirmation)</option>
                    </select>
                    <input
                      type="datetime-local"
                      value={scheduledAt}
                      onChange={(e) => setScheduledAt(e.target.value)}
                      className="px-3 py-1.5 rounded border border-slate-300 dark:border-studio-700 text-xs bg-white dark:bg-studio-950"
                    />
                    <Button size="sm" onClick={() => approve(workflow.id)}>
                      Approve & {scheduledAt ? "Schedule" : "Upload"}
                    </Button>
                  </div>
                </Card>
              )}
            </Card>
          );
        })}
      </div>
    </div>
  );
}
