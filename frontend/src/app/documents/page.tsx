"use client";

import { useState } from "react";
import {
  FileText,
  FileUp,
  Sparkles,
  Loader2,
  Copy,
  Check,
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
        title="Document Generator"
        description="Generate ATS-optimized CVs, SOPs, motivation letters, and research proposals"
      />

      {/* Tabs */}
      <div className="mb-6 flex gap-2 overflow-x-auto">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`flex items-center gap-2 whitespace-nowrap rounded-lg px-4 py-2.5 text-sm font-medium transition-colors ${
              activeTab === key
                ? "bg-emerald-600 text-white"
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
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

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
      setResult(`CV generated successfully!\n\nOutput: ${data.cv_path}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <Card className="p-6">
      <h2 className="mb-4 text-lg font-semibold text-zinc-900 dark:text-white">
        Generate Tailored CV
      </h2>
      <p className="mb-4 text-sm text-zinc-500">
        Generate an ATS-optimized CV tailored to a specific job posting
      </p>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label className="mb-1 block text-xs font-medium text-zinc-500">Company *</label>
          <input
            type="text"
            placeholder="e.g., Google"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-zinc-500">Role</label>
          <input
            type="text"
            placeholder="e.g., ML Engineer"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800"
          />
        </div>
      </div>

      <div className="mt-4">
        <label className="mb-1 block text-xs font-medium text-zinc-500">Job URL (optional)</label>
        <input
          type="text"
          placeholder="https://..."
          value={jobUrl}
          onChange={(e) => setJobUrl(e.target.value)}
          className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800"
        />
      </div>

      <div className="mt-4 flex justify-end">
        <Button onClick={handleGenerate} disabled={generating || !company.trim()}>
          {generating ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
          {generating ? "Generating..." : "Generate CV"}
        </Button>
      </div>

      {error && (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-500/10 dark:text-red-400">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700 dark:border-emerald-800 dark:bg-emerald-500/10 dark:text-emerald-400">
          <pre className="whitespace-pre-wrap">{result}</pre>
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
      setResult(data.sop);
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

  return (
    <Card className="p-6">
      <h2 className="mb-4 text-lg font-semibold text-zinc-900 dark:text-white">
        Generate Statement of Purpose
      </h2>
      <p className="mb-4 text-sm text-zinc-500">
        Create a compelling SOP tailored to your target scholarship
      </p>

      <div className="space-y-4">
        <div>
          <label className="mb-1 block text-xs font-medium text-zinc-500">
            Scholarship Information *
          </label>
          <textarea
            rows={4}
            placeholder="Paste scholarship details, requirements, university name, program..."
            value={scholarshipInfo}
            onChange={(e) => setScholarshipInfo(e.target.value)}
            className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800"
          />
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-xs font-medium text-zinc-500">
              Research Interests (comma-separated)
            </label>
            <input
              type="text"
              placeholder="NLP, computer vision, robotics"
              value={researchInterests}
              onChange={(e) => setResearchInterests(e.target.value)}
              className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-zinc-500">Word Limit</label>
            <input
              type="number"
              value={wordLimit}
              onChange={(e) => setWordLimit(Number(e.target.value))}
              className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800"
            />
          </div>
        </div>
      </div>

      <div className="mt-4 flex justify-end">
        <Button onClick={handleGenerate} disabled={generating || !scholarshipInfo.trim()}>
          {generating ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
          {generating ? "Generating..." : "Generate SOP"}
        </Button>
      </div>

      {error && (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-500/10 dark:text-red-400">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-4">
          <div className="flex items-center justify-between">
            <Badge variant="success">Generated — {result.split(/\s+/).length} words</Badge>
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-700"
            >
              {copied ? <Check size={12} /> : <Copy size={12} />}
              {copied ? "Copied!" : "Copy"}
            </button>
          </div>
          <div className="mt-3 max-h-96 overflow-y-auto rounded-lg border border-zinc-200 bg-zinc-50 p-4 text-sm leading-relaxed dark:border-zinc-700 dark:bg-zinc-800/50">
            <pre className="whitespace-pre-wrap font-sans">{result}</pre>
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
      setResult(data.motivation);
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

  return (
    <Card className="p-6">
      <h2 className="mb-4 text-lg font-semibold text-zinc-900 dark:text-white">
        Generate Motivation Letter
      </h2>
      <p className="mb-4 text-sm text-zinc-500">
        European-style motivation letter for scholarship applications
      </p>

      <div className="space-y-4">
        <div>
          <label className="mb-1 block text-xs font-medium text-zinc-500">
            Scholarship Information *
          </label>
          <textarea
            rows={4}
            placeholder="Paste scholarship details, university, program requirements..."
            value={scholarshipInfo}
            onChange={(e) => setScholarshipInfo(e.target.value)}
            className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-zinc-500">Word Limit</label>
          <input
            type="number"
            value={wordLimit}
            onChange={(e) => setWordLimit(Number(e.target.value))}
            className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800 sm:w-48"
          />
        </div>
      </div>

      <div className="mt-4 flex justify-end">
        <Button onClick={handleGenerate} disabled={generating || !scholarshipInfo.trim()}>
          {generating ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
          {generating ? "Generating..." : "Generate Letter"}
        </Button>
      </div>

      {error && (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-500/10 dark:text-red-400">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-4">
          <div className="flex items-center justify-between">
            <Badge variant="success">Generated — {result.split(/\s+/).length} words</Badge>
            <button onClick={handleCopy} className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-700">
              {copied ? <Check size={12} /> : <Copy size={12} />}
              {copied ? "Copied!" : "Copy"}
            </button>
          </div>
          <div className="mt-3 max-h-96 overflow-y-auto rounded-lg border border-zinc-200 bg-zinc-50 p-4 text-sm leading-relaxed dark:border-zinc-700 dark:bg-zinc-800/50">
            <pre className="whitespace-pre-wrap font-sans">{result}</pre>
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
      setResult(data.research_proposal);
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

  return (
    <Card className="p-6">
      <h2 className="mb-4 text-lg font-semibold text-zinc-900 dark:text-white">
        Generate Research Proposal
      </h2>
      <p className="mb-4 text-sm text-zinc-500">
        Structured research proposal for PhD and postdoc applications
      </p>

      <div className="space-y-4">
        <div>
          <label className="mb-1 block text-xs font-medium text-zinc-500">
            Scholarship / Program Information *
          </label>
          <textarea
            rows={4}
            placeholder="Paste program details, university, research group, requirements..."
            value={scholarshipInfo}
            onChange={(e) => setScholarshipInfo(e.target.value)}
            className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800"
          />
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-xs font-medium text-zinc-500">
              Research Interests (comma-separated)
            </label>
            <input
              type="text"
              placeholder="NLP, computer vision, robotics"
              value={researchInterests}
              onChange={(e) => setResearchInterests(e.target.value)}
              className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-zinc-500">Word Limit</label>
            <input
              type="number"
              value={wordLimit}
              onChange={(e) => setWordLimit(Number(e.target.value))}
              className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800"
            />
          </div>
        </div>
      </div>

      <div className="mt-4 flex justify-end">
        <Button onClick={handleGenerate} disabled={generating || !scholarshipInfo.trim()}>
          {generating ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
          {generating ? "Generating..." : "Generate Proposal"}
        </Button>
      </div>

      {error && (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-500/10 dark:text-red-400">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-4">
          <div className="flex items-center justify-between">
            <Badge variant="success">Generated — {result.split(/\s+/).length} words</Badge>
            <button onClick={handleCopy} className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-700">
              {copied ? <Check size={12} /> : <Copy size={12} />}
              {copied ? "Copied!" : "Copy"}
            </button>
          </div>
          <div className="mt-3 max-h-[32rem] overflow-y-auto rounded-lg border border-zinc-200 bg-zinc-50 p-4 text-sm leading-relaxed dark:border-zinc-700 dark:bg-zinc-800/50">
            <pre className="whitespace-pre-wrap font-sans">{result}</pre>
          </div>
        </div>
      )}
    </Card>
  );
}
