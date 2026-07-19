"use client";

import { useState, useEffect, useRef } from "react";
import {
  Search,
  Globe,
  Terminal,
  FileText,
  Sparkles,
  Activity,
  Briefcase,
  GraduationCap,
  Brain,
  BarChart3,
  Settings,
  Layers,
  User,
  Plus,
  CornerDownLeft,
} from "lucide-react";
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
      id: "nav-workspace",
      category: "navigation",
      label: "Open AI Workspace Canvas",
      shortcut: "G W",
      icon: Sparkles,
      action: () => { router.push("/workspace"); onClose(); }
    },
    {
      id: "nav-jobs",
      category: "navigation",
      label: "Search Jobs & Roles",
      shortcut: "G J",
      icon: Briefcase,
      action: () => { router.push("/jobs"); onClose(); }
    },
    {
      id: "nav-scholarships",
      category: "navigation",
      label: "Discover Fully-Funded Scholarships",
      shortcut: "G S",
      icon: GraduationCap,
      action: () => { router.push("/scholarships"); onClose(); }
    },
    {
      id: "nav-documents",
      category: "navigation",
      label: "Open Document Generator (CV, SOP, Research)",
      shortcut: "G D",
      icon: FileText,
      action: () => { router.push("/documents"); onClose(); }
    },
    {
      id: "nav-tracker",
      category: "navigation",
      label: "Open Applications Kanban Tracker",
      shortcut: "G T",
      icon: Layers,
      action: () => { router.push("/tracker"); onClose(); }
    },
    {
      id: "nav-memory",
      category: "navigation",
      label: "Open AI Memory Center & Facts Index",
      shortcut: "G M",
      icon: Brain,
      action: () => { router.push("/memory"); onClose(); }
    },
    {
      id: "nav-analytics",
      category: "navigation",
      label: "Open AI Telemetry & Analytics",
      shortcut: "G A",
      icon: BarChart3,
      action: () => { router.push("/analytics"); onClose(); }
    },
    {
      id: "nav-profile",
      category: "navigation",
      label: "Edit Canonical Profile",
      shortcut: "G P",
      icon: User,
      action: () => { router.push("/profile"); onClose(); }
    },
    {
      id: "nav-settings",
      category: "navigation",
      label: "Open System Settings & API Keys",
      shortcut: "G K",
      icon: Settings,
      action: () => { router.push("/settings"); onClose(); }
    },
    {
      id: "action-gen-cv",
      category: "actions",
      label: "Generate Tailored Resume / CV",
      shortcut: "A C",
      icon: FileText,
      action: () => { router.push("/documents"); onClose(); }
    },
    {
      id: "action-gen-sop",
      category: "actions",
      label: "Draft Statement of Purpose (SOP)",
      shortcut: "A S",
      icon: Sparkles,
      action: () => { router.push("/documents"); onClose(); }
    },
  ];

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

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % (filtered.length || 1));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex((prev) => (prev - 1 + (filtered.length || 1)) % (filtered.length || 1));
      } else if (e.key === "Enter") {
        e.preventDefault();
        if (filtered[selectedIndex]) {
          filtered[selectedIndex].action();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, selectedIndex, filtered, onClose]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-start justify-center pt-20">
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/70 backdrop-blur-sm"
          onClick={onClose}
        />

        <motion.div 
          initial={{ opacity: 0, scale: 0.96, y: -10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.96, y: -10 }}
          transition={{ duration: 0.15, ease: "easeOut" }}
          className="relative w-full max-w-xl overflow-hidden rounded-xl border border-zinc-800 bg-[#111827] shadow-2xl z-50"
        >
          {/* Input Header */}
          <div className="flex items-center border-b border-zinc-800 px-4 py-3.5">
            <Search className="mr-3 text-emerald-400" size={18} />
            <input
              ref={inputRef}
              type="text"
              placeholder="Type a command or search actions (e.g., Generate Resume, Search Scholarships)..."
              value={query}
              onChange={(e) => { setQuery(e.target.value); setSelectedIndex(0); }}
              className="w-full bg-transparent text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none"
            />
            <span className="rounded bg-zinc-800 border border-zinc-700 px-2 py-0.5 text-[10px] text-zinc-400 font-mono">ESC</span>
          </div>

          {/* Results List */}
          <div className="max-h-80 overflow-y-auto p-2">
            {filtered.length === 0 ? (
              <div className="p-6 text-center text-xs text-zinc-500">
                No matching system commands found.
              </div>
            ) : (
              filtered.map((cmd, index) => {
                const Icon = cmd.icon;
                const isSelected = index === selectedIndex;

                return (
                  <div
                    key={cmd.id}
                    onClick={cmd.action}
                    onMouseEnter={() => setSelectedIndex(index)}
                    className={`flex items-center justify-between rounded-lg px-3 py-2.5 text-xs transition-colors cursor-pointer ${
                      isSelected
                        ? "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30"
                        : "text-zinc-300 hover:bg-zinc-800/60 border border-transparent"
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon size={16} className={isSelected ? "text-emerald-400" : "text-zinc-500"} />
                      <span className="font-medium">{cmd.label}</span>
                    </div>

                    <div className="flex items-center gap-2">
                      {cmd.shortcut && (
                        <span className="rounded bg-zinc-800 border border-zinc-700 px-1.5 py-0.5 text-[10px] text-zinc-400 font-mono">
                          {cmd.shortcut}
                        </span>
                      )}
                      {isSelected && <CornerDownLeft size={12} className="text-emerald-400" />}
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Footer Bar */}
          <div className="flex items-center justify-between border-t border-zinc-800 bg-[#0b111e] px-4 py-2 text-[10px] text-zinc-500 font-mono">
            <span>NORAY AI Operating System</span>
            <div className="flex items-center gap-3">
              <span>↑↓ Navigate</span>
              <span>↵ Select</span>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
