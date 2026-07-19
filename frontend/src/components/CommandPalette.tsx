"use client";

import { useState, useEffect, useRef } from "react";
import { Search, Globe, Terminal, FileText, ArrowRight, CornerDownLeft, Sparkles, Activity, ShieldAlert } from "lucide-react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";

interface CommandItem {
  id: string;
  category: "navigation" | "actions" | "documents";
  label: string;
  shortcut?: string;
  icon: any;
  action: () => void;
}

export function CommandPalette({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const commands: CommandItem[] = [
    {
      id: "nav-dash",
      category: "navigation",
      label: "Go to Mission Control Dashboard",
      shortcut: "G D",
      icon: Globe,
      action: () => { router.push("/"); onClose(); }
    },
    {
      id: "nav-workspace",
      category: "navigation",
      label: "Go to AI Workspace Canvas",
      shortcut: "G W",
      icon: Terminal,
      action: () => { router.push("/workspace"); onClose(); }
    },
    {
      id: "nav-diagnostics",
      category: "navigation",
      label: "Open AI Gateway Diagnostics",
      shortcut: "G A",
      icon: Activity,
      action: () => { router.push("/diagnostics"); onClose(); }
    },
    {
      id: "nav-profile",
      category: "navigation",
      label: "Go to Profile Settings",
      shortcut: "G P",
      icon: Sparkles,
      action: () => { router.push("/profile"); onClose(); }
    },
    {
      id: "action-provider-local",
      category: "actions",
      label: "Switch LLM Gateway Mode to Ollama Local",
      shortcut: "S L",
      icon: Sparkles,
      action: () => {
        alert("Switched to Ollama Local model");
        onClose();
      }
    },
    {
      id: "action-provider-cloud",
      category: "actions",
      label: "Switch LLM Gateway Mode to Cloud Fallbacks",
      shortcut: "S C",
      icon: ShieldAlert,
      action: () => {
        alert("Switched to Cloud GPT/Claude Provider fallback mode");
        onClose();
      }
    }
  ];

  // Filter commands by query match
  const filtered = commands.filter(cmd => 
    cmd.label.toLowerCase().includes(query.toLowerCase())
  );

  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 80);
    }
  }, [isOpen]);

  // Keyboard navigation inside palette
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex(prev => (prev + 1) % Math.max(1, filtered.length));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex(prev => (prev - 1 + filtered.length) % Math.max(1, filtered.length));
      } else if (e.key === "Enter") {
        e.preventDefault();
        if (filtered[selectedIndex]) {
          filtered[selectedIndex].action();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, filtered, selectedIndex, onClose]);

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[200] flex items-start justify-center pt-[15vh] px-4">
          
          {/* Blur Overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm"
            onClick={onClose}
          />

          {/* Dialog Body */}
          <motion.div
            initial={{ opacity: 0, scale: 0.97, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.97, y: -10 }}
            transition={{ duration: 0.15 }}
            className="w-full max-w-xl rounded-xl border border-zinc-800 bg-zinc-950/90 text-zinc-100 shadow-2xl backdrop-blur-md overflow-hidden relative z-10"
          >
            {/* Input Header */}
            <div className="flex items-center gap-3 px-4 border-b border-zinc-800 h-12">
              <Search className="text-zinc-500 shrink-0" size={16} />
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setSelectedIndex(0);
                }}
                placeholder="Type a command or route name..."
                className="w-full bg-transparent text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none"
              />
              <button 
                onClick={onClose}
                className="text-[10px] bg-zinc-900 border border-zinc-850 px-2 py-0.5 rounded text-zinc-500 hover:text-zinc-300"
              >
                ESC
              </button>
            </div>

            {/* Match list */}
            <div className="max-h-64 overflow-y-auto p-2">
              {filtered.map((cmd, idx) => {
                const Icon = cmd.icon;
                const active = idx === selectedIndex;
                return (
                  <button
                    key={cmd.id}
                    onClick={cmd.action}
                    className={`w-full text-left px-3 py-2 rounded-lg text-xs flex items-center justify-between transition-all ${
                      active 
                        ? "bg-emerald-600 text-white shadow" 
                        : "text-zinc-400 hover:bg-zinc-900/60 hover:text-zinc-200"
                    }`}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <Icon size={14} className={active ? "text-white" : "text-zinc-500"} />
                      <span className="truncate">{cmd.label}</span>
                    </div>
                    {cmd.shortcut && (
                      <span className={`font-mono text-[9px] px-2 py-0.5 rounded border ${
                        active 
                          ? "bg-emerald-700 border-emerald-500 text-emerald-100" 
                          : "bg-zinc-900 border-zinc-800 text-zinc-500"
                      }`}>
                        {cmd.shortcut}
                      </span>
                    )}
                  </button>
                );
              })}
              {filtered.length === 0 && (
                <p className="text-center text-xs text-zinc-500 py-6">No commands matching &ldquo;{query}&rdquo;</p>
              )}
            </div>

            {/* Key bindings Footer */}
            <div className="border-t border-zinc-800 px-4 py-2.5 bg-zinc-950 flex items-center justify-between text-[9px] text-zinc-500 font-mono">
              <div className="flex gap-3">
                <span className="flex items-center gap-1">
                  ↑↓ Navigation
                </span>
                <span className="flex items-center gap-1">
                  <CornerDownLeft size={10} /> Execute
                </span>
              </div>
              <span>Raycast Style Console</span>
            </div>

          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
