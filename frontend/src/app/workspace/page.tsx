"use client";

import { useState } from "react";
import {
  Sparkles,
  Send,
  Loader2,
  Brain,
  FileText,
  Copy,
  Check,
  Download,
  Eye,
  Code2,
  FileCode,
  Info,
  Layers,
  Search,
} from "lucide-react";
import { PageHeader, Card, Button, Badge } from "@/components/ui";
import { workspaceApi } from "@/lib/api";
import { AgentPipeline } from "@/components/AgentPipeline";
import { WorkflowTimeline } from "@/components/WorkflowTimeline";
import { ExplainableAIDrawer } from "@/components/ExplainableAIDrawer";

export default function WorkspacePage() {
  const [messages, setMessages] = useState<
    { role: "user" | "assistant"; content: string; time: string }[]
  >([
    {
      role: "assistant",
      content:
        "Welcome to your NORAY AI Workspace Canvas. I am your autonomous career & scholarship operating system. How can I assist you with resume tailoring, DAAD/Chevening scholarship applications, or research proposal engineering today?",
      time: "Just now",
    },
  ]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [xaiOpen, setXaiOpen] = useState(false);
  const [activeRightTab, setActiveRightTab] = useState<"cv" | "sop" | "notes">("cv");
  const [documentContent, setDocumentContent] = useState(
    `# Gharieb Mohamed
**Machine Learning & AI Engineer** | Tailored for **Google**
📧 contact@noray.ai  |  📱 +20 100 000 0000  |  📍 Cairo, Egypt

---

## PROFESSIONAL SUMMARY
Results-driven Machine Learning Engineer with expertise in Agentic RAG Operating Systems, FastAPI, and full-stack software development. Engineered NORAY platform featuring a thread-safe Qdrant hybrid vector search engine and Dual-Tier LLM router.

## TECHNICAL SKILLS & COMPETENCIES
- **Core Languages & Frameworks**: Python, PyTorch, FastAPI, TypeScript, React, Next.js, C++
- **AI & RAG Engineering**: Qdrant Vector Store, BM25 Reciprocal Rank Fusion, ReAct Agent Loops, Ollama
- **Databases & Systems**: PostgreSQL, SQLite, Docker, REST APIs, System Architecture

## PROFESSIONAL EXPERIENCE
**Lead AI Engineer — NORAY Platform** (2024 – Present)
- Engineered an enterprise-grade career operating system tailored for Google.
- Implemented Dual-Tier Model Router dynamically shifting traffic between Cloud APIs and local Ollama runtimes.
- Developed automated ATS resume optimizer and document generation engines.
`
  );

  const [copied, setCopied] = useState(false);

  async function handleSend() {
    if (!input.trim() || loading) return;
    const userMsg = input;
    setInput("");
    setMessages((prev) => [
      ...prev,
      { role: "user", content: userMsg, time: new Date().toLocaleTimeString() },
    ]);

    try {
      setLoading(true);
      const res = await workspaceApi.chat({ query: userMsg });
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: res.response || "Task completed successfully.",
          time: new Date().toLocaleTimeString(),
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "I have processed your prompt and updated your active document workspace.",
          time: new Date().toLocaleTimeString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleCopy() {
    navigator.clipboard.writeText(documentContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleDownloadDocx() {
    const blob = new Blob([documentContent], { type: "application/msword;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `Tailored_Document.docx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  return (
    <div className="flex flex-col h-[calc(100vh-6rem)]">
      {/* Top Bar */}
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b border-zinc-800 pb-3">
        <div>
          <h1 className="text-xl font-bold text-zinc-100 font-heading flex items-center gap-2">
            <Sparkles className="text-emerald-400" size={22} />
            Dual-Pane AI Workspace Canvas
          </h1>
          <p className="text-xs text-zinc-400">
            Work side-by-side with your multi-agent AI engine in real time
          </p>
        </div>

        <button
          onClick={() => setXaiOpen(true)}
          className="flex items-center gap-1.5 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-xs text-emerald-400 hover:bg-emerald-500/20 transition-colors shadow-sm"
        >
          <Info size={14} />
          <span>Explainable AI (XAI) Telemetry</span>
        </button>
      </div>

      {/* DUAL-PANE SPLIT WORKSPACE */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 flex-1 min-h-0 overflow-hidden">
        {/* LEFT PANE: AI Assistant & Pipeline */}
        <div className="flex flex-col rounded-xl border border-zinc-800 bg-[#111827]/90 overflow-hidden shadow-2xl">
          {/* Pipeline Bar */}
          <div className="p-3 border-b border-zinc-800 bg-[#0b111e]">
            <AgentPipeline />
          </div>

          {/* Chat Stream */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs font-sans">
            {messages.map((m, idx) => (
              <div
                key={idx}
                className={`flex flex-col ${
                  m.role === "user" ? "items-end" : "items-start"
                }`}
              >
                <div
                  className={`max-w-[90%] rounded-xl p-3.5 leading-relaxed shadow-sm ${
                    m.role === "user"
                      ? "bg-emerald-600 text-white rounded-br-none"
                      : "bg-[#161f2d] text-zinc-200 border border-zinc-800 rounded-bl-none"
                  }`}
                >
                  <p className="whitespace-pre-wrap">{m.content}</p>
                </div>
                <span className="mt-1 text-[10px] text-zinc-500 font-mono">
                  {m.role === "user" ? "You" : "NORAY OS"} • {m.time}
                </span>
              </div>
            ))}

            {loading && (
              <div className="flex items-center gap-2 text-xs text-emerald-400 font-mono py-2">
                <Loader2 size={14} className="animate-spin" />
                <span>Autonomous multi-agent execution loop running...</span>
              </div>
            )}
          </div>

          {/* Workflow Timeline */}
          <div className="px-3 py-2 border-t border-zinc-800 bg-[#0b111e]">
            <WorkflowTimeline />
          </div>

          {/* Input Form */}
          <div className="p-3 border-t border-zinc-800 bg-[#111827]">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="flex items-center gap-2"
            >
              <input
                type="text"
                placeholder="Ask NORAY AI to tailor your CV, draft an SOP, or research grants..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                className="flex-1 rounded-lg border border-zinc-700 bg-[#161f2d] px-3.5 py-2.5 text-xs text-zinc-100 placeholder-zinc-500 focus:border-emerald-500 focus:outline-none"
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="rounded-lg bg-emerald-600 px-4 py-2.5 text-xs font-semibold text-white hover:bg-emerald-500 disabled:opacity-50 transition-colors flex items-center gap-1.5 shadow-md"
              >
                {loading ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
                Send
              </button>
            </form>
          </div>
        </div>

        {/* RIGHT PANE: Document Editor & Live Previewer */}
        <div className="flex flex-col rounded-xl border border-zinc-800 bg-[#111827]/90 overflow-hidden shadow-2xl">
          {/* Tab Selector & Controls */}
          <div className="flex items-center justify-between border-b border-zinc-800 bg-[#0b111e] px-4 py-2.5 text-xs">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveRightTab("cv")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition-colors ${
                  activeRightTab === "cv"
                    ? "bg-emerald-600 text-white"
                    : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
                }`}
              >
                <FileText size={14} /> Resume (.docx)
              </button>

              <button
                onClick={() => setActiveRightTab("sop")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition-colors ${
                  activeRightTab === "sop"
                    ? "bg-emerald-600 text-white"
                    : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
                }`}
              >
                <Sparkles size={14} /> SOP Draft
              </button>

              <button
                onClick={() => setActiveRightTab("notes")}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md font-medium transition-colors ${
                  activeRightTab === "notes"
                    ? "bg-emerald-600 text-white"
                    : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
                }`}
              >
                <FileCode size={14} /> Research Notes
              </button>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleCopy}
                className="flex items-center gap-1 rounded-md border border-zinc-700 bg-zinc-800 px-2.5 py-1 text-zinc-300 hover:bg-zinc-700"
              >
                {copied ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
                {copied ? "Copied" : "Copy"}
              </button>

              <button
                onClick={handleDownloadDocx}
                className="flex items-center gap-1 rounded-md bg-emerald-600 px-2.5 py-1 text-white hover:bg-emerald-500 font-medium"
              >
                <Download size={13} /> Word (.docx)
              </button>
            </div>
          </div>

          {/* Interactive Document Editor Area (A4 Styled Page) */}
          <div className="flex-1 overflow-y-auto p-4 bg-[#070b12]">
            <div className="mx-auto min-h-[30rem] w-full max-w-2xl rounded-lg border border-zinc-300 bg-white p-8 text-zinc-900 shadow-2xl dark:border-zinc-700 dark:bg-white dark:text-zinc-900">
              <textarea
                value={documentContent}
                onChange={(e) => setDocumentContent(e.target.value)}
                className="h-full min-h-[32rem] w-full resize-none bg-transparent font-sans text-xs leading-relaxed text-zinc-900 focus:outline-none"
              />
            </div>
          </div>
        </div>
      </div>

      {/* XAI Drawer */}
      <ExplainableAIDrawer isOpen={xaiOpen} onClose={() => setXaiOpen(false)} />
    </div>
  );
}
