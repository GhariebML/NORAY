"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Wifi, WifiOff, Cpu, Zap, RefreshCw,
} from "lucide-react";
import { smartRouterApi, type SmartRouterStatus } from "@/lib/api";

interface ProviderStatusBarProps {
  className?: string;
}

export default function ProviderStatusBar({ className = "" }: ProviderStatusBarProps) {
  const [status, setStatus] = useState<SmartRouterStatus | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchStatus = useCallback(async () => {
    setLoading(true);
    try {
      const data = await smartRouterApi.getStatus();
      setStatus(data);
    } catch {
      // Silently fail — component is non-critical
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  if (!status) {
    return (
      <div className={`flex items-center gap-2 text-[10px] text-zinc-500 ${className}`}>
        <RefreshCw size={10} className="animate-spin" />
        <span>Connecting to router...</span>
      </div>
    );
  }

  const { status: s } = status;
  const isOffline = status.offline_mode;
  const isLocal = s.is_local;

  let providerLabel = s.current_provider;
  let modeBadge = s.mode_label;
  let iconColor = "text-emerald-400";

  if (isOffline) {
    providerLabel = "Offline Knowledge";
    modeBadge = "Offline Mode";
    iconColor = "text-amber-400";
  } else if (isLocal) {
    iconColor = "text-blue-400";
  }

  const modelShort = s.current_model.length > 25
    ? s.current_model.substring(0, 22) + "..."
    : s.current_model;

  return (
    <div className={`flex items-center gap-3 text-[10px] font-mono ${className}`}>
      {isOffline ? (
        <WifiOff size={12} className="text-amber-400" />
      ) : (
        <Wifi size={12} className={iconColor} />
      )}

      <span className="text-zinc-400">Provider:</span>
      <span className={`font-semibold ${isOffline ? "text-amber-400" : "text-zinc-200"}`}>
        {providerLabel}
      </span>

      <span className="text-zinc-600">|</span>

      <span className="text-zinc-400">Model:</span>
      <span className="text-zinc-200" title={s.current_model}>
        {modelShort}
      </span>

      <span className="text-zinc-600">|</span>

      <div className={`px-1.5 py-0.5 rounded border text-[9px] font-semibold uppercase tracking-wider ${
        isOffline
          ? "bg-amber-950/20 border-amber-500/20 text-amber-400"
          : isLocal
          ? "bg-blue-950/20 border-blue-500/20 text-blue-400"
          : "bg-emerald-950/20 border-emerald-500/20 text-emerald-400"
      }`}>
        <span className="flex items-center gap-1">
          {isLocal ? <Cpu size={9} /> : <Zap size={9} />}
          {modeBadge}
        </span>
      </div>

      {loading && (
        <RefreshCw size={9} className="text-zinc-500 animate-spin" />
      )}
    </div>
  );
}
