"use client";

import React from "react";
import {
  X,
  Brain,
  Database,
  Terminal,
  Cpu,
  Layers,
  Sparkles,
  BarChart2,
  FileText,
  CheckCircle2,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export interface XAIData {
  reasoning: string;
  toolsUsed: { tool: string; duration: string; status: string }[];
  ragChunks: { source: string; content: string; denseScore: number; bm25Score: number; hybridRank: number }[];
  provider: string;
  model: string;
  totalTokens: number;
  latencyMs: number;
  confidenceScore: number;
}

export function ExplainableAIDrawer({
  isOpen,
  onClose,
  data,
}: {
  isOpen: boolean;
  onClose: () => void;
  data?: XAIData;
}) {
  const defaultData: XAIData = {
    reasoning: "User requested career assistance tailored for ML Engineering positions at Google. Synthesized candidate canonical profile with ATS keyword recommendations.",
    toolsUsed: [
      { tool: "local_search(QdrantVectorStore)", duration: "45ms", status: "success" },
      { tool: "extract_keywords(ats_analyzer)", duration: "32ms", status: "success" },
      { tool: "generate_cv_docx(docx_generator)", duration: "110ms", status: "success" },
    ],
    ragChunks: [
      {
        source: "career_profile.json",
        content: "Gharieb Mohamed — Machine Learning Engineer with expertise in Agentic RAG Operating Systems, FastAPI, Qdrant, and PyTorch.",
        denseScore: 0.942,
        bm25Score: 14.8,
        hybridRank: 1,
      },
      {
        source: "google_ml_engineer_posting.txt",
        content: "Requires experience in distributed LLM architectures, vector databases, Python, and system optimization.",
        denseScore: 0.891,
        bm25Score: 12.4,
        hybridRank: 2,
      },
    ],
    provider: "OpenRouter / Gemini 1.5 Pro",
    model: "gemini-1.5-pro",
    totalTokens: 1420,
    latencyMs: 380,
    confidenceScore: 96,
  };

  const xai = data || defaultData;

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex justify-end">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/60 backdrop-blur-sm"
          onClick={onClose}
        />

        <motion.div
          initial={{ x: "100%" }}
          animate={{ x: 0 }}
          exit={{ x: "100%" }}
          transition={{ type: "spring", damping: 25, stiffness: 200 }}
          className="relative z-50 h-full w-full max-w-lg border-l border-zinc-800 bg-[#0b111e] p-6 shadow-2xl overflow-y-auto font-sans"
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-zinc-800 pb-4">
            <div className="flex items-center gap-2">
              <Sparkles className="text-emerald-400" size={18} />
              <h2 className="text-base font-bold text-zinc-100 font-heading">
                Explainable AI (XAI) Telemetry
              </h2>
            </div>
            <button
              onClick={onClose}
              className="rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200 transition-colors"
            >
              <X size={16} />
            </button>
          </div>

          <div className="mt-5 space-y-6 text-xs">
            {/* Summary Metrics */}
            <div className="grid grid-cols-3 gap-3">
              <div className="rounded-lg border border-zinc-800 bg-[#111827] p-3 text-center">
                <span className="block text-[10px] text-zinc-500 uppercase">Provider</span>
                <span className="mt-1 block font-bold text-emerald-400 truncate">{xai.provider}</span>
              </div>

              <div className="rounded-lg border border-zinc-800 bg-[#111827] p-3 text-center">
                <span className="block text-[10px] text-zinc-500 uppercase">Tokens</span>
                <span className="mt-1 block font-bold text-cyan-400 font-mono">{xai.totalTokens}</span>
              </div>

              <div className="rounded-lg border border-zinc-800 bg-[#111827] p-3 text-center">
                <span className="block text-[10px] text-zinc-500 uppercase">Latency</span>
                <span className="mt-1 block font-bold text-amber-400 font-mono">{xai.latencyMs}ms</span>
              </div>
            </div>

            {/* Cognitive Reasoning */}
            <div>
              <h3 className="mb-2 text-xs font-semibold text-zinc-300 flex items-center gap-1.5">
                <Brain size={14} className="text-emerald-400" />
                Cognitive Reflection & Reasoning
              </h3>
              <div className="rounded-lg border border-zinc-800 bg-[#161f2d]/90 p-3.5 leading-relaxed text-zinc-300 font-sans shadow-inner">
                {xai.reasoning}
              </div>
            </div>

            {/* Tool Executions */}
            <div>
              <h3 className="mb-2 text-xs font-semibold text-zinc-300 flex items-center gap-1.5">
                <Terminal size={14} className="text-cyan-400" />
                Invoked Tool Calls
              </h3>
              <div className="space-y-2 font-mono">
                {xai.toolsUsed.map((t, idx) => (
                  <div key={idx} className="flex items-center justify-between rounded-md border border-zinc-800/80 bg-[#111827] p-2.5">
                    <span className="text-emerald-300 truncate">{t.tool}</span>
                    <span className="text-[10px] text-zinc-500">{t.duration}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* RAG Retrieval Visualizer */}
            <div>
              <h3 className="mb-2 text-xs font-semibold text-zinc-300 flex items-center gap-1.5">
                <Database size={14} className="text-emerald-400" />
                RAG Retrieval & Hybrid Rank (Dense + BM25)
              </h3>

              <div className="space-y-3">
                {xai.ragChunks.map((chunk, idx) => (
                  <div key={idx} className="rounded-lg border border-zinc-800 bg-[#111827] p-3 space-y-2">
                    <div className="flex items-center justify-between text-[11px] font-mono border-b border-zinc-800/60 pb-1.5">
                      <span className="text-emerald-400 flex items-center gap-1 font-medium">
                        <FileText size={12} /> {chunk.source}
                      </span>
                      <span className="rounded bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 text-[10px] text-emerald-300 font-bold">
                        Rank #{chunk.hybridRank}
                      </span>
                    </div>

                    <p className="text-[11px] leading-relaxed text-zinc-300 italic">
                      &quot;{chunk.content}&quot;
                    </p>

                    <div className="flex items-center gap-4 text-[10px] font-mono text-zinc-400 pt-1">
                      <span>Dense Vector Sim: <strong className="text-cyan-400">{chunk.denseScore}</strong></span>
                      <span>BM25 Score: <strong className="text-amber-400">{chunk.bm25Score}</strong></span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
