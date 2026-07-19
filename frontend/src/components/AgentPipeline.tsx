"use client";

import React from "react";
import {
  Brain,
  Search,
  Database,
  FileCheck,
  CheckCircle2,
  Loader2,
  Clock,
  Zap,
} from "lucide-react";
import { motion } from "framer-motion";

export interface AgentStep {
  name: string;
  role: string;
  status: "pending" | "running" | "completed" | "failed";
  executionTime?: string;
  confidence?: number; // 0-100
  icon: React.ElementType;
}

export function AgentPipeline({ steps }: { steps?: AgentStep[] }) {
  const defaultSteps: AgentStep[] = [
    { name: "Planner Agent", role: "Goal Decomposition & Intent Classifier", status: "completed", executionTime: "42ms", confidence: 98, icon: Brain },
    { name: "Research Agent", role: "Hybrid Vector & BM25 Query Expansion", status: "completed", executionTime: "128ms", confidence: 95, icon: Search },
    { name: "Hybrid RAG Engine", role: "Qdrant Vector Store + BM25 RRF Fusion", status: "completed", executionTime: "85ms", confidence: 96, icon: Database },
    { name: "Document / Synthesis Agent", role: "Context Compression & Output Generation", status: "completed", executionTime: "410ms", confidence: 94, icon: FileCheck },
  ];

  const activeSteps = steps && steps.length > 0 ? steps : defaultSteps;

  return (
    <div className="rounded-xl border border-slate-800/80 bg-[#131c31]/90 p-4 backdrop-blur-md shadow-2xl">
      <div className="mb-3 flex items-center justify-between border-b border-zinc-800 pb-2.5">
        <div className="flex items-center gap-2">
          <Zap size={16} className="text-emerald-400" />
          <span className="text-xs font-bold tracking-wide text-zinc-100 uppercase font-heading">
            Autonomous Multi-Agent Pipeline
          </span>
        </div>
        <span className="rounded-full bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 text-[10px] text-emerald-400 font-mono font-medium">
          4 Agents Active
        </span>
      </div>

      <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 lg:grid-cols-4">
        {activeSteps.map((step, idx) => {
          const Icon = step.icon;
          return (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, delay: idx * 0.05 }}
              className={`relative overflow-hidden rounded-lg border p-3 transition-all ${
                step.status === "running"
                  ? "border-emerald-500/50 bg-emerald-500/10 shadow-lg shadow-emerald-500/10"
                  : step.status === "completed"
                  ? "border-zinc-800 bg-[#111827]/90 hover:border-zinc-700"
                  : "border-zinc-800/60 bg-[#0b111e]/60 opacity-60"
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <div className={`rounded-md p-1.5 ${step.status === "running" ? "bg-emerald-500/20 text-emerald-400" : "bg-zinc-800 text-zinc-400"}`}>
                    <Icon size={14} />
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-zinc-200">{step.name}</h4>
                    <p className="text-[10px] text-zinc-400 truncate max-w-[120px]">{step.role}</p>
                  </div>
                </div>

                {step.status === "running" ? (
                  <Loader2 size={13} className="animate-spin text-emerald-400" />
                ) : (
                  <CheckCircle2 size={13} className="text-emerald-400" />
                )}
              </div>

              <div className="mt-3 flex items-center justify-between border-t border-zinc-800/80 pt-2 text-[10px] font-mono text-zinc-400">
                <span className="flex items-center gap-1">
                  <Clock size={11} className="text-zinc-500" /> {step.executionTime || "0ms"}
                </span>
                {step.confidence !== undefined && (
                  <span className="text-emerald-400 font-semibold">{step.confidence}% Conf</span>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
