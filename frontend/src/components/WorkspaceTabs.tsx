"use client";

import React from "react";
import { useRouter, usePathname } from "next/navigation";
import {
  Sparkles,
  Briefcase,
  GraduationCap,
  FileText,
  Brain,
  BarChart3,
  X,
  Plus,
  Layers,
} from "lucide-react";

export interface TabItem {
  id: string;
  title: string;
  href: string;
  icon: React.ElementType;
}

const DEFAULT_TABS: TabItem[] = [
  { id: "workspace", title: "AI Workspace Canvas", href: "/workspace", icon: Sparkles },
  { id: "jobs", title: "Job Search", href: "/jobs", icon: Briefcase },
  { id: "scholarships", title: "Scholarships", href: "/scholarships", icon: GraduationCap },
  { id: "documents", title: "Document Generator", href: "/documents", icon: FileText },
  { id: "tracker", title: "Applications Tracker", href: "/tracker", icon: Layers },
  { id: "memory", title: "AI Memory Center", href: "/memory", icon: Brain },
  { id: "analytics", title: "AI Telemetry", href: "/analytics", icon: BarChart3 },
];

export function WorkspaceTabs() {
  const router = useRouter();
  const pathname = usePathname();
  const [tabs, setTabs] = React.useState<TabItem[]>(DEFAULT_TABS);

  const removeTab = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (tabs.length <= 1) return; // Keep at least one tab
    const nextTabs = tabs.filter((t) => t.id !== id);
    setTabs(nextTabs);
    if (pathname.includes(id)) {
      router.push(nextTabs[0].href);
    }
  };

  return (
    <div className="flex items-center gap-1 border-b border-slate-800/80 bg-[#090e1a]/95 backdrop-blur-md px-3 py-1.5 overflow-x-auto text-xs select-none">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = pathname === tab.href || (tab.href !== "/" && pathname.startsWith(tab.href));

        return (
          <div
            key={tab.id}
            onClick={() => router.push(tab.href)}
            className={`group relative flex items-center gap-2 rounded-md px-3 py-1.5 font-medium transition-all cursor-pointer ${
              isActive
                ? "bg-[#131c31] text-emerald-300 border border-emerald-500/40 shadow-lg shadow-emerald-500/10 font-semibold"
                : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200 border border-transparent"
            }`}
          >
            <Icon size={14} className={isActive ? "text-emerald-400" : "text-zinc-500 group-hover:text-zinc-300"} />
            <span className="whitespace-nowrap font-sans">{tab.title}</span>

            {/* Active Indicator Pulse */}
            {isActive && (
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            )}

            {/* Close Tab Button */}
            {tabs.length > 1 && (
              <button
                onClick={(e) => removeTab(e, tab.id)}
                className="ml-1 rounded p-0.5 opacity-0 group-hover:opacity-100 hover:bg-zinc-700/80 text-zinc-400 hover:text-zinc-200 transition-opacity"
              >
                <X size={12} />
              </button>
            )}
          </div>
        );
      })}

      {/* Quick Add Tab */}
      <button
        onClick={() => router.push("/workspace")}
        className="flex items-center gap-1 rounded-md px-2 py-1.5 text-zinc-500 hover:bg-zinc-800/50 hover:text-zinc-300 transition-colors"
        title="Open Workspace Canvas"
      >
        <Plus size={14} />
      </button>
    </div>
  );
}
