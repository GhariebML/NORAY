"use client";

import { useState } from "react";
import {
  BarChart3,
  Activity,
  Cpu,
  Zap,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Server,
  Shield,
  Layers,
} from "lucide-react";
import { PageHeader, Card, Badge } from "@/components/ui";

export default function AnalyticsPage() {
  const [providers] = useState([
    { name: "Google Gemini 1.5 Pro / Flash", tier: "Tier 1 (Cloud)", score: "100%", latency: "210ms", status: "Active", calls: 420 },
    { name: "OpenRouter AI", tier: "Tier 1 (Cloud)", score: "100%", latency: "185ms", status: "Active", calls: 310 },
    { name: "Together AI (Meta-Llama 3.1)", tier: "Tier 1 (Cloud)", score: "100%", latency: "240ms", status: "Active", calls: 180 },
    { name: "DeepSeek-Chat", tier: "Tier 1 (Cloud)", score: "100%", latency: "195ms", status: "Active", calls: 250 },
    { name: "Ollama (qwen2.5-coder:7b)", tier: "Tier 2 (Local)", score: "100%", latency: "420ms", status: "Active", calls: 890 },
  ]);

  return (
    <div>
      <PageHeader
        title="AI Telemetry & Provider Analytics"
        description="Real-time performance metrics, model routing telemetry, and token consumption analytics"
      />

      {/* Top Stat Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-6">
        <Card className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs text-zinc-400 font-medium">System Success Rate</span>
            <CheckCircle2 className="text-emerald-400" size={18} />
          </div>
          <p className="mt-2 text-2xl font-bold text-white font-heading">99.8%</p>
          <span className="text-[10px] text-emerald-400 font-mono">0 Failed Executions Today</span>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs text-zinc-400 font-medium">Average Latency</span>
            <Clock className="text-cyan-400" size={18} />
          </div>
          <p className="mt-2 text-2xl font-bold text-white font-heading">218ms</p>
          <span className="text-[10px] text-cyan-400 font-mono">-12ms vs Cloud Baseline</span>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs text-zinc-400 font-medium">Total Tokens Processed</span>
            <Cpu className="text-amber-400" size={18} />
          </div>
          <p className="mt-2 text-2xl font-bold text-white font-heading">1.42 M</p>
          <span className="text-[10px] text-amber-400 font-mono">24,500 Prompt / Day</span>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs text-zinc-400 font-medium">Dual-Tier Provider Score</span>
            <Zap className="text-emerald-400" size={18} />
          </div>
          <p className="mt-2 text-2xl font-bold text-emerald-400 font-heading">1.00 Max</p>
          <span className="text-[10px] text-emerald-400 font-mono">5 Active Routing Nodes</span>
        </Card>
      </div>

      {/* Provider Health Table */}
      <Card className="p-6">
        <h2 className="mb-4 text-base font-bold text-zinc-100 font-heading flex items-center gap-2">
          <Server className="text-emerald-400" size={20} />
          Model Router & Provider Telemetry Status
        </h2>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-zinc-800 text-zinc-400 uppercase text-[10px]">
                <th className="py-3 px-3">Provider Engine</th>
                <th className="py-3 px-3">Routing Tier</th>
                <th className="py-3 px-3">Health Score</th>
                <th className="py-3 px-3">Avg Latency</th>
                <th className="py-3 px-3">Total Requests</th>
                <th className="py-3 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60 text-zinc-200">
              {providers.map((p, i) => (
                <tr key={i} className="hover:bg-zinc-800/40 transition-colors">
                  <td className="py-3 px-3 font-semibold text-white flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                    {p.name}
                  </td>
                  <td className="py-3 px-3 text-zinc-400">{p.tier}</td>
                  <td className="py-3 px-3 font-bold text-emerald-400">{p.score}</td>
                  <td className="py-3 px-3 text-cyan-400">{p.latency}</td>
                  <td className="py-3 px-3 text-zinc-300">{p.calls}</td>
                  <td className="py-3 px-3">
                    <Badge variant="success" className="text-[10px]">
                      {p.status}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
