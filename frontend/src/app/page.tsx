"use client";

import { useEffect, useState } from "react";
import {
  Briefcase,
  GraduationCap,
  TrendingUp,
  FileText,
  Clock,
  CheckCircle,
  AlertCircle,
  Cpu,
  Sparkles,
  Server,
  Zap,
  Check,
  Search,
  Activity,
  Play,
  RotateCcw,
  ArrowRight,
  Database,
  Layers,
  HardDrive,
  Users,
  Eye,
  Key,
  Shield,
  HelpCircle,
  Compass,
  Upload,
  Minimize2,
} from "lucide-react";
import {
  PageHeader,
  StatCard,
  Card,
  Badge,
  Button,
  LoadingSpinner,
  EmptyState,
  PageTransition,
} from "@/components/ui";
import { applicationsApi, workspaceApi, type Application } from "@/lib/api";
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  AreaChart, Area,
} from "recharts";
import { motion, AnimatePresence } from "framer-motion";

interface SystemHealth {
  status: string;
  details: {
    database: string;
    vector_store: string;
    graph_store: string;
    llm: string;
    mcp: string;
  };
  gateway: {
    metrics: {
      total_requests: number;
      total_input_tokens: number;
      total_output_tokens: number;
      total_estimated_cost: number;
      total_latency_ms: number;
    };
    provider_states: Record<string, boolean>;
    models: string[];
    active_provider: string;
  };
}

interface AgentStatus {
  id: string;
  name: string;
  role: string;
  status: "idle" | "running" | "completed";
  currentTask: string;
  progress: number;
  executionTime: string;
  provider: string;
  model: string;
  details: string[];
}

export default function DashboardPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [stats, setStats] = useState<Record<string, unknown>>({});
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [docs, setDocs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Time and welcome states
  const [time, setTime] = useState("");
  const [activeAgentId, setActiveAgentId] = useState<string | null>(null);

  // Active providers settings
  const [selectedProvider, setSelectedProvider] = useState("local");

  // Workflow monitor state
  const [workflowStep, setWorkflowStep] = useState(0);
  const [workflowActive, setWorkflowActive] = useState(true);

  // Live event feed state
  const [events, setEvents] = useState<string[]>([
    "Gateway check: Vector store indexed",
    "Active session created: General Workspace",
  ]);

  // Key shortcuts listener helper info
  const [showHotkeys, setShowHotkeys] = useState(false);

  // Clock Ticker
  useEffect(() => {
    const updateTime = () => {
      const d = new Date();
      setTime(d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit" }));
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  // Workflow loop simulation
  useEffect(() => {
    if (!workflowActive) return;
    const interval = setInterval(() => {
      setWorkflowStep((prev) => (prev + 1) % 6);
    }, 4000);
    return () => clearInterval(interval);
  }, [workflowActive]);

  // Live event feed simulation
  useEffect(() => {
    const mockLogs = [
      "Planner initialized: generated plan task list",
      "Graph RAG: searched entity relational triples",
      "Gateway: Ollama llama3.1 local response returned in 320ms",
      "Crawler: matched 2 job postings from index",
      "Optimizer: refined career CV match criteria",
      "MCP: active schema mapping complete",
    ];
    const interval = setInterval(() => {
      const randomLog = mockLogs[Math.floor(Math.random() * mockLogs.length)];
      setEvents((prev) => [randomLog, ...prev.slice(0, 7)]);
    }, 6000);
    return () => clearInterval(interval);
  }, []);

  async function loadData() {
    try {
      setLoading(true);
      const apiBase = typeof window !== "undefined" ? "" : "http://localhost:8001";
      const [appData, healthData, docsData] = await Promise.all([
        applicationsApi.list({}),
        fetch(`${apiBase}/api/health`).then((r) => r.json()),
        workspaceApi.listDocs(),
      ]);
      setApplications(appData.applications || []);
      setStats(appData.stats || {});
      setHealth(healthData);
      setSelectedProvider(healthData.gateway.active_provider || "local");
      setDocs(docsData || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load command center");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  // Handle provider switch trigger
  async function handleProviderToggle(provider: string) {
    setSelectedProvider(provider);
    try {
      const apiBase = typeof window !== "undefined" ? "" : "http://localhost:8001";
      await fetch(`${apiBase}/api/health/setup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ active_provider: provider }),
      });
      // reload health data
      const healthData = await fetch(`${apiBase}/api/health`).then((r) => r.json());
      setHealth(healthData);
    } catch (err) {
      console.error("Failed to switch active provider", err);
    }
  }

  if (loading) return <LoadingSpinner />;

  const jobCount = applications.filter((a) => a.type === "job").length;
  const scholarshipCount = applications.filter((a) => a.type === "scholarship").length;
  const interviewCount = applications.filter((a) =>
    ["interview", "shortlisted"].includes(a.status)
  ).length;
  const offerCount = applications.filter((a) =>
    ["awarded", "accepted"].includes(a.status)
  ).length;

  const recentApps = [...applications]
    .sort((a, b) => (b.applied_date || "").localeCompare(a.applied_date || ""))
    .slice(0, 4);

  const upcomingDeadlines = applications
    .filter((a) => a.deadline && new Date(a.deadline) > new Date())
    .sort((a, b) => (a.deadline || "").localeCompare(b.deadline || ""))
    .slice(0, 4);

  // Active AI Agents Data
  const agents: AgentStatus[] = [
    {
      id: "planner",
      name: "Task Planner",
      role: "Orchestration & DAG planner",
      status: workflowStep === 0 ? "running" : "completed",
      currentTask: workflowStep === 0 ? "Analyzing prompt query structure..." : "Idle",
      progress: workflowStep === 0 ? 40 : 100,
      executionTime: "115ms",
      provider: "Ollama Local",
      model: "llama3.1:8b",
      details: ["DAG Generation", "Router Intent mapping", "Token validation checks"],
    },
    {
      id: "research",
      name: "Research Agent",
      role: "Web & document vector miner",
      status: [1, 2].includes(workflowStep) ? "running" : workflowStep > 2 ? "completed" : "idle",
      currentTask: workflowStep === 1 ? "Query expansion..." : workflowStep === 2 ? "Fetching vector store nodes..." : "Idle",
      progress: workflowStep === 1 ? 30 : workflowStep === 2 ? 75 : workflowStep > 2 ? 100 : 0,
      executionTime: "1.2s",
      provider: "Ollama Local",
      model: "llama3.1:8b",
      details: ["SentenceTransformer encoding", "Hybrid BM25 sparse index matching", "CrossEncoder reranking"],
    },
    {
      id: "graph",
      name: "Knowledge Agent",
      role: "Semantic Graph traversal compiler",
      status: workflowStep === 3 ? "running" : workflowStep > 3 ? "completed" : "idle",
      currentTask: workflowStep === 3 ? "Traversing entity relational triples..." : "Idle",
      progress: workflowStep === 3 ? 60 : workflowStep > 3 ? 100 : 0,
      executionTime: "410ms",
      provider: "SQLite/Network",
      model: "Custom Graph",
      details: ["Entity relationship checks", "Path validation", "Triples compression"],
    },
    {
      id: "resume",
      name: "Resume / CV Optimizer",
      role: "Profile ATS alignment matching",
      status: workflowStep === 4 ? "running" : workflowStep > 4 ? "completed" : "idle",
      currentTask: workflowStep === 4 ? "Comparing CV with job guidelines..." : "Idle",
      progress: workflowStep === 4 ? 80 : workflowStep > 4 ? 100 : 0,
      executionTime: "890ms",
      provider: "Ollama Local",
      model: "llama3.1:8b",
      details: ["ATS Keyword matching", "Profile mapping verification", "HTML output structuring"],
    }
  ];

  // Recharts Chart datasets
  const STATUS_COLORS: Record<string, string> = {
    discovered: "#52525b",
    preparing: "#3b82f6",
    submitted: "#f59e0b",
    interview: "#8b5cf6",
    shortlisted: "#c084fc",
    awarded: "#10b981",
    accepted: "#059669",
    rejected: "#ef4444",
  };

  const statusData = Object.entries(
    applications.reduce((acc, a) => {
      acc[a.status] = (acc[a.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>)
  ).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value,
    fill: STATUS_COLORS[name] || "#a1a1aa",
  }));

  // Timeline data (group by week)
  const timelineData = (() => {
    const weeks: Record<string, number> = {};
    applications.forEach((a) => {
      if (a.applied_date) {
        const d = new Date(a.applied_date);
        const weekStart = new Date(d);
        weekStart.setDate(d.getDate() - d.getDay());
        const key = weekStart.toLocaleDateString("en-US", { month: "short", day: "numeric" });
        weeks[key] = (weeks[key] || 0) + 1;
      }
    });
    return Object.entries(weeks)
      .map(([week, count]) => ({ week, count }))
      .sort((a, b) => a.week.localeCompare(b.week))
      .slice(-12);
  })();

  const workflowSteps = [
    { label: "Planner", desc: "Generates Sub-tasks" },
    { label: "Vector Search", desc: "Retrieve Chunks" },
    { label: "Graph Search", desc: "Extract Triples" },
    { label: "Reasoning", desc: "Synthesizing Details" },
    { label: "Verification", desc: "Grounding Confidence" },
    { label: "Report", desc: "Final Synthesis" }
  ];

  return (
    <PageTransition>
      <div className="space-y-6">
        
        {/* SECTION 1: WELCOME MISSION CONTROL HEADER */}
        <Card className="p-6 border-zinc-800 bg-zinc-950/40 relative overflow-hidden">
          <div className="absolute right-0 top-0 h-full w-1/3 bg-gradient-to-l from-emerald-500/5 to-transparent pointer-events-none" />
          
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="flex items-center gap-4">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-zinc-900 border border-zinc-850">
                <Users className="text-emerald-400" size={20} />
              </div>
              <div>
                <p className="text-[10px] uppercase font-bold tracking-wider text-zinc-500">NORAY OS MISSION CONTROL</p>
                <h1 className="text-lg font-bold text-zinc-100 mt-0.5">Welcome back, Operator</h1>
                <p className="text-[10px] text-zinc-400 mt-1 flex items-center gap-2">
                  <span className="flex items-center gap-1">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    {selectedProvider === "local" ? "Hybrid/Local mode active" : "Cloud fallback mode active"}
                  </span>
                  <span>|</span>
                  <span>Active LLM: {health?.gateway.active_provider === "local" ? "Llama 3.1 8b" : "GPT/Claude Fallback"}</span>
                </p>
              </div>
            </div>

            {/* Live Clock & Workspace meta */}
            <div className="text-left md:text-right shrink-0">
              <p className="font-mono text-xl font-bold tracking-tight text-zinc-100">{time || "00:00:00"}</p>
              <p className="text-[10px] text-zinc-500 mt-0.5 font-mono">
                {new Date().toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric", year: "numeric" })}
              </p>
            </div>
          </div>
        </Card>

        {/* SECTION 2: QUICK ACTION CARDS */}
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
          {[
            { label: "New AI Chat", href: "/workspace", icon: Sparkles, key: "C" },
            { label: "Deep Research", href: "/workspace", icon: Compass, key: "R" },
            { label: "Upload Doc", href: "/workspace", icon: Upload, key: "U" },
            { label: "AI Diagnostics", href: "/diagnostics", icon: Activity, key: "A" },
            { label: "Tracker Board", href: "/tracker", icon: Clock, key: "T" },
            { label: "Profile Setup", href: "/profile", icon: Users, key: "P" },
          ].map((act, idx) => (
            <motion.a
              key={idx}
              href={act.href}
              whileHover={{ y: -3 }}
              className="p-3 border border-zinc-850 rounded-xl bg-zinc-900/40 hover:border-zinc-800 flex flex-col justify-between h-20 transition"
            >
              <act.icon size={16} className="text-emerald-400" />
              <div className="flex items-center justify-between text-[10px]">
                <span className="font-semibold text-zinc-300">{act.label}</span>
                <span className="font-mono text-[8px] bg-zinc-950 border border-zinc-850 px-1 rounded text-zinc-600">
                  Ctrl+{act.key}
                </span>
              </div>
            </motion.a>
          ))}
        </div>

        {/* Top Split Panel: Agents & Workflows */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          
          {/* SECTION 3: ACTIVE AI AGENTS (2 columns) */}
          <Card className="p-5 border-zinc-800 bg-zinc-900/10 lg:col-span-2">
            <div className="flex items-center justify-between border-b border-zinc-850 pb-3 mb-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
                <Cpu size={14} className="text-emerald-400" />
                <span>Active AI Agent Monitors</span>
              </h3>
              <span className="text-[10px] text-zinc-500 font-mono">Running: {agents.filter(a => a.status === "running").length}</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {agents.map((agent) => (
                <div
                  key={agent.id}
                  onClick={() => setActiveAgentId(activeAgentId === agent.id ? null : agent.id)}
                  className={`p-3.5 border rounded-xl bg-zinc-950/40 cursor-pointer transition ${
                    activeAgentId === agent.id 
                      ? "border-emerald-500/40 shadow-[0_0_15px_-5px_rgba(16,185,129,0.15)]" 
                      : "border-zinc-850 hover:border-zinc-800"
                  }`}
                >
                  <div className="flex justify-between items-center mb-2">
                    <div>
                      <h4 className="text-xs font-bold text-zinc-200">{agent.name}</h4>
                      <p className="text-[9px] text-zinc-500">{agent.role}</p>
                    </div>
                    <Badge variant={agent.status === "running" ? "warning" : agent.status === "completed" ? "success" : "default"}>
                      {agent.status}
                    </Badge>
                  </div>

                  {/* Task details */}
                  <p className="text-[10px] text-zinc-400 truncate mb-2">
                    Task: <span className="font-mono text-zinc-300">{agent.currentTask}</span>
                  </p>

                  {/* Progress bar */}
                  <div className="h-1.5 w-full bg-zinc-900 rounded-full overflow-hidden mb-2">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${agent.progress}%` }}
                      className={`h-full rounded-full ${agent.status === "running" ? "bg-amber-500" : "bg-emerald-500"}`}
                    />
                  </div>

                  {/* Provider metadata footer */}
                  <div className="flex justify-between items-center text-[9px] text-zinc-500 font-mono">
                    <span>Model: {agent.model}</span>
                    <span>T: {agent.executionTime}</span>
                  </div>

                  {/* Expanded detail drawer */}
                  <AnimatePresence>
                    {activeAgentId === agent.id && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="mt-3 pt-3 border-t border-zinc-850 overflow-hidden text-[9px] text-zinc-400 space-y-1"
                      >
                        <p className="font-bold text-zinc-300">Execution Stack:</p>
                        {agent.details.map((dt, idx) => (
                          <div key={idx} className="flex items-center gap-1.5">
                            <span className="text-emerald-400">✓</span>
                            <span>{dt}</span>
                          </div>
                        ))}
                      </motion.div>
                    )}
                  </AnimatePresence>

                </div>
              ))}
            </div>
          </Card>

          {/* SECTION 4: AI WORKFLOW MONITOR */}
          <Card className="p-5 border-zinc-800 bg-zinc-900/10 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between border-b border-zinc-850 pb-3 mb-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
                  <Activity size={14} className="text-emerald-400" />
                  <span>AI Workflow Pipeline</span>
                </h3>
                <button 
                  onClick={() => setWorkflowActive(!workflowActive)}
                  className="text-zinc-500 hover:text-zinc-300"
                >
                  {workflowActive ? <Minimize2 size={13} /> : <Play size={13} />}
                </button>
              </div>

              {/* Steps timeline visualizer */}
              <div className="space-y-4 relative pl-4 border-l border-zinc-800">
                {workflowSteps.map((step, idx) => {
                  const active = idx === workflowStep;
                  const completed = idx < workflowStep;

                  return (
                    <div key={idx} className="relative flex items-center gap-3">
                      {/* Step Indicator Dot */}
                      <span className={`absolute -left-[21px] flex h-3.5 w-3.5 items-center justify-center rounded-full border text-[8px] font-bold ${
                        active 
                          ? "bg-amber-500 border-amber-400 text-black animate-pulse" 
                          : completed 
                          ? "bg-emerald-600 border-emerald-500 text-white" 
                          : "bg-zinc-950 border-zinc-800 text-zinc-600"
                      }`}>
                        {completed ? "✓" : idx + 1}
                      </span>

                      <div className="min-w-0">
                        <p className={`text-xs font-semibold ${active ? "text-zinc-100" : completed ? "text-zinc-400" : "text-zinc-600"}`}>
                          {step.label}
                        </p>
                        <p className="text-[9px] text-zinc-500 truncate">{step.desc}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-zinc-850 text-center text-[10px] text-zinc-500">
              {workflowActive ? "Simulating live search reasoning execution..." : "Timeline simulation paused."}
            </div>
          </Card>

        </div>

        {/* Mid Split Panel: System Health, AI Providers, Knowledge Overview */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          
          {/* SECTION 5: SYSTEM HEALTH */}
          <Card className="p-5 border-zinc-800 bg-zinc-900/10">
            <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-4 border-b border-zinc-850 pb-3 flex items-center gap-2">
              <Server size={14} className="text-emerald-400" />
              <span>System Health Monitors</span>
            </h3>

            <div className="grid grid-cols-2 gap-3">
              {[
                { name: "SQLite DB", status: health?.details.database || "healthy", ping: "2ms" },
                { name: "Vector Index", status: health?.details.vector_store || "healthy", ping: "4ms" },
                { name: "Graph Store", status: health?.details.graph_store || "healthy", ping: "12ms" },
                { name: "Ollama Gateway", status: health?.details.llm || "healthy", ping: "340ms" },
                { name: "MCP Sidecars", status: health?.details.mcp || "inactive", ping: "---" },
                { name: "Redis Cache", status: "healthy", ping: "1ms" },
              ].map((sys, idx) => (
                <div key={idx} className="p-2 border border-zinc-850 rounded-lg bg-zinc-950/40 text-[10px] flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-zinc-300">{sys.name}</p>
                    <p className="text-[8px] font-mono text-zinc-500 mt-0.5">Ping: {sys.ping}</p>
                  </div>
                  <Badge variant={sys.status === "healthy" ? "success" : sys.status === "inactive" ? "default" : "danger"}>
                    {sys.status === "healthy" ? "OK" : sys.status === "inactive" ? "INACTIVE" : "ERR"}
                  </Badge>
                </div>
              ))}
            </div>
          </Card>

          {/* SECTION 6: AI PROVIDERS CONTROL */}
          <Card className="p-5 border-zinc-800 bg-zinc-900/10">
            <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-4 border-b border-zinc-850 pb-3 flex items-center gap-2">
              <Sparkles size={14} className="text-emerald-400" />
              <span>AI Providers Gateway Controller</span>
            </h3>

            <div className="space-y-2.5">
              {[
                { id: "local", name: "Ollama (Llama 3.1 Local)", latency: "340ms", cost: "$0.0000", load: "Active" },
                { id: "openai", name: "OpenAI GPT-4o-mini", latency: "790ms", cost: "$0.0015", load: "Standby" },
                { id: "anthropic", name: "Anthropic Claude Sonnet", latency: "1.1s", cost: "$0.0150", load: "Standby" },
              ].map((prov) => {
                const active = selectedProvider === prov.id;
                return (
                  <div
                    key={prov.id}
                    onClick={() => handleProviderToggle(prov.id)}
                    className={`p-2.5 border rounded-lg cursor-pointer transition flex items-center justify-between text-[10px] ${
                      active 
                        ? "border-emerald-500/40 bg-emerald-950/5 text-zinc-100" 
                        : "border-zinc-850 hover:border-zinc-800 text-zinc-400"
                    }`}
                  >
                    <div>
                      <p className="font-bold text-zinc-300">{prov.name}</p>
                      <p className="text-[8px] font-mono text-zinc-500 mt-0.5">Latency: {prov.latency} | Est. Cost: {prov.cost}</p>
                    </div>
                    <Badge variant={active ? "success" : "default"}>
                      {active ? "ACTIVE" : prov.load}
                    </Badge>
                  </div>
                );
              })}
            </div>
          </Card>

          {/* SECTION 7: KNOWLEDGE OVERVIEW & STATS */}
          <Card className="p-5 border-zinc-800 bg-zinc-900/10">
            <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-4 border-b border-zinc-850 pb-3 flex items-center gap-2">
              <Database size={14} className="text-emerald-400" />
              <span>Knowledge Storage Overview</span>
            </h3>

            <div className="grid grid-cols-2 gap-4 text-center">
              <div className="rounded-lg bg-zinc-950/40 border border-zinc-900 p-2.5">
                <span className="text-[9px] text-zinc-500 uppercase font-semibold">Docs Namespaces</span>
                <p className="mt-1 text-lg font-extrabold text-zinc-200">{docs.length}</p>
              </div>

              <div className="rounded-lg bg-zinc-950/40 border border-zinc-900 p-2.5">
                <span className="text-[9px] text-zinc-500 uppercase font-semibold">Graph Triples</span>
                <p className="mt-1 text-lg font-extrabold text-zinc-200">
                  {health?.details.graph_store === "healthy" ? "142" : "0"}
                </p>
              </div>

              <div className="rounded-lg bg-zinc-950/40 border border-zinc-900 p-2.5">
                <span className="text-[9px] text-zinc-500 uppercase font-semibold">Dense Embeddings</span>
                <p className="mt-1 text-lg font-extrabold text-emerald-400">
                  {docs.length * 4}
                </p>
              </div>

              <div className="rounded-lg bg-zinc-950/40 border border-zinc-900 p-2.5">
                <span className="text-[9px] text-zinc-500 uppercase font-semibold">Indexed Chunks</span>
                <p className="mt-1 text-lg font-extrabold text-emerald-400">
                  {docs.length * 4}
                </p>
              </div>
            </div>
          </Card>

        </div>

        {/* Lower Split Panel: Activity Timeline, Live logs feed, Cost Analytics chart */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          
          {/* SECTION 8 & 12: RECENT TIMELINE & LIVE STREAM FEED (2 columns) */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Live streaming event feed logger */}
            <Card className="p-5 border-zinc-800 bg-zinc-900/10 relative overflow-hidden">
              <div className="flex items-center justify-between border-b border-zinc-850 pb-3 mb-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
                  <Layers size={14} className="text-emerald-400 animate-pulse" />
                  <span>Real-time Live Event Log Feed</span>
                </h3>
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
              </div>

              <div className="space-y-2 font-mono text-[9px] text-zinc-400 max-h-[160px] overflow-y-auto pr-1">
                {events.map((evt, idx) => (
                  <div key={idx} className="flex items-start gap-2.5 p-1 border-b border-zinc-900/40">
                    <span className="text-emerald-500">[{new Date().toLocaleTimeString("en-US", { hour12: false })}]</span>
                    <span className="text-zinc-500">INFO:</span>
                    <span>{evt}</span>
                  </div>
                ))}
              </div>
            </Card>

            {/* Daily Recharts usage area chart */}
            {timelineData.length > 0 && (
              <Card className="p-5 border-zinc-800 bg-zinc-900/10">
                <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-4 flex items-center gap-1.5">
                  <TrendingUp size={14} className="text-emerald-400" />
                  <span>Activity Growth & Daily AI Requests</span>
                </h3>
                <div className="h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={timelineData}>
                      <defs>
                        <linearGradient id="colorApps" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#10b981" stopOpacity={0.25} />
                          <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#27272a" strokeOpacity={0.4} />
                      <XAxis dataKey="week" tick={{ fontSize: 10, fill: "#71717a" }} stroke="#27272a" />
                      <YAxis tick={{ fontSize: 10, fill: "#71717a" }} stroke="#27272a" allowDecimals={false} />
                      <Tooltip />
                      <Area
                        type="monotone"
                        dataKey="count"
                        stroke="#10b981"
                        fillOpacity={1}
                        fill="url(#colorApps)"
                        strokeWidth={2.5}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </Card>
            )}

          </div>

          {/* SECTION 10: SYSTEM NOTIFICATIONS & ALERTS */}
          <div className="space-y-6">
            <Card className="p-5 border-zinc-800 bg-zinc-900/10 h-full flex flex-col justify-between">
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-4 border-b border-zinc-850 pb-3 flex items-center gap-2">
                  <AlertCircle size={14} className="text-amber-500" />
                  <span>System Alert Notifications</span>
                </h3>

                <div className="space-y-3">
                  <div className="p-3 border border-amber-500/20 bg-amber-500/5 rounded-lg text-[10px] text-zinc-300">
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-bold text-amber-400">Model Cache Warning</span>
                      <span>1h ago</span>
                    </div>
                    <p className="leading-relaxed text-zinc-400">
                      Ollama model Llama 3.1 8b was loaded from disk, checking local network performance latency indexes.
                    </p>
                  </div>

                  <div className="p-3 border border-emerald-500/20 bg-emerald-500/5 rounded-lg text-[10px] text-zinc-300">
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-bold text-emerald-400">Workflow Complete</span>
                      <span>3h ago</span>
                    </div>
                    <p className="leading-relaxed text-zinc-400">
                      Deep research objectives report compile compiled successfully for objective query.
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-zinc-850 text-center">
                <Button variant="ghost" className="text-[10px] w-full text-zinc-500 hover:text-zinc-300 py-1">
                  Dismiss all notifications
                </Button>
              </div>
            </Card>
          </div>

        </div>

      </div>
    </PageTransition>
  );
}
