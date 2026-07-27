"use client";

import { useEffect, useState } from "react";
import { Server, RefreshCw } from "lucide-react";

interface Provider {
  provider: string;
  status: string;
  latency: number;
  available_models: string[];
  streaming: boolean;
  embeddings: boolean;
  tools: boolean;
}

interface HardwareInfo {
  cpu: string;
  ram_gb: number;
  gpu?: string;
  vram_gb?: number;
}

export default function ModelObservatory() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [hardware, setHardware] = useState<HardwareInfo | null>(null);
  const [loading, setLoading] = useState(false);

  async function fetchObservatoryData() {
    setLoading(true);
    try {
      const [provRes, diagRes] = await Promise.all([
        fetch("/api/system/providers"),
        fetch("/api/system/diagnostics")
      ]);
      if (provRes.ok) {
        const data = await provRes.json();
        setProviders(data.providers || []);
      }
      if (diagRes.ok) {
        const data = await diagRes.json();
        setHardware(data.hardware || null);
      }
    } catch (e) {
      console.error("Failed to load model observatory metrics", e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchObservatoryData();
  }, []);

  return (
    <div className="w-full h-full bg-[#0a0a0c] p-6 flex flex-col gap-6 overflow-y-auto">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-slate-200 tracking-wide flex items-center gap-2">
          <Server className="text-emerald-500" />
          Model Observatory & Local AI Center
        </h2>
        <button
          onClick={fetchObservatoryData}
          disabled={loading}
          className="p-1.5 rounded-lg border border-zinc-800 bg-zinc-950 text-slate-400 hover:text-slate-200 disabled:opacity-50 transition"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Providers Registry */}
        <div className="lg:col-span-2 space-y-4">
          <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">AI Providers Health & Fallback Routing</div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {providers.map((p, idx) => (
              <div key={idx} className="p-4 border border-zinc-900 bg-zinc-950/40 rounded-xl hover:border-zinc-800 transition flex flex-col justify-between gap-3">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-bold text-slate-200">{p.provider}</span>
                  <span className={`px-2 py-0.5 rounded text-[9px] uppercase font-bold tracking-wider ${p.status === "Healthy" ? "bg-emerald-500/10 text-emerald-400" : "bg-zinc-900 text-zinc-550"}`}>
                    {p.status}
                  </span>
                </div>
                <div className="text-[10px] text-slate-400 font-mono flex flex-col gap-1">
                  <span>Latency: <strong className="text-cyan-400">{p.latency}ms</strong></span>
                  <span>Models count: <strong className="text-amber-400">{p.available_models.length}</strong></span>
                </div>
                <div className="border-t border-zinc-900 pt-2 flex gap-1.5 flex-wrap">
                  {p.streaming && <span className="px-1.5 py-0.5 rounded bg-zinc-900 text-slate-500 text-[8px] font-mono">Stream</span>}
                  {p.embeddings && <span className="px-1.5 py-0.5 rounded bg-zinc-900 text-slate-500 text-[8px] font-mono">Embed</span>}
                  {p.tools && <span className="px-1.5 py-0.5 rounded bg-zinc-900 text-slate-500 text-[8px] font-mono">Tools</span>}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Local Hardware Observatory */}
        <div className="p-5 border border-zinc-900 rounded-xl bg-zinc-950/40 flex flex-col gap-4">
          <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">
            Local Hardware Telemetry
          </div>

          <div className="space-y-4 text-xs font-mono">
            <div className="p-3 bg-zinc-950 rounded border border-zinc-900">
              <span className="text-slate-500 block uppercase text-[9px]">GPU Platform</span>
              <span className="text-slate-200 font-bold mt-1 block truncate">{hardware?.gpu || "None / Integrated"}</span>
            </div>
            
            <div className="p-3 bg-zinc-950 rounded border border-zinc-900">
              <span className="text-slate-500 block uppercase text-[9px]">VRAM Footprint</span>
              <span className="text-emerald-400 font-bold mt-1 block">{hardware?.vram_gb ? `${hardware.vram_gb} GB` : "0 GB / Integrated"}</span>
            </div>

            <div className="p-3 bg-zinc-950 rounded border border-zinc-900">
              <span className="text-slate-500 block uppercase text-[9px]">CPU & System RAM</span>
              <span className="text-slate-200 mt-1 block truncate">RAM: {hardware?.ram_gb || 0} GB | CPU: {hardware?.cpu || "Detected"}</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
