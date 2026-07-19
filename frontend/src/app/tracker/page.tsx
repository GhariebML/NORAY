"use client";

import { useEffect, useState } from "react";
import {
  Layers,
  Briefcase,
  GraduationCap,
  Plus,
  ArrowRight,
  CheckCircle2,
  Clock,
  Sparkles,
  ChevronRight,
  ChevronLeft,
} from "lucide-react";
import { PageHeader, Card, Button, Badge } from "@/components/ui";

export interface KanbanApplication {
  id: string;
  title: string;
  companyOrOrg: string;
  type: "job" | "scholarship";
  status: "preparing" | "applied" | "interview" | "offer" | "accepted" | "rejected";
  deadline: string;
  matchScore: number;
}

const KANBAN_COLUMNS: { id: KanbanApplication["status"]; label: string; color: string }[] = [
  { id: "preparing", label: "Preparing SOP / Resume", color: "border-amber-500/40 text-amber-400 bg-amber-500/10" },
  { id: "applied", label: "Submitted / Applied", color: "border-cyan-500/40 text-cyan-400 bg-cyan-500/10" },
  { id: "interview", label: "Interview Scheduled", color: "border-purple-500/40 text-purple-400 bg-purple-500/10" },
  { id: "offer", label: "Offer Received", color: "border-emerald-500/40 text-emerald-400 bg-emerald-500/10" },
  { id: "accepted", label: "Accepted & Enrolled", color: "border-green-500/40 text-green-400 bg-green-500/10" },
  { id: "rejected", label: "Archived / Rejected", color: "border-zinc-700 text-zinc-400 bg-zinc-800/40" },
];

export default function TrackerPage() {
  const [items, setItems] = useState<KanbanApplication[]>([
    {
      id: "a1",
      title: "Senior Machine Learning Engineer",
      companyOrOrg: "Google AI Research",
      type: "job",
      status: "interview",
      deadline: "2026-08-15",
      matchScore: 96,
    },
    {
      id: "a2",
      title: "DAAD EPOS Postgraduate Scholarship",
      companyOrOrg: "DAAD Germany",
      type: "scholarship",
      status: "applied",
      deadline: "2026-10-31",
      matchScore: 98,
    },
    {
      id: "a3",
      title: "Chevening Master's Fellowship",
      companyOrOrg: "UK Foreign & Commonwealth Office",
      type: "scholarship",
      status: "preparing",
      deadline: "2026-11-05",
      matchScore: 95,
    },
    {
      id: "a4",
      title: "Lead RAG Architect",
      companyOrOrg: "Anthropic / OpenAI Partner Network",
      type: "job",
      status: "offer",
      deadline: "2026-07-30",
      matchScore: 97,
    },
  ]);

  function moveStatus(id: string, direction: "next" | "prev") {
    const statuses: KanbanApplication["status"][] = ["preparing", "applied", "interview", "offer", "accepted", "rejected"];
    setItems((prev) =>
      prev.map((item) => {
        if (item.id !== id) return item;
        const currIdx = statuses.indexOf(item.status);
        const nextIdx = direction === "next" ? Math.min(currIdx + 1, statuses.length - 1) : Math.max(currIdx - 1, 0);
        return { ...item, status: statuses[nextIdx] };
      })
    );
  }

  return (
    <div>
      <PageHeader
        title="Application Kanban Pipeline"
        description="Track your job and scholarship applications across real-time stage columns"
      />

      {/* Kanban Board Layout */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 overflow-x-auto pb-6">
        {KANBAN_COLUMNS.map((col) => {
          const colItems = items.filter((i) => i.status === col.id);

          return (
            <div
              key={col.id}
              className="flex flex-col rounded-xl border border-zinc-800 bg-[#111827]/90 p-3 min-w-[240px] shadow-xl"
            >
              {/* Column Header */}
              <div className="mb-3 flex items-center justify-between border-b border-zinc-800 pb-2">
                <span className={`rounded-md border px-2 py-0.5 text-xs font-semibold ${col.color}`}>
                  {col.label}
                </span>
                <span className="text-xs font-mono font-bold text-zinc-400">{colItems.length}</span>
              </div>

              {/* Column Cards */}
              <div className="flex-1 space-y-3 min-h-[300px]">
                {colItems.length === 0 ? (
                  <div className="flex h-32 items-center justify-center rounded-lg border border-dashed border-zinc-800 p-4 text-center text-[11px] text-zinc-600">
                    No applications in this stage
                  </div>
                ) : (
                  colItems.map((item) => (
                    <div
                      key={item.id}
                      className="group relative rounded-lg border border-zinc-800 bg-[#161f2d] p-3.5 shadow-md transition-all hover:border-emerald-500/40 hover:shadow-emerald-500/5 space-y-2.5"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <span className="inline-flex items-center gap-1 rounded bg-zinc-800 px-1.5 py-0.5 text-[10px] font-medium text-emerald-400">
                            {item.type === "job" ? <Briefcase size={10} /> : <GraduationCap size={10} />}
                            {item.type.toUpperCase()}
                          </span>
                          <h4 className="mt-1.5 text-xs font-bold text-zinc-100 line-clamp-2">
                            {item.title}
                          </h4>
                          <p className="text-[11px] text-zinc-400 font-medium">{item.companyOrOrg}</p>
                        </div>

                        <span className="rounded-full bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 text-[10px] font-mono font-bold text-emerald-400 shrink-0">
                          {item.matchScore}%
                        </span>
                      </div>

                      <div className="flex items-center justify-between border-t border-zinc-800/80 pt-2 text-[10px] font-mono text-zinc-500">
                        <span className="flex items-center gap-1">
                          <Clock size={11} /> {item.deadline}
                        </span>

                        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={() => moveStatus(item.id, "prev")}
                            className="rounded p-1 hover:bg-zinc-800 hover:text-white"
                            title="Move to previous stage"
                          >
                            <ChevronLeft size={13} />
                          </button>
                          <button
                            onClick={() => moveStatus(item.id, "next")}
                            className="rounded p-1 hover:bg-zinc-800 hover:text-white"
                            title="Move to next stage"
                          >
                            <ChevronRight size={13} />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
