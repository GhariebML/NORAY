"use client";

import { useState, useEffect } from "react";
import { 
  Activity, 
  Cpu, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  RefreshCw,
  Coins,
  Layers,
  Download
} from "lucide-react";
import { PageHeader, Card, Button, Badge } from "@/components/ui";

interface DiagnosticItem {
  name: string;
  category: string;
  status: "healthy" | "degraded" | "unhealthy" | "checking";
  description: string;
}

interface GatewayMetrics {
  total_requests: number;
  total_input_tokens: number;
  total_output_tokens: number;
  total_estimated_cost: number;
  total_latency_ms: number;
}

interface HardwareInfo {
  os: string;
  cpu: string;
  ram_gb: number;
  gpu: string;
  vram_gb: number;
  cuda_available: boolean;
  avx2_supported: boolean;
  disk_free_gb: number;
}

export default function DiagnosticsPage() {
  const [loading, setLoading] = useState(false);
  const [installing, setInstalling] = useState(false);
  const [installResult, setInstallResult] = useState<string>("");
  const [lastChecked, setLastChecked] = useState<string>("");
  const [activeProvider, setActiveProvider] = useState<string>("local");
  const [registeredModels, setRegisteredModels] = useState<string[]>([]);
  const [recommendedModel, setRecommendedModel] = useState<string>("");
  const [hardware, setHardware] = useState<HardwareInfo | null>(null);
  
  const [metrics, setMetrics] = useState<GatewayMetrics>({
    total_requests: 0,
    total_input_tokens: 0,
    total_output_tokens: 0,
    total_estimated_cost: 0.0,
    total_latency_ms: 0.0
  });

  const [subsystems, setSubsystems] = useState<DiagnosticItem[]>([
    { name: "PostgreSQL", category: "Database", status: "checking", description: "Relational persistence store for profile, applications, and relations mapping." },
    { name: "Qdrant", category: "Vector Store", status: "checking", description: "Primary high-dimensional vector search index for dense semantic embeddings." },
    { name: "PostgresGraphStore", category: "Graph", status: "checking", description: "PostgreSQL backed Entity-Relationship Graph mapping." },
    { name: "Local LLM", category: "AI Providers", status: "checking", description: "Ollama or local offline models." },
    { name: "Cloud LLM", category: "AI Providers", status: "checking", description: "OpenAI, Anthropic, Gemini, OpenRouter." },
    { name: "Embedding Model", category: "AI Providers", status: "checking", description: "Sentence-transformers local embedding model." },
    { name: "MCP Client Adapter", category: "MCP", status: "checking", description: "JSON-RPC client adapter for external tools discovery." },
    { name: "PlannerAgent", category: "Planner", status: "checking", description: "Decomposes user objectives into DAG task plans." },
    { name: "RouterAgent", category: "Router", status: "checking", description: "Dispatches and manages asynchronous task trees." },
    { name: "Background Workers", category: "Workers", status: "checking", description: "Celery/async workers for heavy tasks." },
    { name: "Deep Research Engine", category: "Orchestration", status: "checking", description: "Multi-stage evidence analysis and conflict solver pipeline." },
    { name: "Startup Validation", category: "Environment", status: "checking", description: "Health validation of all dependencies on startup." }
  ]);

  const runHealthChecks = async () => {
    setLoading(true);
    setLastChecked(new Date().toLocaleTimeString());
    
    let dbStatus: "healthy" | "unhealthy" = "unhealthy";
    let vecStatus: "healthy" | "unhealthy" = "unhealthy";
    let graphStatus: "healthy" | "unhealthy" = "unhealthy";
    let llmStatus: "healthy" | "degraded" = "degraded";
    let mcpStatus: "healthy" | "degraded" | "unhealthy" = "unhealthy";

    try {
      const res = await fetch("/api/health");
      if (res.ok) {
        const data = await res.json();
        dbStatus = data.details.database === "healthy" ? "healthy" : "unhealthy";
        vecStatus = data.details.vector_store === "healthy" ? "healthy" : "unhealthy";
        graphStatus = data.details.graph_store === "healthy" ? "healthy" : "unhealthy";
        llmStatus = data.details.llm === "configured" ? "healthy" : "degraded";
        mcpStatus = data.details.mcp === "active" ? "healthy" : "degraded";

        // Expose AI Gateway values
        if (data.gateway) {
          setMetrics(data.gateway.metrics);
          setRegisteredModels(data.gateway.models);
          setActiveProvider(data.gateway.active_provider);
        }
      }

      // Fetch hardware configuration setup info
      const setupRes = await fetch("/api/health/setup");
      if (setupRes.ok) {
        const setupData = await setupRes.json();
        setHardware(setupData.hardware);
        setRecommendedModel(setupData.recommended_model);
      }
    } catch (err) {
      console.error("Health check failed", err);
    }

    setSubsystems(prev => prev.map(item => {
      let status: "healthy" | "degraded" | "unhealthy" = "healthy";

      if (item.name === "PostgreSQL") status = dbStatus;
      else if (item.name === "Qdrant") status = vecStatus;
      else if (item.name === "PostgresGraphStore") status = graphStatus;
      else if (item.name === "LLM Config") status = llmStatus;
      else if (item.name === "MCP Client Adapter") status = mcpStatus;
      
      else if (item.name === "PlannerAgent" || item.name === "RouterAgent" || item.name === "Domain Agents Registry") {
        status = llmStatus === "healthy" ? "healthy" : "degraded";
      }
      else if (item.name === "Workspace API") {
        status = (dbStatus === "healthy" && vecStatus === "healthy") ? "healthy" : "unhealthy";
      }
      else if (item.name === "Deep Research Engine") {
        status = (llmStatus === "healthy" && vecStatus === "healthy") ? "healthy" : "degraded";
      }

      return { ...item, status };
    }));

    setLoading(false);
  };

  const handleInstallLocalModel = async () => {
    setInstalling(true);
    setInstallResult("Installing Ollama / Pulling recommended model... This might take 3-5 minutes.");
    try {
      const res = await fetch("/api/health/setup/install", { method: "POST" });
      const data = await res.json();
      if (data.success) {
        setInstallResult(`Success! Installed and verified local model: ${data.model}. Verification: ${data.verification}`);
        runHealthChecks();
      } else {
        setInstallResult(`Failure: ${data.error}. Details: ${data.details || ""}`);
      }
    } catch (err) {
      setInstallResult(`Installation failed with connection error: ${err}`);
    }
    setInstalling(false);
  };

  useEffect(() => {
    runHealthChecks();
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "healthy":
        return <CheckCircle className="text-emerald-500 shrink-0" size={18} />;
      case "degraded":
        return <AlertTriangle className="text-amber-500 shrink-0" size={18} />;
      case "unhealthy":
        return <XCircle className="text-red-500 shrink-0" size={18} />;
      default:
        return <RefreshCw className="text-zinc-500 animate-spin shrink-0" size={18} />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "healthy":
        return <Badge variant="success">Online</Badge>;
      case "degraded":
        return <Badge variant="warning">Degraded</Badge>;
      case "unhealthy":
        return <Badge variant="danger">Offline</Badge>;
      default:
        return <Badge variant="default">Checking</Badge>;
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-zinc-950 text-zinc-100 p-6">
      <div className="flex justify-between items-center mb-6">
        <PageHeader 
          title="AI Diagnostics Console" 
          description="Real-time health checking and hybrid request routing control center for NORAY AI Gateway."
        />
        <Button 
          onClick={runHealthChecks} 
          disabled={loading}
          className="flex items-center gap-2 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-100"
        >
          <RefreshCw className={loading ? "animate-spin" : ""} size={14} />
          <span>Refresh Console</span>
        </Button>
      </div>

      <div className="mb-6 text-xs text-zinc-500 flex justify-between px-1">
        <span>Last checked: {lastChecked || "Checking..."}</span>
        <span>AI Gateway Mode: <span className="text-emerald-400 font-semibold uppercase">{activeProvider}</span></span>
      </div>

      {/* Hardware and Installer section */}
      {hardware && (
        <Card className="p-5 border-zinc-850 bg-zinc-900/50 mb-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2">
            <h3 className="font-bold text-sm text-zinc-200 mb-3 flex items-center gap-2">
              <Cpu className="text-emerald-400" size={16} />
              <span>Detected Hardware Profile</span>
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
              <div className="bg-zinc-950/30 p-2 rounded border border-zinc-850">
                <span className="text-zinc-500 block">CPU</span>
                <span className="font-semibold text-zinc-300 truncate block" title={hardware.cpu}>{hardware.cpu}</span>
              </div>
              <div className="bg-zinc-950/30 p-2 rounded border border-zinc-850">
                <span className="text-zinc-500 block">System RAM</span>
                <span className="font-semibold text-zinc-300">{hardware.ram_gb} GB</span>
              </div>
              <div className="bg-zinc-950/30 p-2 rounded border border-zinc-850">
                <span className="text-zinc-500 block">Graphics Card</span>
                <span className="font-semibold text-zinc-300 truncate block" title={hardware.gpu}>{hardware.gpu}</span>
              </div>
              <div className="bg-zinc-950/30 p-2 rounded border border-zinc-850">
                <span className="text-zinc-500 block">Video VRAM</span>
                <span className="font-semibold text-zinc-300">{hardware.vram_gb} GB</span>
              </div>
              <div className="bg-zinc-950/30 p-2 rounded border border-zinc-850">
                <span className="text-zinc-500 block">CUDA Capability</span>
                <span className={hardware.cuda_available ? "text-emerald-400 font-semibold" : "text-zinc-400"}>
                  {hardware.cuda_available ? "Supported" : "N/A"}
                </span>
              </div>
              <div className="bg-zinc-950/30 p-2 rounded border border-zinc-850">
                <span className="text-zinc-500 block">Disk Space Free</span>
                <span className="font-semibold text-zinc-300">{hardware.disk_free_gb} GB</span>
              </div>
            </div>
          </div>

          <div className="bg-zinc-950/40 p-4 rounded-lg border border-zinc-850 flex flex-col justify-between">
            <div>
              <span className="text-[10px] text-zinc-500 uppercase tracking-wider font-semibold">Ollama Setup</span>
              <h4 className="font-bold text-sm text-zinc-200 mt-1">Local Model Autoinstaller</h4>
              <p className="text-xs text-zinc-400 mt-2 leading-relaxed">
                Recommended Local Model: <strong className="text-emerald-400 font-mono">{recommendedModel}</strong>
              </p>
            </div>

            <div className="mt-4">
              <Button 
                onClick={handleInstallLocalModel} 
                disabled={installing}
                className="w-full flex items-center justify-center gap-2 bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/30 text-emerald-400 text-xs py-1.5"
              >
                <Download size={14} className={installing ? "animate-bounce" : ""} />
                <span>{installing ? "Downloading..." : "Autoinstall Model"}</span>
              </Button>
            </div>
          </div>
          {installResult && (
            <div className="col-span-1 md:col-span-3 text-xs bg-zinc-950/80 border border-zinc-800 p-2.5 rounded text-zinc-400 flex items-center gap-2">
              <Activity className="text-emerald-500 animate-pulse shrink-0" size={14} />
              <span>{installResult}</span>
            </div>
          )}
        </Card>
      )}

      {/* AI Gateway Stats and Settings */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <Card className="p-5 border-zinc-800 bg-zinc-900/60 backdrop-blur-sm lg:col-span-2">
          <h3 className="font-bold text-sm text-zinc-200 mb-4 flex items-center gap-2">
            <Coins className="text-emerald-400" size={16} />
            <span>AI Gateway Analytics</span>
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
            <div className="bg-zinc-950/40 p-3 rounded-lg border border-zinc-850">
              <span className="text-[10px] text-zinc-500 uppercase tracking-wider block">Total Requests</span>
              <span className="text-lg font-bold text-zinc-200">{metrics.total_requests}</span>
            </div>
            <div className="bg-zinc-950/40 p-3 rounded-lg border border-zinc-850">
              <span className="text-[10px] text-zinc-500 uppercase tracking-wider block">Estimated Cost</span>
              <span className="text-lg font-bold text-emerald-400">${metrics.total_estimated_cost.toFixed(5)}</span>
            </div>
            <div className="bg-zinc-950/40 p-3 rounded-lg border border-zinc-850">
              <span className="text-[10px] text-zinc-500 uppercase tracking-wider block">Average Latency</span>
              <span className="text-lg font-bold text-zinc-200">
                {metrics.total_requests > 0 
                  ? `${(metrics.total_latency_ms / metrics.total_requests).toFixed(0)} ms` 
                  : "0 ms"}
              </span>
            </div>
            <div className="bg-zinc-950/40 p-3 rounded-lg border border-zinc-850">
              <span className="text-[10px] text-zinc-500 uppercase tracking-wider block">Accumulated Tokens</span>
              <span className="text-lg font-bold text-zinc-200">{metrics.total_input_tokens + metrics.total_output_tokens}</span>
            </div>
          </div>
          <div className="mt-4 text-[11px] text-zinc-500 flex justify-between">
            <span>Inputs: {metrics.total_input_tokens} tokens</span>
            <span>Outputs: {metrics.total_output_tokens} tokens</span>
          </div>
        </Card>

        <Card className="p-5 border-zinc-800 bg-zinc-900/60 backdrop-blur-sm">
          <h3 className="font-bold text-sm text-zinc-200 mb-4 flex items-center gap-2">
            <Layers className="text-emerald-400" size={16} />
            <span>Active Model Registry</span>
          </h3>
          <div className="flex flex-wrap gap-2 max-h-[120px] overflow-y-auto pr-1">
            {registeredModels.map((model, i) => (
              <Badge key={i} variant="default" className="border-zinc-800 bg-zinc-950/50 text-zinc-300 text-[10px]">
                {model}
              </Badge>
            ))}
            {registeredModels.length === 0 && (
              <span className="text-xs text-zinc-500">No active models registered.</span>
            )}
          </div>
        </Card>
      </div>

      {/* Grid listing */}
      <h3 className="text-xs text-zinc-500 uppercase tracking-wider font-semibold mb-3 px-1">Subsystem Health List</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {subsystems.map((sub, idx) => (
          <Card key={idx} className="p-4 border-zinc-800 bg-zinc-900/40 backdrop-blur-sm flex flex-col justify-between">
            <div>
              <div className="flex justify-between items-start gap-4 mb-2">
                <div className="flex flex-col">
                  <span className="text-[10px] text-zinc-500 uppercase tracking-wider font-semibold">{sub.category}</span>
                  <h3 className="font-bold text-sm text-zinc-200 mt-0.5">{sub.name}</h3>
                </div>
                {getStatusBadge(sub.status)}
              </div>
              <p className="text-xs text-zinc-400 leading-relaxed mt-2">{sub.description}</p>
            </div>
            
            <div className="mt-4 pt-3 border-t border-zinc-850 flex items-center gap-2 text-xs">
              {getStatusIcon(sub.status)}
              <span className="text-zinc-500">Status Check: </span>
              <span className={
                sub.status === "healthy" ? "text-emerald-400 font-semibold" :
                sub.status === "degraded" ? "text-amber-400 font-semibold" :
                sub.status === "unhealthy" ? "text-red-400 font-semibold" :
                "text-zinc-500"
              }>
                {sub.status.toUpperCase()}
              </span>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
