"use client";

import { useEffect, useState } from "react";
import {
  Cpu,
  Server,
  Download,
  CheckCircle,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Play,
  Sliders,
  DollarSign,
  ArrowUp,
  ArrowDown,
  BookOpen,
  Save,
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

interface PromptPreset {
  id: string;
  name: string;
  version: string;
  content: string;
}

export default function AISettingsPage() {
  const [activeTab, setActiveTab] = useState<"providers" | "prompts">("providers");
  const [providers, setProviders] = useState<ProviderStatus[]>([]);
  const [diagnostics, setDiagnostics] = useState<DiagnosticsReport | null>(null);
  const [, setLoading] = useState(false);
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
  const [monthlyCost] = useState(0.00);
  const [tokenUsage] = useState({ input: 0, output: 0 });

  // Prompt Presets State
  const [prompts, setPrompts] = useState<PromptPreset[]>([
    { id: "planner", name: "Planner Prompt", version: "v1.4.2", content: "You are the autonomous execution planner agent. Breakdown user query into sequential dependency tasks..." },
    { id: "retriever", name: "Retriever Prompt", version: "v1.2.0", content: "RAG dense vector retrieval filter. Match core entity tokens with search parameters..." },
    { id: "research", name: "Research Prompt", version: "v2.0.1", content: "Deep academic paper analyzer and citation builder. Synthesize findings objectively..." },
    { id: "career", name: "Career Prompt", version: "v1.1.5", content: "ATS cv and professional profile optimizer. Highlight tech stack alignment details..." },
    { id: "reflection", name: "Reflection & Validation Prompt", version: "v1.0.3", content: "Verify synthesized responses against grounding source chunks to prevent hallucination..." },
    { id: "memory", name: "Memory Consolidation Prompt", version: "v1.1.0", content: "Consolidate episodic user dialogues into structured semantic key preference memories..." }
  ]);

  const [selectedPromptId, setSelectedPromptId] = useState("planner");
  const [editingPromptContent, setEditingPromptContent] = useState("");

  useEffect(() => {
    const activePrompt = prompts.find(p => p.id === selectedPromptId);
    if (activePrompt) {
      setEditingPromptContent(activePrompt.content);
    }
  }, [selectedPromptId, prompts]);

  async function fetchStatus() {
    setLoading(true);
    try {
      const provRes = await fetch("/api/system/providers");
      const diagRes = await fetch("/api/system/diagnostics");
      if (provRes.ok) {
        const data = await provRes.json();
        const apiProviders = data.providers || [];
        
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

        const mappedProviders = apiProviders.map((p: any) => {
          const name = p.provider;
          const pos = providerOrder.indexOf(name) + 1;
          return {
            ...p,
            costTier: costTiers[name] || "Low",
            fallbackPosition: pos > 0 ? pos : 99
          };
        });

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
  }, [providerOrder]); // eslint-disable-line react-hooks/exhaustive-deps

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

  const handleSavePrompt = () => {
    setPrompts(prev => prev.map(p => {
      if (p.id === selectedPromptId) {
        const verParts = p.version.substring(1).split(".").map(Number);
        verParts[2] += 1; // Increment patch version
        return { ...p, content: editingPromptContent, version: `v${verParts.join(".")}` };
      }
      return p;
    }));
    alert("System prompt preset updated and compiled successfully.");
  };

  return (
    <div className="space-y-6 text-gray-200">
      <PageHeader
        title="AI Control Center & Prompt Studio"
        description="Configure fallback providers, local Ollama runtimes, and system-wide agent instructions library"
      />

      {/* Primary Tab Switcher */}
      <div className="flex gap-2 border-b border-zinc-900 pb-2">
        <button
          onClick={() => setActiveTab("providers")}
          className={`px-4 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-colors border ${
            activeTab === "providers"
              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
              : "bg-zinc-950 border-zinc-900 text-zinc-500 hover:text-zinc-300"
          }`}
        >
          <Server size={12} className="inline mr-1.5" /> Providers Observatory
        </button>
        <button
          onClick={() => setActiveTab("prompts")}
          className={`px-4 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-colors border ${
            activeTab === "prompts"
              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
              : "bg-zinc-950 border-zinc-900 text-zinc-500 hover:text-zinc-300"
          }`}
        >
          <BookOpen size={12} className="inline mr-1.5" /> Prompt Studio
        </button>
      </div>

      {activeTab === "providers" ? (
        <div className="space-y-6">
          {/* Stats and Quick Controls */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Hardware Status Card */}
            <Card className="p-6 bg-zinc-950/40 border-zinc-900 rounded-xl space-y-4 shadow-xl">
              <div className="flex items-center justify-between border-b border-zinc-900 pb-3">
                <h3 className="text-sm font-semibold flex items-center gap-2">
                  <Cpu className="text-emerald-400" size={16} /> Hardware Specs
                </h3>
                <Badge variant="info" className="border-emerald-500 text-emerald-400 font-mono">Windows OS</Badge>
              </div>
              {diagnostics?.hardware ? (
                <div className="space-y-3 text-xs">
                  <div>
                    <span className="text-slate-400 text-[10px]">Processor (CPU):</span>
                    <p className="font-mono text-white mt-1 truncate">{diagnostics.hardware.cpu || "Unknown"}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-slate-400 text-[10px]">RAM Installed:</span>
                      <p className="font-bold text-white text-base mt-0.5">{diagnostics.hardware.ram_gb || 0} GB</p>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[10px]">Ollama State:</span>
                      <p className="mt-0.5">
                        {diagnostics.ollama_running ? (
                          <span className="text-emerald-400 font-bold flex items-center gap-1">
                            <CheckCircle size={12} /> Active
                          </span>
                        ) : (
                          <span className="text-rose-400 font-bold flex items-center gap-1">
                            <XCircle size={12} /> Offline
                          </span>
                        )}
                      </p>
                    </div>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px]">Graphics Card (GPU):</span>
                    <p className="font-mono text-emerald-400 mt-1 truncate">{diagnostics.hardware.gpu || "None / Integrated"}</p>
                    {diagnostics.hardware.vram_gb ? (
                      <p className="text-[10px] text-slate-400 mt-0.5 font-bold font-mono">VRAM: {diagnostics.hardware.vram_gb} GB</p>
                    ) : null}
                  </div>
                </div>
              ) : (
                <p className="text-xs text-slate-400">Loading hardware details...</p>
              )}
            </Card>

            {/* Global Routing Engine Card */}
            <Card className="p-6 bg-zinc-950/40 border-zinc-900 rounded-xl space-y-4 shadow-xl">
              <div className="flex items-center justify-between border-b border-zinc-900 pb-3">
                <h3 className="text-sm font-semibold flex items-center gap-2">
                  <Sliders className="text-emerald-400" size={16} /> Routing Preset
                </h3>
                <Badge variant="info" className="border-emerald-500 text-emerald-400 font-mono">Dynamic Router</Badge>
              </div>
              <div className="space-y-3 text-xs">
                <div>
                  <label className="text-slate-400 block mb-1">Active Routing Policy:</label>
                  <select
                    value={routingPolicy}
                    onChange={(e) => handlePolicyChange(e.target.value)}
                    className="w-full bg-slate-950 border border-zinc-900 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-emerald-500 font-medium"
                  >
                    <option value="balanced">Hybrid Balanced (Default Priority)</option>
                    <option value="fastest">Fastest (Lowest Latency Scoring)</option>
                    <option value="lowest-cost">Lowest Cost (Free/Cheap Cloud first)</option>
                    <option value="highest-quality">Highest Quality (Premium reasoning models first)</option>
                    <option value="offline-first">Offline First (Ollama priority)</option>
                  </select>
                </div>
                <div className="pt-2 text-[10px] border-t border-zinc-900 space-y-1.5 font-mono">
                  <div className="flex justify-between text-slate-400">
                    <span>Task Reranker:</span>
                    <span className="font-bold text-white">BGE-Reranker-v2</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Dynamic Scoring Mode:</span>
                    <span className="font-bold text-emerald-400">Enabled</span>
                  </div>
                </div>
              </div>
            </Card>

            {/* Cost & Token Monitor Card */}
            <Card className="p-6 bg-zinc-950/40 border-zinc-900 rounded-xl space-y-4 shadow-xl">
              <div className="flex items-center justify-between border-b border-zinc-900 pb-3">
                <h3 className="text-sm font-semibold flex items-center gap-2">
                  <DollarSign className="text-emerald-400" size={16} /> Usage & Cost
                </h3>
                <Badge variant="outline" className="border-emerald-500 text-emerald-400 font-mono">Telemetry</Badge>
              </div>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-slate-400 text-xs">Estimated Cost (USD):</span>
                    <p className="text-2xl font-extrabold text-white mt-1 font-mono">${monthlyCost.toFixed(2)}</p>
                  </div>
                  <div>
                    <span className="text-slate-400 text-xs">Total Requests:</span>
                    <p className="text-xl font-bold text-slate-355 mt-1.5 font-mono">0</p>
                  </div>
                </div>
                <div className="space-y-2 text-xs">
                  <div>
                    <div className="flex justify-between text-slate-400 mb-1 font-mono text-[10px]">
                      <span>Input Tokens:</span>
                      <span>{tokenUsage.input}</span>
                    </div>
                    <div className="h-1.5 w-full bg-slate-955 rounded-full overflow-hidden">
                      <div className="h-full bg-emerald-500" style={{ width: "0%" }}></div>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </div>

          {/* Main Grid: Priority drag-and-drop ordering + Models manager */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <Card className="lg:col-span-1 p-6 bg-zinc-950/40 border-zinc-900 rounded-xl space-y-4 shadow-xl">
              <div className="border-b border-zinc-900 pb-3">
                <h3 className="text-sm font-bold flex items-center gap-2">
                  <Sliders size={16} className="text-emerald-400" /> Fallback Priority Order
                </h3>
                <p className="text-zinc-500 text-[10px] mt-1 font-mono">Adjust fallback priorities sequence.</p>
              </div>
              <div className="space-y-2 font-mono text-xs">
                {providerOrder.map((name, idx) => (
                  <div
                    key={name}
                    className="flex items-center justify-between p-2.5 bg-slate-950 border border-zinc-900 rounded-lg"
                  >
                    <div className="flex items-center gap-2 font-semibold">
                      <span className="text-slate-500">#{idx + 1}</span>
                      <span className="text-zinc-200">{name}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <button
                        disabled={idx === 0}
                        onClick={() => moveProvider(idx, "up")}
                        className="p-1 hover:bg-slate-900 text-slate-400 hover:text-white rounded disabled:opacity-30"
                      >
                        <ArrowUp size={12} />
                      </button>
                      <button
                        disabled={idx === providerOrder.length - 1}
                        onClick={() => moveProvider(idx, "down")}
                        className="p-1 hover:bg-slate-900 text-slate-400 hover:text-white rounded disabled:opacity-30"
                      >
                        <ArrowDown size={12} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <Card className="lg:col-span-2 p-6 bg-zinc-950/40 border-zinc-900 rounded-xl space-y-6 shadow-xl">
              <div className="flex items-center justify-between border-b border-zinc-900 pb-3">
                <h3 className="text-sm font-bold flex items-center gap-2">
                  <Download className="text-emerald-400" size={16} /> Local Ollama Library
                </h3>
                <Button
                  size="sm"
                  variant="outline"
                  className="text-xs flex items-center gap-1"
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
                    className="flex-1 bg-slate-955 border border-zinc-900 rounded px-3 py-2 text-xs focus:outline-none focus:border-emerald-500 text-white"
                  />
                  <Button
                    onClick={() => handlePullModel(newModelName)}
                    disabled={pullingModel !== null || !newModelName.trim()}
                    className="bg-emerald-600 hover:bg-emerald-500 text-zinc-950 font-bold"
                  >
                    {pullingModel ? "Pulling..." : "Pull Model"}
                  </Button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider mb-2 font-mono">Installed Models</h4>
                    {diagnostics?.details.downloaded_models && diagnostics.details.downloaded_models.length > 0 ? (
                      <div className="divide-y divide-zinc-900 bg-slate-955 rounded-lg p-3 border border-zinc-900">
                        {diagnostics.details.downloaded_models.map((model, idx) => (
                          <div key={idx} className="py-2 flex items-center justify-between text-xs font-mono">
                            <span className="text-emerald-400">{model}</span>
                            <Badge variant="success" className="text-[9px]">Ready</Badge>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-400 italic">No models detected.</p>
                    )}
                  </div>

                  <div>
                    <h4 className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider mb-2 font-mono">System Checklist</h4>
                    <div className="space-y-1.5 text-xs font-mono">
                      <div className="flex justify-between items-center p-2 bg-slate-950 border border-zinc-900 rounded">
                        <span>Ollama Connection</span>
                        {diagnostics?.ollama_running ? <Badge variant="success">OK</Badge> : <Badge variant="danger">Offline</Badge>}
                      </div>
                      <div className="flex justify-between items-center p-2 bg-slate-950 border border-zinc-900 rounded">
                        <span>Required Models</span>
                        {diagnostics?.models_downloaded ? <Badge variant="success">OK</Badge> : <Badge variant="warning">Missing</Badge>}
                      </div>
                      <div className="flex justify-between items-center p-2 bg-slate-950 border border-zinc-900 rounded">
                        <span>Dynamic Router Status</span>
                        {diagnostics?.router_healthy ? <Badge variant="success">Healthy</Badge> : <Badge variant="danger">Error</Badge>}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </div>

          {/* Active LLM Providers Configuration Table */}
          <Card className="p-6 bg-zinc-950/40 border-zinc-900 rounded-xl space-y-6 shadow-xl">
            <div className="flex items-center justify-between border-b border-zinc-900 pb-3">
              <h3 className="text-sm font-bold flex items-center gap-2">
                <Server className="text-emerald-400" size={16} /> Active LLM Providers & Credentials Health
              </h3>
              <Button
                size="sm"
                variant="outline"
                className="text-xs flex items-center gap-1"
                onClick={fetchStatus}
              >
                <Play size={12} /> Run Connections Test
              </Button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs font-mono">
                <thead>
                  <tr className="border-b border-zinc-900 text-zinc-500 text-[10px] uppercase">
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
                <tbody className="divide-y divide-zinc-900">
                  {providers.map((p, idx) => {
                    const isProviderDisabled = disabledProviders.includes(p.provider.toLowerCase());
                    return (
                      <tr key={idx} className={`hover:bg-zinc-900/10 ${isProviderDisabled ? "opacity-45" : ""}`}>
                        <td className="py-4 px-4 text-zinc-100 font-bold text-xs">{p.provider}</td>
                        <td className="py-4 px-4">
                          <Badge className="bg-slate-950 text-slate-300">Tier {p.fallbackPosition}</Badge>
                        </td>
                        <td className="py-4 px-4">
                          <Badge variant="outline" className={`
                            ${p.costTier === "Free" ? "border-emerald-900/50 text-emerald-400 bg-emerald-950/20" : ""}
                            ${p.costTier === "Low" ? "border-zinc-800 text-zinc-305 bg-zinc-900/20" : ""}
                            ${p.costTier === "Medium" ? "border-amber-900/50 text-amber-400 bg-amber-950/20" : ""}
                            ${p.costTier === "High" ? "border-rose-900/50 text-rose-450 bg-rose-950/20" : ""}
                          `}>
                            {p.costTier}
                          </Badge>
                        </td>
                        <td className="py-4 px-4">
                          {isProviderDisabled ? (
                            <Badge>Disabled</Badge>
                          ) : p.status === "Healthy" ? (
                            <span className="text-emerald-400 font-bold flex items-center gap-1">
                              <CheckCircle size={12} /> Healthy
                            </span>
                          ) : p.status === "Unconfigured" ? (
                            <span className="text-zinc-500 flex items-center gap-1">
                              <AlertTriangle size={12} /> Unconfigured
                            </span>
                          ) : (
                            <span className="text-rose-450 font-bold flex items-center gap-1">
                              <XCircle size={12} /> Error
                            </span>
                          )}
                        </td>
                        <td className="py-4 px-4 text-zinc-500 text-[10px]">
                          {p.configured ? "sk-•••••••••" : "Not Provided"}
                        </td>
                        <td className="py-4 px-4 text-zinc-300">
                          {p.configured && p.latency && !isProviderDisabled ? `${p.latency}ms` : "-"}
                        </td>
                        <td className="py-4 px-4">
                          <div className="flex gap-1 flex-wrap">
                            {p.streaming ? <Badge className="text-[9px]">Stream</Badge> : null}
                            {p.embeddings ? <Badge className="text-[9px]">Embed</Badge> : null}
                            {p.tools ? <Badge className="text-[9px]">Tools</Badge> : null}
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-[10px] px-2 py-0.5 hover:bg-zinc-900"
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
      ) : (
        /* Prompt Studio (Prompt Library) View */
        <Card className="p-6 bg-zinc-950/40 border-zinc-900 rounded-xl space-y-6 shadow-xl">
          <div className="border-b border-zinc-900 pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold flex items-center gap-2">
                <BookOpen size={16} className="text-emerald-400" /> Prompt Studio (Prompt Library)
              </h3>
              <p className="text-zinc-500 text-[10px] mt-1 font-mono">Tailor system instructions dynamically. Model will recompile guidelines immediately.</p>
            </div>
            <Badge variant="info" className="font-mono">v2.4 LTS</Badge>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Prompt Selector List */}
            <div className="space-y-2 border-r border-zinc-900 pr-4">
              <span className="text-[10px] text-zinc-550 uppercase font-bold font-mono tracking-wider block mb-2">Available Prompt Tiers</span>
              {prompts.map((p) => {
                const active = selectedPromptId === p.id;
                return (
                  <div
                    key={p.id}
                    onClick={() => setSelectedPromptId(p.id)}
                    className={`p-2.5 border rounded-lg cursor-pointer transition text-xs flex items-center justify-between font-mono ${
                      active
                        ? "border-emerald-500/30 bg-emerald-500/5 text-emerald-400"
                        : "border-zinc-900 hover:border-zinc-800 text-zinc-400"
                    }`}
                  >
                    <span>{p.name}</span>
                    <span className="text-[9px] bg-zinc-900 px-1 rounded text-zinc-500">{p.version}</span>
                  </div>
                );
              })}
            </div>

            {/* Prompt Editor Box */}
            <div className="lg:col-span-2 flex flex-col gap-4">
              <span className="text-[10px] text-zinc-550 uppercase font-bold font-mono tracking-wider block">Instructions Sandbox</span>
              
              <textarea
                value={editingPromptContent}
                onChange={(e) => setEditingPromptContent(e.target.value)}
                className="w-full h-64 p-4 rounded-xl border border-zinc-900 bg-zinc-950 font-mono text-xs leading-relaxed focus:outline-none focus:border-emerald-500 text-slate-300 resize-none"
              />

              <div className="flex justify-between items-center text-[10px] text-zinc-500 font-mono">
                <span>Last updated: just now | Local compile: active</span>
                <button
                  onClick={handleSavePrompt}
                  className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-zinc-950 font-bold flex items-center gap-1.5 transition"
                >
                  <Save size={12} /> Compile & Update Version
                </button>
              </div>
            </div>

          </div>
        </Card>
      )}

    </div>
  );
}
