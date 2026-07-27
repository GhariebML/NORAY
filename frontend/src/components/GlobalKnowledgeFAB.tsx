"use client";

import React from "react";
import { Plus, Database, Sparkles } from "lucide-react";

interface GlobalKnowledgeFABProps {
  onClick: () => void;
  activeQueueCount?: number;
}

export function GlobalKnowledgeFAB({ onClick, activeQueueCount = 0 }: GlobalKnowledgeFABProps) {
  return (
    <div className="fixed bottom-3 right-56 z-40 font-sans text-xs select-none">
      <button
        onClick={onClick}
        className="group relative flex items-center gap-2 rounded-xl border border-emerald-500/30 bg-zinc-950/90 px-3.5 py-2 text-emerald-400 font-semibold shadow-2xl backdrop-blur-md transition-all duration-300 hover:border-emerald-400 hover:bg-emerald-500/10 hover:shadow-[0_0_20px_rgba(16,185,129,0.3)] active:scale-95"
        title="Open Knowledge Drawer (Alt + K)"
      >
        <div className="flex items-center gap-1.5">
          <div className="relative flex items-center justify-center">
            <Plus size={14} className="transition-transform duration-300 group-hover:rotate-90" />
            <Database size={12} className="absolute -bottom-1 -right-1 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
          <span className="tracking-wide">Add Knowledge</span>
        </div>

        {activeQueueCount > 0 ? (
          <span className="flex items-center gap-1 rounded-md bg-emerald-500 text-zinc-950 px-1.5 py-0.5 text-[9px] font-bold font-mono animate-pulse">
            <Sparkles size={10} />
            {activeQueueCount}
          </span>
        ) : (
          <span className="hidden sm:inline-block rounded bg-zinc-900 border border-zinc-800 px-1.5 py-0.5 text-[9px] text-zinc-500 font-mono group-hover:border-emerald-500/30 group-hover:text-emerald-400/80">
            Alt+K
          </span>
        )}
      </button>
    </div>
  );
}
