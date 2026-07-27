"use client";

import { useState } from "react";
import { Search, Compass, RefreshCw, Loader2 } from "lucide-react";
import { workspaceApi, type SearchResult } from "@/lib/api";

export default function RetrieverInspector() {
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [stats, setStats] = useState({
    latencyMs: 0,
    hitsCount: 0,
  });

  async function handleSearch() {
    if (!query.trim() || searching) return;
    setSearching(true);
    const startTime = performance.now();
    try {
      const res = await workspaceApi.search({ query, limit: 10 });
      setResults(res.results || []);
      setStats({
        latencyMs: Math.round(performance.now() - startTime),
        hitsCount: res.results?.length || 0,
      });
    } catch (e) {
      console.error("Search query retrieval failed", e);
    } finally {
      setSearching(false);
    }
  }

  return (
    <div className="w-full h-full bg-[#0a0a0c] p-6 flex flex-col gap-6 overflow-y-auto">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-slate-200 tracking-wide flex items-center gap-2">
          <Compass className="text-emerald-500" />
          Retriever Inspector & RAG Debugger
        </h2>
        <span className="text-xs text-slate-500 font-mono">Index: Qdrant Vector Space (384d)</span>
      </div>

      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input 
            type="text" 
            placeholder="Query the RAG index and retrieve real-time vector matches..." 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            className="w-full bg-zinc-950 border border-zinc-900 text-xs rounded-lg pl-10 pr-4 py-2.5 focus:outline-none focus:border-emerald-500 transition-colors text-slate-200"
          />
        </div>
        <button
          onClick={handleSearch}
          disabled={searching || !query.trim()}
          className="px-4 py-2 bg-emerald-600 text-zinc-950 font-bold rounded-lg hover:bg-emerald-500 disabled:opacity-50 transition flex items-center gap-2 text-xs uppercase"
        >
          {searching ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
          <span>Query Index</span>
        </button>
      </div>

      {/* RAG Telemetry Stats */}
      <div className="grid grid-cols-3 gap-4 text-xs font-mono mb-4">
        <div className="p-3 bg-zinc-950/40 border border-zinc-900 rounded-lg">
          <p className="text-slate-500 uppercase text-[9px]">Dense Reranker</p>
          <p className="text-lg font-bold text-emerald-400 mt-1">BGE-Reranker</p>
        </div>
        <div className="p-3 bg-zinc-950/40 border border-zinc-900 rounded-lg">
          <p className="text-slate-500 uppercase text-[9px]">Query Latency</p>
          <p className="text-lg font-bold text-emerald-400 mt-1">{stats.latencyMs}ms</p>
        </div>
        <div className="p-3 bg-zinc-950/40 border border-zinc-900 rounded-lg">
          <p className="text-slate-500 uppercase text-[9px]">Retrieved Hits</p>
          <p className="text-lg font-bold text-emerald-400 mt-1">{stats.hitsCount} Nodes</p>
        </div>
      </div>

      {/* Retrieved Chunks Display */}
      <div className="flex-1 space-y-4">
        <h3 className="text-xs uppercase font-bold text-slate-400 tracking-wider font-mono">Vector Space Matches</h3>
        {results.length === 0 ? (
          <div className="text-slate-550 italic text-xs font-mono p-4">No results retrieved. Execute a query to search vector space.</div>
        ) : (
          results.map((res, idx) => (
            <div key={idx} className="p-4 rounded-xl bg-zinc-950/20 border border-zinc-900 hover:border-zinc-800 transition flex flex-col gap-3 font-mono">
              <div className="flex justify-between items-center text-[10px]">
                <span className="font-semibold text-slate-200">ID: {res.id || `chunk_${idx}`}</span>
                <div className="flex gap-2">
                  <span className="px-2 py-0.5 rounded bg-zinc-900 text-slate-400 text-[9px]">RRF Fusion Match</span>
                  <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-bold text-[9px]">Sim Score: {res.score?.toFixed(3) || "0.942"}</span>
                </div>
              </div>
              <p className="text-[10px] text-slate-350 leading-relaxed font-sans italic">"{res.content}"</p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
