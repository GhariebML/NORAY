"use client";

import { useEffect, useState } from "react";
import { Network, GitCommit, RefreshCw } from "lucide-react";
import { workspaceApi } from "@/lib/api";

interface Triple {
  source: string;
  relation: string;
  target: string;
}

export default function KnowledgeGraph() {
  const [triples, setTriples] = useState<Triple[]>([]);
  const [nodes, setNodes] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  async function fetchGraphData() {
    setLoading(true);
    try {
      const data = await workspaceApi.getGraphTriples(30);
      setTriples(data.triples || []);
      setNodes(data.nodes || []);
    } catch (e) {
      console.error("Failed to load Knowledge Graph triples", e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchGraphData();
  }, []);

  return (
    <div className="w-full h-full bg-[#0a0a0c] p-6 flex flex-col gap-6 overflow-y-auto">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-slate-200 tracking-wide flex items-center gap-2">
          <Network className="text-emerald-500" />
          Semantic Knowledge Graph Explorer (GraphRAG)
        </h2>
        <button
          onClick={fetchGraphData}
          disabled={loading}
          className="p-1.5 rounded-lg border border-zinc-850 bg-zinc-950 text-slate-400 hover:text-slate-200 disabled:opacity-50 transition"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Visual Graph Layout */}
        <div className="lg:col-span-2 p-5 border border-zinc-900 rounded-xl bg-zinc-950/40 min-h-[300px] flex flex-col justify-between relative overflow-hidden">
          <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:16px_16px] opacity-20 pointer-events-none" />
          <div className="text-xs text-slate-400 font-semibold mb-4">Graph Graph Store Map Topology</div>
          
          <div className="flex-1 flex flex-wrap items-center justify-center gap-6 p-4">
            {nodes.length === 0 ? (
              <div className="text-slate-500 italic text-xs font-mono">No nodes indexed in graph context.</div>
            ) : (
              nodes.slice(0, 12).map((node, idx) => (
                <div key={idx} className="px-4 py-2 border border-emerald-500/20 bg-emerald-500/5 rounded-lg text-emerald-400 font-mono text-xs flex items-center gap-2 glow-emerald">
                  <GitCommit size={12} />
                  <span>{node}</span>
                </div>
              ))
            )}
          </div>
          
          <div className="text-[10px] text-slate-500 font-mono text-center">Interactive Graph Nodes Map representation</div>
        </div>

        {/* Semantic Triples List */}
        <div className="p-5 border border-zinc-900 rounded-xl bg-zinc-950/40 flex flex-col gap-4">
          <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Semantic Triples Registry</div>
          <div className="space-y-3 max-h-[300px] overflow-y-auto pr-1">
            {triples.length === 0 ? (
              <div className="text-slate-550 italic text-xs font-mono">Empty registry.</div>
            ) : (
              triples.map((t, idx) => (
                <div key={idx} className="p-2.5 border border-zinc-900 rounded bg-zinc-950/40 text-[10px] font-mono flex flex-col gap-1">
                  <div className="flex justify-between items-center text-slate-400">
                    <span className="text-emerald-400 truncate max-w-[120px]">{t.source}</span>
                    <span className="text-[8px] bg-zinc-900 px-1 rounded text-zinc-550 font-bold uppercase">{t.relation}</span>
                  </div>
                  <div className="text-right text-slate-300 truncate">{t.target}</div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
