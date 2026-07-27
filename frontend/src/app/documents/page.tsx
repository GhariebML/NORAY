"use client";

import { useState } from "react";
import {
  FileText, Sparkles, Loader2, Copy, Check, Download,
  Send, RefreshCw, CheckCircle2,
  Brain, FileCode, Mail, Globe, GraduationCap,
} from "lucide-react";
import { PageHeader, Card, Badge, Button } from "@/components/ui";
import { documentsApi } from "@/lib/api";

const DOCUMENT_TYPES = [
  { id: "ats_resume", label: "ATS Resume", icon: FileText },
  { id: "executive_resume", label: "Executive Resume", icon: FileCode },
  { id: "academic_cv", label: "Academic CV", icon: GraduationCap },
  { id: "cover_letter", label: "Cover Letter", icon: Send },
  { id: "statement_of_purpose", label: "Statement of Purpose", icon: Brain },
  { id: "motivation_letter", label: "Motivation Letter", icon: Sparkles },
  { id: "research_proposal", label: "Research Proposal", icon: FileCode },
  { id: "email", label: "Professional Email", icon: Mail },
  { id: "linkedin_summary", label: "LinkedIn Summary", icon: Globe },
];

interface QualityReport {
  ats_score: number;
  grammar_score: number;
  keyword_coverage: number;
  readability_score: number;
  hallucination_risk: string;
  suggestions: string[];
  overall_quality: string;
}

export default function DocumentsPage() {
  const [docType, setDocType] = useState("ats_resume");
  const [target, setTarget] = useState("");
  const [context, setContext] = useState("");
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [content, setContent] = useState("");
  const [streamedContent, setStreamedContent] = useState("");
  const [quality, setQuality] = useState<QualityReport | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");


  const currentDoc = DOCUMENT_TYPES.find((d) => d.id === docType) || DOCUMENT_TYPES[0];

  async function handleGenerate() {
    if (!target.trim()) return;
    setLoading(true);
    setError("");
    setContent("");
    setStreamedContent("");
    setQuality(null);
    try {
      const result = await documentsApi.generate({
        doc_type: docType,
        target,
        context,
        run_quality_check: true,
      });
      setContent(result.content);
      if (result.quality) setQuality(result.quality);
    } catch (err: any) {
      setError(err.message || "Generation failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleStream() {
    if (!target.trim()) return;
    setLoading(true);
    setError("");
    setContent("");
    setStreamedContent("");
    setQuality(null);
    setStreaming(true);

    try {
      await fetch("/api/profile");

      const nextPublicUrl = process.env.NEXT_PUBLIC_API_URL;
      let streamUrl = "/api/cv/stream";
      if (nextPublicUrl) {
        streamUrl = `${nextPublicUrl}/api/cv/stream`;
      } else if (typeof window !== "undefined") {
        const host = window.location.host;
        if (host.includes("localhost:3000")) {
          streamUrl = "http://localhost:8001/api/cv/stream";
        } else if (host.includes("127.0.0.1:3000")) {
          streamUrl = "http://127.0.0.1:8001/api/cv/stream";
        }
      }

      const response = await fetch(streamUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          doc_type: docType,
          target,
          context,
          session_id: "doc-gen-" + Date.now(),
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No stream reader");

      let full = "";
      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const text = decoder.decode(value);
        const lines = text.split("\n");
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === "chunk") {
                full += data.content;
                setStreamedContent(full);
              } else if (data.type === "done") {
                setContent(full);
                setStreaming(false);
                // Run quality check after streaming completes
                const qc = await documentsApi.checkQuality({ target: full, doc_type: docType });
                if (qc?.report) setQuality(qc.report);
              }
            } catch { }
          }
        }
      }
    } catch (err: any) {
      setError(err.message || "Streaming failed");
      if (!content && streamedContent) setContent(streamedContent);
    } finally {
      setLoading(false);
      setStreaming(false);
    }
  }

  function handleCopy() {
    navigator.clipboard.writeText(content || streamedContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleDownload() {
    const text = content || streamedContent;
    const blob = new Blob([text], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${docType}_${Date.now()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  const displayContent = content || streamedContent;

  return (
    <div className="flex flex-col h-full select-none">
      <PageHeader
        title="AI Document Generator"
        description="ATS resumes, cover letters, SOPs, research proposals — all AI-generated with quality checks"
      />

      <div className="flex-1 flex gap-4 overflow-hidden">
        {/* Left Panel - Controls */}
        <div className="w-[35%] flex flex-col gap-4 overflow-y-auto pr-2 shrink-0">
          {/* Document Type Selector */}
          <Card className="p-4">
            <h3 className="text-xs font-bold text-zinc-300 mb-3 uppercase tracking-wider">Document Type</h3>
            <div className="grid grid-cols-2 gap-1.5">
              {DOCUMENT_TYPES.map((dt) => {
                const Icon = dt.icon;
                return (
                  <button
                    key={dt.id}
                    onClick={() => setDocType(dt.id)}
                    className={`flex items-center gap-1.5 px-2 py-2 rounded-lg text-[10px] font-medium transition-colors ${
                      docType === dt.id
                        ? "bg-emerald-950/20 border border-emerald-500/20 text-emerald-400"
                        : "bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-zinc-200"
                    }`}
                  >
                    <Icon size={12} />
                    <span className="truncate">{dt.label}</span>
                  </button>
                );
              })}
            </div>
          </Card>

          {/* Input Fields */}
          <Card className="p-4 space-y-3">
            <div>
              <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1 block">
                Target / Job / Scholarship
              </label>
              <textarea
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                placeholder={docType === "ats_resume" ? "Paste job description or target company + role..." : "Describe the target program, scholarship, or opportunity..."}
                rows={4}
                className="w-full rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 py-2 text-[11px] text-zinc-200 placeholder-zinc-500 focus:border-emerald-500 focus:outline-none resize-none"
              />
            </div>

            <div>
              <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-1 block">
                Additional Context (optional)
              </label>
              <textarea
                value={context}
                onChange={(e) => setContext(e.target.value)}
                placeholder="Any additional details, requirements, or notes..."
                rows={3}
                className="w-full rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 py-2 text-[11px] text-zinc-200 placeholder-zinc-500 focus:border-emerald-500 focus:outline-none resize-none"
              />
            </div>

            <div className="flex gap-2">
              <Button onClick={handleGenerate} disabled={loading || !target.trim()} variant="primary" className="flex-1">
                {loading ? <Loader2 size={12} className="animate-spin" /> : <Sparkles size={12} />}
                {loading ? "Generating..." : "Generate"}
              </Button>
              <Button onClick={handleStream} disabled={loading || !target.trim()} variant="secondary">
                <RefreshCw size={12} />
                Stream
              </Button>
            </div>
          </Card>

          {/* Quality Report */}
          {quality && (
            <Card className="p-4">
              <h3 className="text-xs font-bold text-zinc-300 mb-3 uppercase tracking-wider flex items-center gap-1.5">
                <CheckCircle2 size={12} className="text-emerald-400" />
                Quality Report
              </h3>
              <div className="grid grid-cols-2 gap-2 mb-3">
                {[
                  { label: "ATS Score", value: quality.ats_score },
                  { label: "Grammar", value: quality.grammar_score },
                  { label: "Keywords", value: quality.keyword_coverage },
                  { label: "Readability", value: quality.readability_score },
                ].map((m) => (
                  <div key={m.label} className="p-2 rounded bg-zinc-900/50 border border-zinc-800">
                    <div className="text-[9px] text-zinc-500">{m.label}</div>
                    <div className={`text-sm font-bold font-heading ${
                      m.value >= 80 ? "text-emerald-400" : m.value >= 60 ? "text-amber-400" : "text-red-400"
                    }`}>{m.value}%</div>
                  </div>
                ))}
              </div>

              <div className="flex items-center gap-2 text-[10px] mb-2">
                <span className="text-zinc-500">Hallucination Risk:</span>
                <Badge variant={quality.hallucination_risk === "low" ? "success" : "warning"} className="text-[9px]">
                  {quality.hallucination_risk}
                </Badge>
                <span className="text-zinc-500">Overall:</span>
                <Badge variant={quality.overall_quality === "excellent" ? "success" : quality.overall_quality === "good" ? "info" : "warning"} className="text-[9px]">
                  {quality.overall_quality}
                </Badge>
              </div>

              {quality.suggestions && quality.suggestions.length > 0 && (
                <div>
                  <span className="text-[9px] text-zinc-500 block mb-1">Suggestions:</span>
                  {quality.suggestions.slice(0, 3).map((s, i) => (
                    <p key={i} className="text-[9px] text-zinc-400 flex items-start gap-1">
                      <span className="text-emerald-400 mt-0.5">•</span> {s}
                    </p>
                  ))}
                </div>
              )}
            </Card>
          )}
        </div>

        {/* Right Panel - Document Preview */}
        <div className="flex-1 flex flex-col rounded-xl border border-zinc-900 bg-zinc-950/40 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-zinc-900 bg-zinc-950">
            <div className="flex items-center gap-2 text-[10px] text-zinc-400">
              <currentDoc.icon size={14} className="text-emerald-400" />
              <span className="font-semibold text-zinc-200">{currentDoc.label}</span>
              {displayContent && (
                <span className="text-zinc-600">| {displayContent.length.toLocaleString()} chars</span>
              )}
            </div>
            <div className="flex items-center gap-1.5">
              {displayContent && (
                <>
                  <button onClick={handleCopy}
                    className="flex items-center gap-1 px-2 py-1 rounded border border-zinc-800 text-[10px] text-zinc-400 hover:text-white">
                    {copied ? <Check size={11} className="text-emerald-400" /> : <Copy size={11} />}
                    {copied ? "Copied" : "Copy"}
                  </button>
                  <button onClick={handleDownload}
                    className="flex items-center gap-1 px-2 py-1 rounded bg-emerald-600 text-zinc-950 text-[10px] font-bold hover:bg-emerald-500">
                    <Download size={11} /> Download
                  </button>
                </>
              )}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-6 bg-[#0a0a0c]">
            {!displayContent && !loading && !error && (
              <div className="flex flex-col items-center justify-center h-full text-zinc-600">
                <FileText size={40} className="mb-3 opacity-20" />
                <p className="text-sm text-zinc-500">Enter your requirements and generate a document</p>
                <p className="text-[10px] text-zinc-600 mt-1">
                  Choose a document type, fill in the target, and click Generate or Stream
                </p>
              </div>
            )}

            {loading && !streaming && (
              <div className="flex items-center justify-center h-full text-zinc-500">
                <Loader2 size={20} className="animate-spin mr-3" />
                <span>AI is generating your {currentDoc.label}...</span>
              </div>
            )}

            {streaming && (
              <div className="flex items-center gap-2 text-[10px] text-emerald-400 mb-4 font-mono">
                <Loader2 size={10} className="animate-spin" />
                <span>Streaming generation...</span>
              </div>
            )}

            {error && (
              <div className="mb-4 p-3 rounded-lg bg-red-950/20 border border-red-500/20 text-red-400 text-[11px]">
                {error}
              </div>
            )}

            {displayContent && (
              <div className="mx-auto max-w-3xl">
                <div className="rounded-lg border border-zinc-800 bg-white p-8 text-zinc-900 shadow-2xl">
                  <div className="prose prose-sm max-w-none whitespace-pre-wrap font-sans text-[11px] leading-relaxed">
                    {displayContent}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
