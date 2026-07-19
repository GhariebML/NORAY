"use client";

import React, { useState } from "react";
import {
  Activity,
  CheckCircle2,
  Loader2,
  ChevronUp,
  ChevronDown,
  Database,
  Cpu,
  Layers,
  Sparkles,
} from "lucide-react";

export interface BackgroundTask {
  id: string;
  name: string;
  status: "running" | "completed" | "failed";
  progress: number; // 0-100
  estimatedTime?: string;
  category: "embedding" | "generation" | "analysis" | "indexing";
}

export function TaskManagerBar() {
  const [expanded, setExpanded] = useState(false);
  const [tasks] = useState<BackgroundTask[]>([
    {
      id: "t1",
      name: "Vector Store Indexing (Qdrant Singleton)",
      status: "completed",
      progress: 100,
      estimatedTime: "Done",
      category: "indexing",
    },
    {
      id: "t2",
      name: "Dual-Tier Model Health Monitor Sync",
      status: "running",
      progress: 85,
      estimatedTime: "~2s",
      category: "analysis",
    },
  ]);

  const activeCount = tasks.filter((t) => t.status === "running").length;

  return (
    <div className="fixed bottom-3 right-4 z-40 font-sans text-xs">
      <div className="rounded-xl border border-zinc-800/90 bg-[#111827]/95 p-2 shadow-2xl backdrop-blur-md">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-3 px-2 py-1 text-zinc-300 hover:text-white transition-colors"
        >
          <div className="flex items-center gap-1.5 font-medium text-emerald-400">
            <Activity size={14} className="animate-pulse" />
            <span>AI Background Engine</span>
          </div>

          <span className="rounded-md bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 text-[10px] text-emerald-300 font-mono">
            {activeCount > 0 ? `${activeCount} Active` : "Ready"}
          </span>

          {expanded ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
        </button>

        {expanded && (
          <div className="mt-3 w-80 space-y-2 border-t border-zinc-800/80 pt-3 text-xs">
            {tasks.map((task) => (
              <div key={task.id} className="space-y-1 rounded-lg border border-zinc-800 bg-[#161f2d]/80 p-2.5">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium text-zinc-200 truncate flex items-center gap-1.5">
                    {task.category === "indexing" && <Database size={13} className="text-emerald-400" />}
                    {task.category === "analysis" && <Cpu size={13} className="text-cyan-400" />}
                    {task.category === "generation" && <Sparkles size={13} className="text-amber-400" />}
                    {task.name}
                  </span>
                  <span className="text-[10px] text-zinc-400 font-mono">{task.estimatedTime}</span>
                </div>

                <div className="flex items-center gap-2 pt-1">
                  <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-zinc-800">
                    <div
                      className={`h-full transition-all duration-300 ${
                        task.status === "completed" ? "bg-emerald-500" : "bg-cyan-500"
                      }`}
                      style={{ width: `${task.progress}%` }}
                    />
                  </div>
                  {task.status === "running" ? (
                    <Loader2 size={12} className="animate-spin text-cyan-400" />
                  ) : (
                    <CheckCircle2 size={12} className="text-emerald-400" />
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
