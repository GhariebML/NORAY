"use client";

import { useEffect, useState } from "react";
import {
  Cpu,
  Server,
  Activity,
  Download,
  CheckCircle,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Key,
  Database,
  Layers,
  Settings as SettingsIcon,
  Play,
  Trash2,
  TrendingUp,
  Sliders,
  DollarSign,
  ArrowUp,
  ArrowDown,
  Eye,
  Info
} from "lucide-react";
import { PageHeader, Card, Button, Badge } from "@/components/ui";

interface ProviderStatus {
  provider: string;
  status: "Healthy" | "Unconfigured" | "Error";
  latency: number;
  available_models: string[];
  streaming: boolean;
  embeddings: boolean;
  tools: boolean;
  configured: boolean;
  healthy: boolean;
  costTier?: "Free" | "Low" | "Medium" | "High";
  fallbackPosition?: number;
}

interface DiagnosticsReport {
  ollama_running: boolean;
  models_downloaded: boolean;
  api_keys_loaded: boolean;
  router_healthy: boolean;
  embeddings_healthy: boolean;
  streaming_works: boolean;
  memory_service_works: boolean;
  details: {
    ollama?: string;
    downloaded_models?: string[];
    api_keys_configured_count?: number;
    router_decision?: string;
    embedding_dimension?: number;
    streaming_error?: string;
    memory_context_length?: number;
  };
  hardware: {
    cpu?: string;
    ram_gb?: number;
    gpu?: string;
    vram_gb?: number;
  };
}

export default function AISettingsPage() {
  const [providers, setProviders] = useState<ProviderStatus[]>([]);
  const [diagnostics, setDiagnostics] = useState<DiagnosticsReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [pullingModel, setPullingModel] = useState<string | null>(null);
  const [newModelName, setNewModelName] = useState("");
  
  // Custom policy configurations
  const [routingPolicy, setRoutingPolicy] = useState("balanced");
  const [disabledProviders, setDisabledProviders] = useState<string[]>([]);
  
  // Provider ordering priorities state
  const [providerOrder, setProviderOrder] = useState<string[]>([
    "Gemini", "DeepSeek", "Together", "OpenRouter", "Ollama", "OpenAI", "Anthropic", "Mistral"
  ]);

  // Cost tracking simulator
  const [monthlyCost, setMonthlyCost] = useState(0.00);
  const [tokenUsage, setTokenUsage] = useState({ input: 0, output: 0 });

  async function fetchStatus() {
    setLoading(true);
    try {
      const [provRes, diagRes] = await Promise.all([
        fetch("/api/system/providers"),
        fetch("/api/system/diagnostics")
      ]);
      if (provRes.ok) {
        const data = await provRes.json();
        const apiProviders = data.providers || [];
        
        // Define cost tiers
        const costTiers: Record<string, "Free" | "Low" | "Medium" | "High"> = {
          "Gemini": "Free",
          "Ollama": "Free",
          "DeepSeek": "Low",
          "Together": "Low",
          "OpenRouter": "Low",
          "Mistral": "Medium",
          "OpenAI": "Medium",
          "Anthropic": "High"
        };

        // Map fallbacks and cost tiers
        const mappedProviders = apiProviders.map((p: any) => {
          const name = p.provider;
          const pos = providerOrder.indexOf(name) + 1;
          return {
            ...p,
            costTier: costTiers[name] || "Low",
            fallbackPosition: pos > 0 ? pos : 99
          };
        });

        // Sort mapped providers by fallbackPosition initially
        mappedProviders.sort((a: any, b: any) => (a.fallbackPosition || 99) - (b.fallbackPosition || 99));
        setProviders(mappedProviders);
      }
      if (diagRes.ok) {
        const data = await diagRes.json();
        setDiagnostics(data);
      }
    } catch (err) {
      console.error("Failed to load AI system settings", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchStatus();
  }, [providerOrder]);

  const handlePullModel = async (model: string) => {
    if (!model.trim()) return;
    setPullingModel(model);
    try {
      const res = await fetch("/api/system/pull-model", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model })
      });
      if (res.ok) {
        alert(`Started pulling model ${model} in the background. Please wait a few minutes.`);
      } else {
        alert("Failed to start pulling model.");
      }
    } catch (err) {
      console.error("Error during model pull trigger", err);
    } finally {
      setPullingModel(null);
      setNewModelName("");
      setTimeout(fetchStatus, 3000);
    }
  };

  const moveProvider = (index: number, direction: "up" | "down") => {
    const nextIndex = direction === "up" ? index - 1 : index + 1;
    if (nextIndex < 0 || nextIndex >= providerOrder.length) return;
    
    const newOrder = [...providerOrder];
    const temp = newOrder[index];
    newOrder[index] = newOrder[nextIndex];
    newOrder[nextIndex] = temp;
    setProviderOrder(newOrder);
  };

  const toggleProviderEnable = (name: string) => {
    const list = [...disabledProviders];
    const index = list.indexOf(name.toLowerCase());
    if (index > -1) {
      list.splice(index, 1);
    } else {
      list.push(name.toLowerCase());
    }
    setDisabledProviders(list);
  };

  const handlePolicyChange = async (policy: string) => {
    setRoutingPolicy(policy);
    try {
      // Save routing policy environment preset to backend
      const apiBase = typeof window !== "undefined" ? "" : "http://localhost:8001";
      await fetch(`${apiBase}/api/health/setup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ active_policy: policy }),
      });
    } catch (e) {
      console.error("Failed to save active policy preset", e);
    }
  };

  return (
    <div className="space-y-8 p-6 max-w-7xl mx-auto text-gray-200">
      <PageHeader
        title="AI Control Center & Provider Settings"
        subtitle="Manage dynamic priority tiers, routing presets, local runtime checks, and online API keys connection status."
      />

      {/* Stats and Quick Controls */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Hardware Status Card */}
        <Card className="p-6 bg-slate-900 border-slate-800 rounded-xl space-y-4 shadow-xl">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Cpu className="text-indigo-400" /> Hardware Specs
            </h3>
            <Badge variant="outline" className="border-indigo-500 text-indigo-400">Windows System</Badge>
          </div>
          {diagnostics?.hardware ? (
            <div className="space-y-3 text-sm">
              <div>
                <span className="text-slate-400 text-xs">Processor (CPU):</span>
                <p className="font-mono text-white text-xs mt-1 truncate">{diagnostics.hardware.cpu || "Unknown"}</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-slate-400 text-xs">RAM Installed:</span>
                  <p className="font-bold text-white text-base mt-0.5">{diagnostics.hardware.ram_gb || 0} GB</p>
                </div>
                <div>
                  <span className="text-slate-400 text-xs">Ollama State:</span>
                  <p className="mt-0.5">
                    {diagnostics.ollama_running ? (
                      <span className="text-emerald-400 font-bold flex items-center gap-1 text-xs">
                        <CheckCircle size={14} /> Active
                      </span>
                    ) : (
                      <span className="text-red-400 font-bold flex items-center gap-1 text-xs">
                        <XCircle size={14} /> Inactive
                      </span>
                    )}
                  </p>
                </div>
              </div>
              <div>
                <span className="text-slate-400 text-xs">Graphics Card (GPU):</span>
                <p className="font-mono text-indigo-300 text-xs mt-1 truncate">{diagnostics.hardware.gpu || "None / Integrated"}</p>
                {diagnostics.hardware.vram_gb ? (
                  <p className="text-xs text-slate-400 mt-0.5 font-bold">VRAM: {diagnostics.hardware.vram_gb} GB</p>
                ) : null}
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-400">Loading hardware details...</p>
          )}
        </Card>

        {/* Global Routing Engine Card */}
        <Card className="p-6 bg-slate-900 border-slate-800 rounded-xl space-y-4 shadow-xl">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Sliders className="text-indigo-400" /> Routing Preset
            </h3>
            <Badge variant="outline" className="border-indigo-500 text-indigo-400">Dynamic Score</Badge>
          </div>
          <div className="space-y-3 text-sm">
            <div>
              <label className="text-slate-400 block mb-1 text-xs">Active Routing Policy:</label>
              <select
                value={routingPolicy}
                onChange={(e) => handlePolicyChange(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500 font-medium"
              >
                <option value="balanced">Hybrid Balanced (Default Priority)</option>
                <option value="fastest">Fastest (Lowest Latency Scoring)</option>
                <option value="lowest-cost">Lowest Cost (Free/Cheap Cloud first)</option>
                <option value="highest-quality">Highest Quality (Premium reasoning models first)</option>
                <option value="offline-first">Offline First (Ollama priority)</option>
                <option value="research">Research Mode (Long Context first)</option>
                <option value="coding">Coding Mode (High Coder scoring first)</option>
              </select>
            </div>
            <div className="pt-2 text-xs border-t border-slate-800/50 space-y-1.5">
              <div className="flex justify-between text-slate-400">
                <span>Task Reranker:</span>
                <span className="font-bold text-white font-mono">BGE-Reranker-v2</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Dynamic Scoring Mode:</span>
                <span className="font-bold text-emerald-400">Enabled</span>
              </div>
            </div>
          </div>
        </Card>

        {/* Cost & Token Monitor Card */}
        <Card className="p-6 bg-slate-900 border-slate-800 rounded-xl space-y-4 shadow-xl">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <DollarSign className="text-indigo-400" /> Usage & Cost
            </h3>
            <Badge variant="outline" className="border-indigo-500 text-indigo-400">Gateway Metrics</Badge>
          </div>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-slate-400 text-xs">Estimated Cost (USD):</span>
                <p className="text-2xl font-extrabold text-white mt-1">${monthlyCost.toFixed(2)}</p>
              </div>
              <div>
                <span className="text-slate-400 text-xs">Total Requests:</span>
                <p className="text-xl font-bold text-slate-300 mt-1.5">0</p>
              </div>
            </div>
            <div className="space-y-2 text-xs">
              <div>
                <div className="flex justify-between text-slate-400 mb-1">
                  <span>Input Tokens:</span>
                  <span>{tokenUsage.input}</span>
                </div>
                <div className="h-1.5 w-full bg-slate-950 rounded-full overflow-hidden">
                  <div className="h-full bg-indigo-500" style={{ width: "0%" }}></div>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Main Grid: Priority drag-and-drop ordering + Models manager */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Fallback Priority Ordering */}
        <Card className="lg:col-span-1 p-6 bg-slate-900 border-slate-800 rounded-xl space-y-4 shadow-xl">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-lg font-bold flex items-center gap-2">
              <Sliders size={18} className="text-indigo-400" /> Fallback Priority Order
            </h3>
            <p className="text-slate-400 text-xxs mt-1">Adjust order of models routing logic during failover sequences.</p>
          </div>
          <div className="space-y-2">
            {providerOrder.map((name, idx) => (
              <div
                key={name}
                className="flex items-center justify-between p-2.5 bg-slate-950 border border-slate-800/80 rounded-lg text-xs"
              >
                <div className="flex items-center gap-2 font-semibold">
                  <span className="text-slate-500 font-mono">#{idx + 1}</span>
                  <span className="text-white">{name}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <button
                    disabled={idx === 0}
                    onClick={() => moveProvider(idx, "up")}
                    className="p-1 hover:bg-slate-800 text-slate-400 hover:text-white rounded disabled:opacity-30"
                  >
                    <ArrowUp size={12} />
                  </button>
                  <button
                    disabled={idx === providerOrder.length - 1}
                    onClick={() => moveProvider(idx, "down")}
                    className="p-1 hover:bg-slate-800 text-slate-400 hover:text-white rounded disabled:opacity-30"
                  >
                    <ArrowDown size={12} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Local Ollama Models and Diagnostics */}
        <Card className="lg:col-span-2 p-6 bg-slate-900 border-slate-800 rounded-xl space-y-6 shadow-xl">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-lg font-bold flex items-center gap-2">
              <Download className="text-indigo-400" /> Local Ollama Library
            </h3>
            <Button
              size="sm"
              variant="outline"
              className="text-xs flex items-center gap-1 hover:bg-slate-800"
              onClick={fetchStatus}
            >
              <RefreshCw size={12} /> Refresh taglist
            </Button>
          </div>

          <div className="space-y-6">
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Enter model name (e.g. qwen2.5:7b)"
                value={newModelName}
                onChange={(e) => setNewModelName(e.target.value)}
                className="flex-1 bg-slate-950 border border-slate-800 rounded px-3 py-2 text-sm focus:outline-none focus:border-indigo-500 text-white"
              />
              <Button
                onClick={() => handlePullModel(newModelName)}
                disabled={pullingModel !== null || !newModelName.trim()}
                className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm"
              >
                {pullingModel ? "Pulling..." : "Pull Model"}
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="text-xs text-slate-400 font-bold uppercase tracking-wider mb-2">Installed Models</h4>
                {diagnostics?.details.downloaded_models && diagnostics.details.downloaded_models.length > 0 ? (
                  <div className="divide-y divide-slate-800/80 bg-slate-950 rounded-lg p-3 border border-slate-850">
                    {diagnostics.details.downloaded_models.map((model, idx) => (
                      <div key={idx} className="py-2 flex items-center justify-between text-xs">
                        <span className="font-mono text-indigo-300">{model}</span>
                        <Badge variant="outline" className="border-indigo-900/50 text-indigo-400 text-xxs font-semibold">Ready</Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No models detected. Download a model to enable offline functionality.</p>
                )}
              </div>

              <div>
                <h4 className="text-xs text-slate-400 font-bold uppercase tracking-wider mb-2">System Diagnostic Checklist</h4>
                <div className="space-y-1.5 text-xs">
                  <div className="flex justify-between items-center p-2 bg-slate-950/80 border border-slate-850 rounded">
                    <span>Ollama Connection</span>
                    {diagnostics?.ollama_running ? <Badge className="bg-emerald-950 text-emerald-400">OK</Badge> : <Badge className="bg-rose-950 text-rose-400">Offline</Badge>}
                  </div>
                  <div className="flex justify-between items-center p-2 bg-slate-950/80 border border-slate-850 rounded">
                    <span>Required Models</span>
                    {diagnostics?.models_downloaded ? <Badge className="bg-emerald-950 text-emerald-400">OK</Badge> : <Badge className="bg-amber-950 text-amber-400">Missing</Badge>}
                  </div>
                  <div className="flex justify-between items-center p-2 bg-slate-950/80 border border-slate-850 rounded">
                    <span>Dynamic Router Status</span>
                    {diagnostics?.router_healthy ? <Badge className="bg-emerald-950 text-emerald-400">Healthy</Badge> : <Badge className="bg-rose-950 text-rose-400">Error</Badge>}
                  </div>
                  <div className="flex justify-between items-center p-2 bg-slate-950/80 border border-slate-850 rounded">
                    <span>Local Embeddings</span>
                    {diagnostics?.embeddings_healthy ? <Badge className="bg-emerald-950 text-emerald-400">Healthy</Badge> : <Badge className="bg-rose-950 text-rose-400">Error</Badge>}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Cloud & Local Providers Configuration Table */}
      <Card className="p-6 bg-slate-900 border-slate-800 rounded-xl space-y-6 shadow-xl">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h3 className="text-lg font-bold flex items-center gap-2">
            <Server className="text-indigo-400" /> Active LLM Providers & Credentials Health
          </h3>
          <Button
            size="sm"
            variant="outline"
            className="text-xs flex items-center gap-1 hover:bg-slate-800"
            onClick={fetchStatus}
          >
            <Play size={12} /> Run Connections Test
          </Button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 text-xs uppercase">
                <th className="py-3 px-4">Provider</th>
                <th className="py-3 px-4">Fallback Pos</th>
                <th className="py-3 px-4">Cost Tier</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Credentials Check</th>
                <th className="py-3 px-4">Latency</th>
                <th className="py-3 px-4">Capabilities</th>
                <th className="py-3 px-4">Enable status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 font-medium text-xs">
              {providers.map((p, idx) => {
                const isProviderDisabled = disabledProviders.includes(p.provider.toLowerCase());
                return (
                  <tr key={idx} className={`hover:bg-slate-950/40 ${isProviderDisabled ? "opacity-45" : ""}`}>
                    <td className="py-4 px-4 text-white font-bold text-sm">{p.provider}</td>
                    <td className="py-4 px-4">
                      <Badge className="bg-slate-950 text-slate-300 font-mono">Tier {p.fallbackPosition}</Badge>
                    </td>
                    <td className="py-4 px-4">
                      <Badge variant="outline" className={`
                        ${p.costTier === "Free" ? "border-emerald-900 text-emerald-400 bg-emerald-950/20" : ""}
                        ${p.costTier === "Low" ? "border-indigo-900 text-indigo-400 bg-indigo-950/20" : ""}
                        ${p.costTier === "Medium" ? "border-amber-900 text-amber-400 bg-amber-950/20" : ""}
                        ${p.costTier === "High" ? "border-rose-900 text-rose-400 bg-rose-950/20" : ""}
                      `}>
                        {p.costTier}
                      </Badge>
                    </td>
                    <td className="py-4 px-4">
                      {isProviderDisabled ? (
                        <Badge className="bg-slate-850 text-slate-400 border border-slate-800">Disabled</Badge>
                      ) : p.status === "Healthy" ? (
                        <span className="text-emerald-400 font-bold flex items-center gap-1">
                          <CheckCircle size={14} /> Healthy
                        </span>
                      ) : p.status === "Unconfigured" ? (
                        <span className="text-slate-400 flex items-center gap-1">
                          <AlertTriangle size={14} /> Unconfigured
                        </span>
                      ) : (
                        <span className="text-rose-400 font-bold flex items-center gap-1">
                          <XCircle size={14} /> Error
                        </span>
                      )}
                    </td>
                    <td className="py-4 px-4 font-mono text-slate-400 text-xxs">
                      {p.configured ? "sk-•••••••••" : "Not Provided"}
                    </td>
                    <td className="py-4 px-4 font-mono text-slate-300">
                      {p.configured && p.latency && !isProviderDisabled ? `${p.latency}ms` : "-"}
                    </td>
                    <td className="py-4 px-4">
                      <div className="flex gap-1 flex-wrap">
                        {p.streaming ? <Badge className="bg-indigo-950/80 text-indigo-400 border border-indigo-900/50 text-xxs">Stream</Badge> : null}
                        {p.embeddings ? <Badge className="bg-pink-950/80 text-pink-400 border border-pink-900/50 text-xxs">Embed</Badge> : null}
                        {p.tools ? <Badge className="bg-violet-950/80 text-violet-400 border border-violet-900/50 text-xxs">Tools</Badge> : null}
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      <Button
                        size="sm"
                        variant="outline"
                        className={`text-xxs px-2 py-1 ${isProviderDisabled ? "bg-indigo-600/20 border-indigo-500 text-indigo-400" : "bg-rose-950/20 border-rose-900 text-rose-400"}`}
                        onClick={() => toggleProviderEnable(p.provider)}
                      >
                        {isProviderDisabled ? "Enable" : "Disable"}
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
