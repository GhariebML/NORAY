"use client";

import { useEffect, useState } from "react";
import { Wrench, CheckCircle, RefreshCw } from "lucide-react";

interface MCPStatus {
  status: string;
  connected_servers: string[];
  discovered_tools_count: number;
}

export default function ToolRegistry() {
  const [status, setStatus] = useState<MCPStatus | null>(null);
  const [loading, setLoading] = useState(false);

  async function fetchToolStatus() {
    setLoading(true);
    try {
      const res = await fetch("/api/health/mcp");
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
      }
    } catch (e) {
      console.error("Failed to load tools registry state", e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchToolStatus();
  }, []);

  const tools = [
    { name: "crawl_job_postings", description: "Scrape online career websites for tailored matches", module: "career_agent", status: "ready", mcp: false },
    { name: "semantic_vector_search", description: "Cosine similarity dense vector retrieval", module: "retriever", status: "ready", mcp: false },
    { name: "entity_relation_triples", description: "SQLite Graph traversal relational miner", module: "retriever", status: "ready", mcp: false },
    { name: "ats_optimizer_engine", description: "Analyze resume keywords with model targets", module: "career_agent", status: "ready", mcp: false },
    { name: "filesystem_sidecar", description: "Local path documents filesystem navigator", module: "mcp_server", status: status?.status === "healthy" ? "connected" : "standby", mcp: true },
    { name: "web_search_duckduckgo", description: "Real-time query web crawling fetcher", module: "mcp_server", status: status?.status === "healthy" ? "connected" : "standby", mcp: true }
  ];

  return (
    <div className="w-full h-full bg-[#0a0a0c] p-6 flex flex-col gap-6 overflow-y-auto">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-slate-200 tracking-wide flex items-center gap-2">
          <Wrench className="text-emerald-500" />
          Capability Registry & MCP Tools
        </h2>
        <button
          onClick={fetchToolStatus}
          disabled={loading}
          className="p-1.5 rounded-lg border border-zinc-850 bg-zinc-950 text-slate-400 hover:text-slate-200 disabled:opacity-50 transition"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {tools.map((t, idx) => (
          <div key={idx} className="p-4 rounded-xl border border-zinc-900 bg-zinc-950/40 hover:border-zinc-850 transition flex flex-col justify-between gap-4">
            <div className="flex justify-between items-start">
              <div>
                <span className="font-mono text-xs font-bold text-slate-250">{t.name}</span>
                <p className="text-[9px] text-zinc-500 font-mono mt-0.5">Module: {t.module}</p>
              </div>
              <span className={`px-2 py-0.5 rounded text-[8px] uppercase font-bold tracking-wider ${t.status === "ready" || t.status === "connected" ? "bg-emerald-500/10 text-emerald-400" : "bg-zinc-900 text-zinc-500"}`}>
                {t.status}
              </span>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed font-sans">{t.description}</p>

            <div className="border-t border-zinc-900 pt-3 flex justify-between items-center text-[10px] text-slate-500 font-mono">
              <span>MCP Protocol: {t.mcp ? "Yes" : "No"}</span>
              <span className="flex items-center gap-1"><CheckCircle size={10} className="text-emerald-500" /> Secure Sandbox</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
