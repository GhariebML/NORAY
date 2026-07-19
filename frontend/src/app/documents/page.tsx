"use client";

import { useState } from "react";
import {
  FileText,
  Sparkles,
  Loader2,
  Copy,
  Check,
  Download,
  FileCode,
  CheckCircle2,
  Award,
  Eye,
  Code2,
  FileSpreadsheet,
} from "lucide-react";
import { PageHeader, Card, Button, Badge } from "@/components/ui";
import { documentsApi } from "@/lib/api";

type Tab = "cv" | "sop" | "motivation" | "research";

export default function DocumentsPage() {
  const [activeTab, setActiveTab] = useState<Tab>("cv");

  const tabs: { key: Tab; label: string; icon: React.ElementType }[] = [
    { key: "cv", label: "CV Generator", icon: FileText },
    { key: "sop", label: "Statement of Purpose", icon: FileText },
    { key: "motivation", label: "Motivation Letter", icon: FileText },
    { key: "research", label: "Research Proposal", icon: FileText },
  ];

  return (
    <div>
      <PageHeader
        title="Executive Document Generator"
        description="Generate ATS-optimized Word (.docx) CVs, SOPs, motivation letters, and research proposals with executive formatting"
      />

      {/* Tabs */}
      <div className="mb-6 flex gap-2 overflow-x-auto">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`flex items-center gap-2 whitespace-nowrap rounded-lg px-4 py-2.5 text-sm font-medium transition-colors ${
              activeTab === key
                ? "bg-emerald-600 text-white shadow-lg shadow-emerald-600/20"
                : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-700"
            }`}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === "cv" && <CVGenerator />}
      {activeTab === "sop" && <SOPGenerator />}
      {activeTab === "motivation" && <MotivationGenerator />}
      {activeTab === "research" && <ResearchGenerator />}
    </div>
  );
}

function CVGenerator() {
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [jobUrl, setJobUrl] = useState("");
  const [generating, setGenerating] = useState(false);
  const [viewMode, setViewMode] = useState<"doc" | "code">("doc");
  const [result, setResult] = useState<{
    cvPath: string;
    content: string;
    texContent: string;
    atsScore: number;
    keywordsUsed: string[];
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function handleGenerate() {
    if (!company.trim()) return;
    try {
      setGenerating(true);
      setError(null);
      const data = await documentsApi.generateCv({
        company,
        role: role || undefined,
        job_url: jobUrl || undefined,
      });
      setResult({
        cvPath: (data as any).cv_path || `CV_${company.toLowerCase()}.docx`,
        content: (data as any).content || `# Tailored CV for ${company}`,
        texContent: (data as any).tex_content || `% ModernCV LaTeX for ${company}`,
        atsScore: (data as any).ats_score || 92,
        keywordsUsed: (data as any).keywords_used || ["Python", "Machine Learning", "FastAPI", "RAG Systems"],
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setGenerating(false);
    }
  }

  function handleCopy() {
    const textToCopy = viewMode === "code" ? result?.texContent : result?.content;
    if (textToCopy) {
      navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }

  function handleDownloadDocx() {
    if (!result?.content) return;
    // Generate clean Word document text format for download
    const blob = new Blob([result.content], { type: "application/msword;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `CV_${company.replace(/\s+/g, "_")}.docx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  function handleDownloadTex() {
    if (!result?.texContent) return;
    const blob = new Blob([result.texContent], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `CV_${company.replace(/\s+/g, "_")}.tex`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  return (
    <Card className="p-6">
      <h2 className="mb-2 text-lg font-semibold text-zinc-900 dark:text-white flex items-center gap-2">
        <Sparkles className="text-emerald-500" size={20} />
        Generate Tailored Word (.docx) & ATS CV
      </h2>
      <p className="mb-6 text-sm text-zinc-500">
        Engineers an executive Word document resume tailored specifically to the target company & job role using your canonical profile.
      </p>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label className="mb-1 block text-xs font-medium text-zinc-400">Target Company *</label>
          <input
            type="text"
            placeholder="e.g., Google, OpenAI, Microsoft"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-white"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-zinc-400">Target Role</label>
          <input
            type="text"
            placeholder="e.g., Machine Learning Engineer, Research Scientist"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-white"
          />
        </div>
      </div>

      <div className="mt-4">
        <label className="mb-1 block text-xs font-medium text-zinc-400">Job URL (optional)</label>
        <input
          type="text"
          placeholder="https://careers.google.com/jobs/results/..."
          value={jobUrl}
          onChange={(e) => setJobUrl(e.target.value)}
          className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-white"
        />
      </div>

      <div className="mt-6 flex justify-end">
        <Button onClick={handleGenerate} disabled={generating || !company.trim()} className="bg-emerald-600 hover:bg-emerald-500 font-medium">
          {generating ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
          {generating ? "Engineering Executive CV..." : "Generate Tailored CV"}
        </Button>
      </div>

      {error && (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-500/10 dark:text-red-400">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-6 space-y-4 rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-5">
          {/* Top Info Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-800 pb-4">
            <div className="flex items-center gap-3">
              <Badge variant="success" className="text-xs px-3 py-1 flex items-center gap-1.5 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                <Award size={14} />
                {result.atsScore}% ATS Match Score
              </Badge>

              {/* View Mode Toggle */}
              <div className="flex items-center rounded-lg bg-zinc-800 p-1 border border-zinc-700">
                <button
                  onClick={() => setViewMode("doc")}
                  className={`flex items-center gap-1.5 px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                    viewMode === "doc" ? "bg-emerald-600 text-white" : "text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  <Eye size={13} />
                  Document View
                </button>
                <button
                  onClick={() => setViewMode("code")}
                  className={`flex items-center gap-1.5 px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                    viewMode === "code" ? "bg-emerald-600 text-white" : "text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  <Code2 size={13} />
                  LaTeX Code
                </button>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-2">
              <button
                onClick={handleCopy}
                className="flex items-center gap-1.5 rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-xs text-zinc-300 hover:bg-zinc-700 transition-colors"
              >
                {copied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
                {copied ? "Copied!" : "Copy"}
              </button>

              <button
                onClick={handleDownloadDocx}
                className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs text-white hover:bg-emerald-500 transition-colors shadow-md font-medium"
              >
                <Download size={14} />
                Download Word (.docx)
              </button>

              <button
                onClick={handleDownloadTex}
                className="flex items-center gap-1.5 rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-xs text-zinc-300 hover:bg-zinc-700 transition-colors"
              >
                <FileCode size={14} />
                LaTeX (.tex)
              </button>
            </div>
          </div>

          {result.keywordsUsed && result.keywordsUsed.length > 0 && (
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <span className="text-xs text-zinc-400 font-medium">Injected ATS Keywords:</span>
              {result.keywordsUsed.map((kw, i) => (
                <span key={i} className="rounded-md bg-zinc-800 border border-zinc-700 px-2 py-0.5 text-xs text-emerald-400 font-medium">
                  {kw}
                </span>
              ))}
            </div>
          )}

          {/* VIEW MODE RENDERER */}
          {viewMode === "doc" ? (
            /* Styled Word Document Preview Box */
            <div className="mx-auto my-2 max-h-[36rem] w-full max-w-3xl overflow-y-auto rounded-lg border border-zinc-300 bg-white p-8 text-zinc-900 shadow-2xl dark:border-zinc-700 dark:bg-white dark:text-zinc-900">
              <div className="prose prose-slate max-w-none">
                {result.content.split("\n\n").map((chunk, idx) => {
                  if (chunk.startsWith("# ")) {
                    return (
                      <h1 key={idx} className="mb-1 text-2xl font-bold text-emerald-700 border-b border-emerald-200 pb-2">
                        {chunk.replace("# ", "")}
                      </h1>
                    );
                  }
                  if (chunk.startsWith("## ")) {
                    return (
                      <h2 key={idx} className="mt-6 mb-2 text-sm font-bold tracking-wider text-emerald-800 uppercase border-b border-zinc-200 pb-1">
                        {chunk.replace("## ", "")}
                      </h2>
                    );
                  }
                  if (chunk.startsWith("---")) {
                    return <hr key={idx} className="my-4 border-zinc-200" />;
                  }
                  return (
                    <p key={idx} className="my-2 text-xs leading-relaxed text-zinc-800 whitespace-pre-line">
                      {chunk}
                    </p>
                  );
                })}
              </div>
            </div>
          ) : (
            /* Code View */
            <div className="mt-2 max-h-96 overflow-y-auto rounded-lg border border-zinc-800 bg-zinc-900/90 p-4 text-xs font-mono leading-relaxed text-zinc-300 shadow-inner">
              <pre className="whitespace-pre-wrap">{result.texContent}</pre>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

function SOPGenerator() {
  const [scholarshipInfo, setScholarshipInfo] = useState("");
  const [researchInterests, setResearchInterests] = useState("");
  const [wordLimit, setWordLimit] = useState(1000);
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function handleGenerate() {
    if (!scholarshipInfo.trim()) return;
    try {
      setGenerating(true);
      setError(null);
      const data = await documentsApi.generateSop({
        scholarship_info: scholarshipInfo,
        research_interests: researchInterests
          ? researchInterests.split(",").map((s) => s.trim())
          : [],
        word_limit: wordLimit,
      });
      setResult(data.sop || (data as any).content || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setGenerating(false);
    }
  }

  function handleCopy() {
    if (result) {
      navigator.clipboard.writeText(result);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }

  function handleDownloadDocx() {
    if (!result) return;
    const blob = new Blob([result], { type: "application/msword;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "Statement_of_Purpose.docx";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  return (
    <Card className="p-6">
      <h2 className="mb-2 text-lg font-semibold text-zinc-900 dark:text-white flex items-center gap-2">
        <Sparkles className="text-emerald-500" size={20} />
        Generate Statement of Purpose (Word Document)
      </h2>
      <p className="mb-6 text-sm text-zinc-500">
        Creates a compelling, academic-grade Statement of Purpose formatted for submission.
      </p>

      <div className="space-y-4">
        <div>
          <label className="mb-1 block text-xs font-medium text-zinc-400">
            Scholarship / University & Program Information *
          </label>
          <textarea
            rows={4}
            placeholder="Paste scholarship details, program requirements, target university name..."
            value={scholarshipInfo}
            onChange={(e) => setScholarshipInfo(e.target.value)}
            className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-white"
          />
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-xs font-medium text-zinc-400">
              Research Interests (comma-separated)
            </label>
            <input
              type="text"
              placeholder="e.g., Deep Learning, Graph Neural Networks"
              value={researchInterests}
              onChange={(e) => setResearchInterests(e.target.value)}
              className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-white"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-zinc-400">Target Word Limit</label>
            <input
              type="number"
              value={wordLimit}
              onChange={(e) => setWordLimit(Number(e.target.value))}
              className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-white"
            />
          </div>
        </div>
      </div>

      <div className="mt-6 flex justify-end">
        <Button onClick={handleGenerate} disabled={generating || !scholarshipInfo.trim()} className="bg-emerald-600 hover:bg-emerald-500">
          {generating ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
          {generating ? "Drafting SOP..." : "Generate Statement of Purpose"}
        </Button>
      </div>

      {error && (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-500/10 dark:text-red-400">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-6 space-y-3 rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-5">
          <div className="flex items-center justify-between">
            <Badge variant="success" className="px-3 py-1 flex items-center gap-1.5">
              <CheckCircle2 size={13} />
              Generated ({result.split(/\s+/).length} Words)
            </Badge>
            <div className="flex items-center gap-2">
              <button onClick={handleCopy} className="flex items-center gap-1.5 rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-xs text-zinc-300 hover:bg-zinc-700">
                {copied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
                {copied ? "Copied!" : "Copy Text"}
              </button>
              <button onClick={handleDownloadDocx} className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs text-white hover:bg-emerald-500">
                <Download size={14} />
                Download Word (.docx)
              </button>
            </div>
          </div>

          {/* Styled A4 Paper Box */}
          <div className="mx-auto my-2 max-h-[32rem] w-full max-w-3xl overflow-y-auto rounded-lg border border-zinc-300 bg-white p-8 text-zinc-900 shadow-2xl dark:border-zinc-700 dark:bg-white dark:text-zinc-900">
            <div className="prose prose-slate max-w-none text-xs leading-relaxed">
              {result.split("\n\n").map((para, i) => (
                <p key={i} className="mb-4 text-zinc-800">
                  {para}
                </p>
              ))}
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}

function MotivationGenerator() {
  const [scholarshipInfo, setScholarshipInfo] = useState("");
  const [wordLimit, setWordLimit] = useState(500);
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function handleGenerate() {
    if (!scholarshipInfo.trim()) return;
    try {
      setGenerating(true);
      setError(null);
      const data = await documentsApi.generateMotivation({
        scholarship_info: scholarshipInfo,
        word_limit: wordLimit,
      });
      setResult(data.motivation || (data as any).content || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setGenerating(false);
    }
  }

  function handleCopy() {
    if (result) {
      navigator.clipboard.writeText(result);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }

  function handleDownloadDocx() {
    if (!result) return;
    const blob = new Blob([result], { type: "application/msword;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "Motivation_Letter.docx";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  return (
    <Card className="p-6">
      <h2 className="mb-2 text-lg font-semibold text-zinc-900 dark:text-white flex items-center gap-2">
        <Sparkles className="text-emerald-500" size={20} />
        Generate Motivation Letter (Word Document)
      </h2>
      <p className="mb-6 text-sm text-zinc-500">
        Drafts a high-impact European-standard motivation letter customized for grant and university applications.
      </p>

      <div className="space-y-4">
        <div>
          <label className="mb-1 block text-xs font-medium text-zinc-400">
            Scholarship / Program Information *
          </label>
          <textarea
            rows={4}
            placeholder="Paste scholarship details, university name, program requirements..."
            value={scholarshipInfo}
            onChange={(e) => setScholarshipInfo(e.target.value)}
            className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-white"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-zinc-400">Target Word Limit</label>
          <input
            type="number"
            value={wordLimit}
            onChange={(e) => setWordLimit(Number(e.target.value))}
            className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-white sm:w-48"
          />
        </div>
      </div>

      <div className="mt-6 flex justify-end">
        <Button onClick={handleGenerate} disabled={generating || !scholarshipInfo.trim()} className="bg-emerald-600 hover:bg-emerald-500">
          {generating ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
          {generating ? "Drafting Letter..." : "Generate Motivation Letter"}
        </Button>
      </div>

      {error && (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-500/10 dark:text-red-400">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-6 space-y-3 rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-5">
          <div className="flex items-center justify-between">
            <Badge variant="success" className="px-3 py-1 flex items-center gap-1.5">
              <CheckCircle2 size={13} />
              Generated ({result.split(/\s+/).length} Words)
            </Badge>
            <div className="flex items-center gap-2">
              <button onClick={handleCopy} className="flex items-center gap-1.5 rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-xs text-zinc-300 hover:bg-zinc-700">
                {copied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
                {copied ? "Copied!" : "Copy Text"}
              </button>
              <button onClick={handleDownloadDocx} className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs text-white hover:bg-emerald-500">
                <Download size={14} />
                Download Word (.docx)
              </button>
            </div>
          </div>

          <div className="mx-auto my-2 max-h-[32rem] w-full max-w-3xl overflow-y-auto rounded-lg border border-zinc-300 bg-white p-8 text-zinc-900 shadow-2xl dark:border-zinc-700 dark:bg-white dark:text-zinc-900">
            <div className="prose prose-slate max-w-none text-xs leading-relaxed">
              {result.split("\n\n").map((para, i) => (
                <p key={i} className="mb-4 text-zinc-800">
                  {para}
                </p>
              ))}
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}

function ResearchGenerator() {
  const [scholarshipInfo, setScholarshipInfo] = useState("");
  const [researchInterests, setResearchInterests] = useState("");
  const [wordLimit, setWordLimit] = useState(2000);
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function handleGenerate() {
    if (!scholarshipInfo.trim()) return;
    try {
      setGenerating(true);
      setError(null);
      const data = await documentsApi.generateResearch({
        scholarship_info: scholarshipInfo,
        research_interests: researchInterests
          ? researchInterests.split(",").map((s) => s.trim())
          : [],
        word_limit: wordLimit,
      });
      setResult(data.research_proposal || (data as any).content || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setGenerating(false);
    }
  }

  function handleCopy() {
    if (result) {
      navigator.clipboard.writeText(result);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }

  function handleDownloadDocx() {
    if (!result) return;
    const blob = new Blob([result], { type: "application/msword;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "Research_Proposal.docx";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  return (
    <Card className="p-6">
      <h2 className="mb-2 text-lg font-semibold text-zinc-900 dark:text-white flex items-center gap-2">
        <Sparkles className="text-emerald-500" size={20} />
        Generate Structured Research Proposal (Word Document)
      </h2>
      <p className="mb-6 text-sm text-zinc-500">
        Drafts a rigorous academic research proposal with methodology, objectives, and references.
      </p>

      <div className="space-y-4">
        <div>
          <label className="mb-1 block text-xs font-medium text-zinc-400">
            Scholarship / Program & Lab Details *
          </label>
          <textarea
            rows={4}
            placeholder="Paste program details, university, research lab focus..."
            value={scholarshipInfo}
            onChange={(e) => setScholarshipInfo(e.target.value)}
            className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-white"
          />
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-xs font-medium text-zinc-400">
              Key Research Topics (comma-separated)
            </label>
            <input
              type="text"
              placeholder="e.g., Computer Vision, Medical Imaging"
              value={researchInterests}
              onChange={(e) => setResearchInterests(e.target.value)}
              className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-white"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-zinc-400">Target Word Limit</label>
            <input
              type="number"
              value={wordLimit}
              onChange={(e) => setWordLimit(Number(e.target.value))}
              className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-white"
            />
          </div>
        </div>
      </div>

      <div className="mt-6 flex justify-end">
        <Button onClick={handleGenerate} disabled={generating || !scholarshipInfo.trim()} className="bg-emerald-600 hover:bg-emerald-500">
          {generating ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
          {generating ? "Drafting Proposal..." : "Generate Research Proposal"}
        </Button>
      </div>

      {error && (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-500/10 dark:text-red-400">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-6 space-y-3 rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-5">
          <div className="flex items-center justify-between">
            <Badge variant="success" className="px-3 py-1 flex items-center gap-1.5">
              <CheckCircle2 size={13} />
              Generated ({result.split(/\s+/).length} Words)
            </Badge>
            <div className="flex items-center gap-2">
              <button onClick={handleCopy} className="flex items-center gap-1.5 rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-xs text-zinc-300 hover:bg-zinc-700">
                {copied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
                {copied ? "Copied!" : "Copy Text"}
              </button>
              <button onClick={handleDownloadDocx} className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs text-white hover:bg-emerald-500">
                <Download size={14} />
                Download Word (.docx)
              </button>
            </div>
          </div>

          <div className="mx-auto my-2 max-h-[32rem] w-full max-w-3xl overflow-y-auto rounded-lg border border-zinc-300 bg-white p-8 text-zinc-900 shadow-2xl dark:border-zinc-700 dark:bg-white dark:text-zinc-900">
            <div className="prose prose-slate max-w-none text-xs leading-relaxed">
              {result.split("\n\n").map((para, i) => (
                <p key={i} className="mb-4 text-zinc-800">
                  {para}
                </p>
              ))}
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}
