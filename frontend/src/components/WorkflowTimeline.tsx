"use client";

import React from "react";
import { CheckCircle2, Loader2, Circle } from "lucide-react";
import { motion } from "framer-motion";

export interface TimelineStep {
  label: string;
  status: "completed" | "running" | "pending";
  timestamp?: string;
}

export function WorkflowTimeline({ steps }: { steps?: TimelineStep[] }) {
  const defaultTimeline: TimelineStep[] = [
    { label: "Query Ingestion & Intent Analysis", status: "completed", timestamp: "+10ms" },
    { label: "Hybrid Search (Qdrant Dense + BM25 Lexical)", status: "completed", timestamp: "+45ms" },
    { label: "Reciprocal Rank Fusion (RRF) & Cross-Encoder Rerank", status: "completed", timestamp: "+82ms" },
    { label: "Context Compression & Grounded Context Assembly", status: "completed", timestamp: "+115ms" },
    { label: "Dual-Tier Model Routing (Gemini 1.5 / DeepSeek / Ollama)", status: "completed", timestamp: "+190ms" },
    { label: "Synthesizing Structured Output", status: "completed", timestamp: "+340ms" },
  ];

  const list = steps && steps.length > 0 ? steps : defaultTimeline;

  return (
    <div className="rounded-lg border border-zinc-800 bg-[#111827]/90 p-3 text-xs font-mono">
      <div className="mb-2 flex items-center justify-between border-b border-zinc-800 pb-1.5">
        <span className="font-semibold text-emerald-400 uppercase tracking-wider text-[10px]">
          AI Workflow Execution Timeline
        </span>
        <span className="text-[10px] text-zinc-500">6 Steps Executed</span>
      </div>

      <div className="space-y-1.5 pt-1">
        {list.map((step, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, x: -5 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.15, delay: idx * 0.04 }}
            className="flex items-center justify-between gap-2 text-zinc-300"
          >
            <div className="flex items-center gap-2">
              {step.status === "completed" ? (
                <CheckCircle2 size={13} className="text-emerald-400 shrink-0" />
              ) : step.status === "running" ? (
                <Loader2 size={13} className="animate-spin text-cyan-400 shrink-0" />
              ) : (
                <Circle size={13} className="text-zinc-600 shrink-0" />
              )}
              <span className={step.status === "completed" ? "text-zinc-300" : "text-zinc-500"}>
                {step.label}
              </span>
            </div>

            {step.timestamp && (
              <span className="text-[10px] text-zinc-500 shrink-0">{step.timestamp}</span>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  );
}
