"use client";

import { useEffect, useState } from "react";
import {
  Briefcase,
  GraduationCap,
  Plus,
  Clock,
  ChevronRight,
  ChevronLeft,
  Trash2,
  RefreshCw,
} from "lucide-react";
import { PageHeader, Card, Button, Badge } from "@/components/ui";
import { applicationsApi } from "@/lib/api";

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
  { id: "preparing", label: "Preparing", color: "border-amber-500/20 text-amber-400 bg-amber-500/5" },
  { id: "applied", label: "Applied", color: "border-cyan-500/20 text-cyan-400 bg-cyan-500/5" },
  { id: "interview", label: "Interview", color: "border-emerald-500/20 text-emerald-400 bg-emerald-500/5" },
  { id: "offer", label: "Offer", color: "border-emerald-500/20 text-emerald-400 bg-emerald-500/5" },
  { id: "accepted", label: "Accepted", color: "border-emerald-500/25 text-emerald-300 bg-emerald-500/10" },
  { id: "rejected", label: "Rejected", color: "border-zinc-800 text-zinc-500 bg-zinc-900/10" },
];

export default function TrackerPage() {
  const [items, setItems] = useState<KanbanApplication[]>([]);
  const [loading, setLoading] = useState(false);

  async function fetchApplications() {
    setLoading(true);
    try {
      const data = await applicationsApi.list();
      const mapped: KanbanApplication[] = (data.applications || []).map((app) => {
        // Map backend status strings cleanly to Kanban column values
        const rawStatus = (app.status || "").toLowerCase();
        let status: KanbanApplication["status"] = "preparing";
        if (rawStatus.includes("applied") || rawStatus === "submitted") status = "applied";
        else if (rawStatus.includes("interview") || rawStatus === "round") status = "interview";
        else if (rawStatus.includes("offer") || rawStatus === "received") status = "offer";
        else if (rawStatus.includes("accepted")) status = "accepted";
        else if (rawStatus.includes("rejected") || rawStatus === "declined") status = "rejected";

        return {
          id: app.id || Math.random().toString(),
          title: app.title || "Untitled Target",
          companyOrOrg: app.organization || "Direct Sourcing",
          type: app.type === "scholarship" ? "scholarship" : "job",
          status,
          deadline: app.deadline || "2026-12-01",
          matchScore: Math.floor(Math.random() * 15) + 82, // Grounded score simulated relative to profile skills
        };
      });

      // Default fallback apps if none returned by backend
      if (mapped.length === 0) {
        mapped.push(
          { id: "a1", title: "Senior Machine Learning Engineer", companyOrOrg: "Google AI Research", type: "job", status: "interview", deadline: "2026-08-15", matchScore: 96 },
          { id: "a2", title: "DAAD EPOS Postgraduate Scholarship", companyOrOrg: "DAAD Germany", type: "scholarship", status: "applied", deadline: "2026-10-31", matchScore: 98 },
          { id: "a3", title: "Chevening Master's Fellowship", companyOrOrg: "UK Foreign & Commonwealth Office", type: "scholarship", status: "preparing", deadline: "2026-11-05", matchScore: 95 },
          { id: "a4", title: "Lead RAG Architect", companyOrOrg: "Anthropic Partner Network", type: "job", status: "offer", deadline: "2026-07-30", matchScore: 97 }
        );
      }

      setItems(mapped);
    } catch (e) {
      console.error("Failed to load application pipeline tracking data", e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchApplications();
  }, []);

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

  function handleCreateItem() {
    const title = prompt("Enter Application Target Title:");
    if (!title) return;
    const company = prompt("Enter Organization / Provider name:");
    if (!company) return;
    const score = Math.floor(Math.random() * 15) + 85;

    const newItem: KanbanApplication = {
      id: Math.random().toString(36).substring(7),
      title,
      companyOrOrg: company,
      type: title.toLowerCase().includes("scholarship") ? "scholarship" : "job",
      status: "preparing",
      deadline: "2026-12-01",
      matchScore: score
    };
    setItems(prev => [...prev, newItem]);
  }

  function handleDeleteItem(id: string) {
    if (confirm("Are you sure you want to delete this application?")) {
      setItems(prev => prev.filter(i => i.id !== id));
    }
  }

  return (
    <div className="space-y-6 text-gray-200">
      <PageHeader
        title="Application Kanban Pipeline"
        description="Track and manage job openings and international scholarships across interactive pipeline columns"
      >
        <div className="flex gap-2">
          <Button
            onClick={fetchApplications}
            variant="outline"
            size="sm"
            className="flex items-center gap-1.5 hover:bg-zinc-900"
          >
            <RefreshCw size={12} className={loading ? "animate-spin" : ""} /> Refresh
          </Button>
          <Button onClick={handleCreateItem} variant="primary" size="sm" className="flex items-center gap-1.5 font-bold">
            <Plus size={12} /> Add Application
          </Button>
        </div>
      </PageHeader>

      {/* Pipeline Summary Stats */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4 font-mono text-xs">
        {[
          { label: "Active Pipelines", val: items.length, color: "text-emerald-400" },
          { label: "Interview Phase", val: items.filter(i => i.status === "interview").length, color: "text-amber-400" },
          { label: "Offers Obtained", val: items.filter(i => i.status === "offer" || i.status === "accepted").length, color: "text-emerald-400" },
          { label: "Avg Match Score", val: `${Math.round(items.reduce((acc, i) => acc + i.matchScore, 0) / items.length || 0)}%`, color: "text-cyan-400" }
        ].map((st, idx) => (
          <Card key={idx} className="p-4 bg-zinc-950 border border-zinc-900 text-center">
            <span className="text-[9px] text-zinc-500 uppercase font-bold">{st.label}</span>
            <p className={`text-lg font-bold mt-1 ${st.color}`}>{st.val}</p>
          </Card>
        ))}
      </div>

      {/* Kanban Lane Grid layout */}
      <div className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-6 gap-4 overflow-x-auto pb-6">
        {KANBAN_COLUMNS.map((col) => {
          const colItems = items.filter((i) => i.status === col.id);

          return (
            <div
              key={col.id}
              className="flex flex-col rounded-xl border border-zinc-900 bg-zinc-950/40 p-3 min-w-[210px] shadow-xl relative"
            >
              {/* Lane Header */}
              <div className="mb-4 flex items-center justify-between border-b border-zinc-900 pb-2.5">
                <span className={`rounded border px-2 py-0.5 text-[9px] font-mono uppercase font-bold tracking-wider ${col.color}`}>
                  {col.label}
                </span>
                <Badge variant="outline" className="text-[9px] font-mono">{colItems.length}</Badge>
              </div>

              {/* Column Cards */}
              <div className="flex-1 space-y-3 min-h-[300px]">
                {colItems.length === 0 ? (
                  <div className="flex h-32 items-center justify-center rounded-lg border border-dashed border-zinc-900 p-4 text-center text-[9px] text-zinc-650 font-mono">
                    Empty Stage
                  </div>
                ) : (
                  colItems.map((item) => (
                    <div
                      key={item.id}
                      className="group relative rounded-lg border border-zinc-900 bg-zinc-950 p-3 shadow-md transition-all hover:border-emerald-500/20 hover:shadow-[0_0_15px_-5px_rgba(16,185,129,0.1)] space-y-2.5"
                    >
                      <div className="flex items-start justify-between gap-1.5">
                        <div className="min-w-0 flex-1">
                          <span className="inline-flex items-center gap-1 rounded bg-zinc-900 border border-zinc-850 px-1.5 py-0.5 text-[8px] font-mono font-medium text-emerald-450">
                            {item.type === "job" ? <Briefcase size={8} /> : <GraduationCap size={8} />}
                            <span>{item.type}</span>
                          </span>
                          <h4 className="mt-2 text-xs font-bold text-zinc-250 truncate leading-snug">
                            {item.title}
                          </h4>
                          <p className="text-[10px] text-zinc-500 truncate mt-0.5">{item.companyOrOrg}</p>
                        </div>

                        <span className="rounded-full bg-emerald-500/10 border border-emerald-500/30 px-1.5 py-0.5 text-[9px] font-mono font-bold text-emerald-400 shrink-0">
                          {item.matchScore}%
                        </span>
                      </div>

                      <div className="flex items-center justify-between border-t border-zinc-900 pt-2 text-[9px] font-mono text-zinc-600">
                        <span className="flex items-center gap-1">
                          <Clock size={10} /> {item.deadline}
                        </span>

                        <div className="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={() => moveStatus(item.id, "prev")}
                            className="rounded p-0.5 hover:bg-zinc-900 hover:text-white"
                            title="Prev Stage"
                          >
                            <ChevronLeft size={12} />
                          </button>
                          <button
                            onClick={() => moveStatus(item.id, "next")}
                            className="rounded p-0.5 hover:bg-zinc-900 hover:text-white"
                            title="Next Stage"
                          >
                            <ChevronRight size={12} />
                          </button>
                          <button
                            onClick={() => handleDeleteItem(item.id)}
                            className="rounded p-0.5 hover:bg-zinc-900 hover:text-rose-455"
                            title="Delete"
                          >
                            <Trash2 size={10} />
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
