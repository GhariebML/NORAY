"use client";

import { useEffect, useState, useCallback } from "react";
import {
  BarChart3, CheckCircle2, Server, Shield, RefreshCw, DollarSign, FileText
} from "lucide-react";
import { PageHeader, Card, Badge } from "@/components/ui";
import { smartRouterApi, type SmartRouterStatus, type ProviderAnalyticsData } from "@/lib/api";

type SortKey = "requests" | "latency" | "success" | "tokens" | "cost";

export default function ProviderAnalyticsDashboard() {
  const [status, setStatus] = useState<SmartRouterStatus | null>(null);
  const [analytics, setAnalytics] = useState<ProviderAnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sortBy, setSortBy] = useState<SortKey>("requests");
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [statusData, analyticsData] = await Promise.all([
        smartRouterApi.getStatus(),
        smartRouterApi.getAnalytics(),
      ]);
      setStatus(statusData);
      setAnalytics(analyticsData);
      setError("");
    } catch (err: any) {
      setError(err.message || "Failed to fetch analytics");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    if (!autoRefresh) return;
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, [fetchData, autoRefresh]);

  const agg = analytics?.aggregated;
  const providers = analytics?.providers
    ? Object.values(analytics.providers).sort((a: any, b: any) => {
        switch (sortBy) {
          case "latency": return b.average_latency_ms - a.average_latency_ms;
          case "success": return b.success_rate - a.success_rate;
          case "tokens": return (b.total_tokens_input + b.total_tokens_output) - (a.total_tokens_input + a.total_tokens_output);
          case "cost": return b.total_estimated_cost - a.total_estimated_cost;
          default: return b.total_requests - a.total_requests;
        }
      })
    : [];

  const healthMap = status?.health || {};
  const maxRequests = Math.max(...providers.map((p: any) => p.total_requests), 1);

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <PageHeader
          title="Provider Analytics"
          description="Real-time provider performance, routing metrics, and health monitoring"
        />
        <div className="flex items-center gap-2">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`text-[10px] px-2 py-1 rounded border font-mono ${
              autoRefresh
                ? "bg-emerald-950/20 border-emerald-500/20 text-emerald-400"
                : "bg-zinc-900 border-zinc-800 text-zinc-500"
            }`}
          >
            {autoRefresh ? "Auto-refresh ON" : "Auto-refresh OFF"}
          </button>
          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-1 text-[10px] px-2 py-1 rounded border border-zinc-800 bg-zinc-900 text-zinc-400 hover:text-white"
          >
            <RefreshCw size={10} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-lg bg-red-950/20 border border-red-500/20 text-red-400 text-[11px] font-mono">
          {error}
        </div>
      )}

      {/* Stat Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-6">
        <Card className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs text-zinc-400 font-medium">Overall Success Rate</span>
            <CheckCircle2 className="text-emerald-400" size={18} />
          </div>
          <p className="mt-2 text-2xl font-bold text-white font-heading">
            {agg ? `${agg.overall_success_rate}%` : "—"}
          </p>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-[10px] text-emerald-400 font-mono">
              {agg ? `${agg.total_successful} / ${agg.total_requests} requests` : ""}
            </span>
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs text-zinc-400 font-medium">Active Providers</span>
            <Server className="text-cyan-400" size={18} />
          </div>
          <p className="mt-2 text-2xl font-bold text-white font-heading">
            {agg ? `${agg.active_providers} / ${agg.total_providers}` : "—"}
          </p>
          <div className="mt-1 flex gap-1">
            {Object.entries(healthMap).slice(0, 8).map(([name, h]: [string, any]) => (
              <span
                key={name}
                className={`w-2 h-2 rounded-full ${
                  h.healthy ? "bg-emerald-400" : h.status === "quarantined" ? "bg-amber-400" : "bg-red-400"
                }`}
                title={`${name}: ${h.status}`}
              />
            ))}
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs text-zinc-400 font-medium">Total Tokens</span>
            <FileText className="text-amber-400" size={18} />
          </div>
          <p className="mt-2 text-2xl font-bold text-white font-heading">
            {agg ? (agg.total_tokens / 1000).toFixed(1) + "K" : "—"}
          </p>
          <span className="text-[10px] text-amber-400 font-mono">
            Total across all providers
          </span>
        </Card>

        <Card className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs text-zinc-400 font-medium">Est. Total Cost</span>
            <DollarSign className="text-emerald-400" size={18} />
          </div>
          <p className="mt-2 text-2xl font-bold text-emerald-400 font-heading">
            ${agg?.total_estimated_cost?.toFixed(4) || "—"}
          </p>
          <span className="text-[10px] text-zinc-500 font-mono">
            Cumulative across all providers
          </span>
        </Card>
      </div>

      {/* Provider Comparison */}
      <Card className="p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold text-zinc-100 font-heading flex items-center gap-2">
            <BarChart3 className="text-emerald-400" size={20} />
            Provider Performance Comparison
          </h2>
          <div className="flex items-center gap-1.5">
            {(["requests", "latency", "success", "tokens"] as SortKey[]).map((key) => (
              <button
                key={key}
                onClick={() => setSortBy(key)}
                className={`text-[9px] px-2 py-1 rounded-full uppercase font-bold tracking-wider ${
                  sortBy === key
                    ? "bg-emerald-950/20 text-emerald-400 border border-emerald-500/20"
                    : "text-zinc-500 hover:text-zinc-300"
                }`}
              >
                {key}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-3">
          {providers.length === 0 && !loading && (
            <div className="text-center py-8 text-zinc-500 text-[11px]">
              No provider data yet. Make some requests to see analytics.
            </div>
          )}

          {providers.map((p: any) => {
            const health = healthMap[p.provider];
            const isHealthy = health?.healthy;
            const circuitState = health?.circuit_state;
            const barWidth = (p.total_requests / maxRequests) * 100;

            return (
              <div key={p.provider} className="border border-zinc-800/60 rounded-lg p-3 hover:bg-zinc-800/20 transition-colors">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${
                      isHealthy ? "bg-emerald-400" : circuitState === "open" ? "bg-amber-400" : "bg-red-400"
                    }`} />
                    <span className="text-xs font-semibold text-white capitalize">{p.provider}</span>
                    {circuitState && circuitState !== "closed" && (
                      <Badge variant="warning" className="text-[9px]">
                        {circuitState}
                      </Badge>
                    )}
                    {health?.last_error && (
                      <span className="text-[9px] text-red-400 truncate max-w-[200px]">
                        {health.last_error}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 text-[10px] text-zinc-400">
                    <span>{p.total_requests} req</span>
                    <span>{p.average_latency_ms}ms</span>
                    <span className={p.success_rate >= 90 ? "text-emerald-400" : "text-amber-400"}>
                      {p.success_rate}%
                    </span>
                  </div>
                </div>

                {/* Request volume bar */}
                <div className="w-full bg-zinc-800 rounded-full h-1.5">
                  <div
                    className={`h-1.5 rounded-full transition-all duration-500 ${
                      isHealthy ? "bg-emerald-500" : "bg-red-500"
                    }`}
                    style={{ width: `${barWidth}%` }}
                  />
                </div>

                <div className="flex items-center gap-4 mt-2 text-[9px] text-zinc-500 font-mono">
                  <span>Tokens: {(p.total_tokens_input + p.total_tokens_output).toLocaleString()}</span>
                  <span>Cost: ${p.total_estimated_cost?.toFixed(6) || "0"}</span>
                  <span>Tokens/s: {p.tokens_per_second}</span>
                </div>
              </div>
            );
          })}

          {loading && (
            <div className="flex items-center justify-center py-8 text-zinc-500">
              <RefreshCw size={14} className="animate-spin mr-2" />
              Loading analytics...
            </div>
          )}
        </div>
      </Card>

      {/* Status & Circuit Breaker */}
      <Card className="p-6">
        <h2 className="mb-4 text-base font-bold text-zinc-100 font-heading flex items-center gap-2">
          <Shield className="text-emerald-400" size={20} />
          Circuit Breaker & Health Status
        </h2>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-zinc-800 text-zinc-400 uppercase text-[10px]">
                <th className="py-3 px-3">Provider</th>
                <th className="py-3 px-3">Status</th>
                <th className="py-3 px-3">Circuit</th>
                <th className="py-3 px-3">Latency</th>
                <th className="py-3 px-3">Uptime</th>
                <th className="py-3 px-3">Failures</th>
                <th className="py-3 px-3">Last Error</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60 text-zinc-200">
              {Object.entries(healthMap).map(([name, h]: [string, any]) => (
                <tr key={name} className="hover:bg-zinc-800/40 transition-colors">
                  <td className="py-3 px-3 font-semibold text-white capitalize flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${
                      h.healthy ? "bg-emerald-400" : h.status === "quarantined" ? "bg-amber-400" : "bg-red-400"
                    }`} />
                    {name}
                  </td>
                  <td className="py-3 px-3">
                    <Badge variant={h.healthy ? "success" : h.status === "quarantined" ? "warning" : "danger"} className="text-[10px]">
                      {h.status}
                    </Badge>
                  </td>
                  <td className="py-3 px-3">
                    <span className={`font-semibold ${
                      h.circuit_state === "closed" ? "text-emerald-400" :
                      h.circuit_state === "half_open" ? "text-amber-400" : "text-red-400"
                    }`}>
                      {h.circuit_state}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-cyan-400">{h.latency_ms.toFixed(1)}ms</td>
                  <td className="py-3 px-3 text-emerald-400">{h.uptime_percentage}%</td>
                  <td className="py-3 px-3">{h.consecutive_failures}</td>
                  <td className="py-3 px-3 text-red-400 text-[9px] max-w-[200px] truncate">
                    {h.last_error || "—"}
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
