"use client";

import { useState } from "react";
import {
  TrendingUp,
  Target,
  Map,
  BookOpen,
  Loader2,
  Sparkles,
  ChevronRight,
} from "lucide-react";
import { PageHeader, Card, Button, Badge, EmptyState } from "@/components/ui";
import { upskillApi, type SkillGap, type RoadmapPhase } from "@/lib/api";

type Tab = "gaps" | "roadmap" | "resources";

export default function UpskillPage() {
  const [activeTab, setActiveTab] = useState<Tab>("gaps");

  const tabs: { key: Tab; label: string; icon: React.ElementType }[] = [
    { key: "gaps", label: "Skill Gap Analysis", icon: Target },
    { key: "roadmap", label: "Career Roadmap", icon: Map },
    { key: "resources", label: "Learning Resources", icon: BookOpen },
  ];

  return (
    <div>
      <PageHeader
        title="Upskill"
        description="Analyze skill gaps, build career roadmaps, and find learning resources"
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

      {activeTab === "gaps" && <GapAnalysis />}
      {activeTab === "roadmap" && <RoadmapBuilder />}
      {activeTab === "resources" && <ResourceFinder />}
    </div>
  );
}

function GapAnalysis() {
  const [jobText, setJobText] = useState("");
  const [jobUrl, setJobUrl] = useState("");
  const [mode, setMode] = useState("aggregate");
  const [analyzing, setAnalyzing] = useState(false);
  const [gaps, setGaps] = useState<SkillGap[]>([]);
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function handleAnalyze() {
    try {
      setAnalyzing(true);
      setError(null);
      const data = await upskillApi.analyze({
        job_url: jobUrl || undefined,
        job_text: jobText || undefined,
        mode,
      });
      setGaps(data.gaps || []);
      setRecommendations(data.recommendations || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setAnalyzing(false);
    }
  }

  const priorityColor: Record<string, "danger" | "warning" | "info"> = {
    high: "danger",
    medium: "warning",
    low: "info",
  };

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <h2 className="mb-4 text-lg font-semibold text-zinc-900 dark:text-white">
          Analyze Skill Gaps
        </h2>
        <p className="mb-4 text-sm text-zinc-500">
          Compare your profile against job requirements to identify skills to develop
        </p>

        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-medium text-zinc-500">Job URL</label>
              <input
                type="text"
                placeholder="https://..."
                value={jobUrl}
                onChange={(e) => setJobUrl(e.target.value)}
                className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-zinc-500">Mode</label>
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value)}
                className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800"
              >
                <option value="aggregate">Aggregate (all job postings)</option>
                <option value="targeted">Targeted (specific posting)</option>
              </select>
            </div>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-zinc-500">
              Or paste job description
            </label>
            <textarea
              rows={3}
              placeholder="Paste job description text..."
              value={jobText}
              onChange={(e) => setJobText(e.target.value)}
              className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800"
            />
          </div>
        </div>

        <div className="mt-4 flex justify-end">
          <Button onClick={handleAnalyze} disabled={analyzing}>
            {analyzing ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
            {analyzing ? "Analyzing..." : "Analyze Gaps"}
          </Button>
        </div>

        {error && (
          <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-500/10 dark:text-red-400">
            {error}
          </div>
        )}
      </Card>

      {/* Results */}
      {gaps.length > 0 && (
        <Card className="p-6">
          <h3 className="mb-4 text-lg font-semibold text-zinc-900 dark:text-white">
            Skill Gaps ({gaps.length})
          </h3>
          <div className="space-y-3">
            {gaps.map((gap, i) => (
              <div
                key={i}
                className="flex items-center justify-between rounded-lg border border-zinc-100 p-4 dark:border-zinc-800"
              >
                <div className="flex items-center gap-3">
                  <Target size={16} className="text-zinc-400" />
                  <div>
                    <p className="text-sm font-medium text-zinc-900 dark:text-white">
                      {gap.skill}
                    </p>
                    <p className="text-xs text-zinc-500">
                      {gap.category} · {gap.frequency} posting{gap.frequency !== 1 ? "s" : ""}
                      {gap.estimated_hours ? ` · ~${gap.estimated_hours}h to learn` : ""}
                    </p>
                    {gap.study_direction && (
                      <p className="mt-1 text-xs text-zinc-400">{gap.study_direction}</p>
                    )}
                  </div>
                </div>
                <Badge variant={priorityColor[gap.priority] || "default"}>
                  {gap.priority}
                </Badge>
              </div>
            ))}
          </div>

          {recommendations.length > 0 && (
            <div className="mt-6">
              <h4 className="mb-2 text-sm font-semibold text-zinc-900 dark:text-white">
                Recommendations
              </h4>
              <ul className="space-y-2">
                {recommendations.map((rec, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-zinc-600 dark:text-zinc-400">
                    <ChevronRight size={14} className="mt-0.5 shrink-0 text-emerald-500" />
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </Card>
      )}

      {gaps.length === 0 && !analyzing && (
        <EmptyState
          icon={Target}
          title="No skill gaps analyzed yet"
          description="Paste a job description or URL to identify skills you should develop"
        />
      )}
    </div>
  );
}

function RoadmapBuilder() {
  const [timeline, setTimeline] = useState(12);
  const [targetRoles, setTargetRoles] = useState("");
  const [building, setBuilding] = useState(false);
  const [phases, setPhases] = useState<RoadmapPhase[]>([]);
  const [summary, setSummary] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleBuild() {
    try {
      setBuilding(true);
      setError(null);
      const data = await upskillApi.roadmap({
        timeline_months: timeline,
        target_roles: targetRoles ? targetRoles.split(",").map((s) => s.trim()) : [],
      });
      setPhases(data.roadmap || []);
      setSummary(data.summary || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to build roadmap");
    } finally {
      setBuilding(false);
    }
  }

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <h2 className="mb-4 text-lg font-semibold text-zinc-900 dark:text-white">
          Build Career Roadmap
        </h2>
        <p className="mb-4 text-sm text-zinc-500">
          Generate a personalized career development plan with milestones
        </p>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-1 block text-xs font-medium text-zinc-500">Timeline (months)</label>
            <input
              type="number"
              value={timeline}
              onChange={(e) => setTimeline(Number(e.target.value))}
              min={3}
              max={36}
              className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-zinc-500">
              Target Roles (comma-separated)
            </label>
            <input
              type="text"
              placeholder="ML Engineer, Data Scientist"
              value={targetRoles}
              onChange={(e) => setTargetRoles(e.target.value)}
              className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800"
            />
          </div>
        </div>

        <div className="mt-4 flex justify-end">
          <Button onClick={handleBuild} disabled={building}>
            {building ? <Loader2 size={16} className="animate-spin" /> : <Map size={16} />}
            {building ? "Building..." : "Build Roadmap"}
          </Button>
        </div>

        {error && (
          <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-500/10 dark:text-red-400">
            {error}
          </div>
        )}
      </Card>

      {summary && (
        <Card className="p-6">
          <p className="text-sm text-zinc-600 dark:text-zinc-400">{summary}</p>
        </Card>
      )}

      {phases.length > 0 && (
        <div className="space-y-4">
          {phases.map((phase, i) => (
            <Card key={i} className="p-6">
              <div className="mb-4 flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-100 text-sm font-bold text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400">
                  {i + 1}
                </div>
                <div>
                  <h3 className="font-semibold text-zinc-900 dark:text-white">
                    {phase.phase}
                  </h3>
                  <p className="text-xs text-zinc-500">{phase.duration}</p>
                </div>
              </div>
              <div className="space-y-3 pl-11">
                {phase.milestones.map((m, j) => (
                  <div key={j} className="flex items-start gap-3">
                    <div
                      className={`mt-1 h-2 w-2 shrink-0 rounded-full ${
                        m.type === "learning"
                          ? "bg-blue-400"
                          : m.type === "certification"
                          ? "bg-amber-400"
                          : m.type === "project"
                          ? "bg-emerald-400"
                          : m.type === "application"
                          ? "bg-purple-400"
                          : "bg-zinc-400"
                      }`}
                    />
                    <div>
                      <p className="text-sm font-medium text-zinc-900 dark:text-white">
                        {m.title}
                      </p>
                      <p className="text-xs text-zinc-500">{m.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          ))}
        </div>
      )}

      {phases.length === 0 && !building && (
        <EmptyState
          icon={Map}
          title="No roadmap built yet"
          description="Set your timeline and target roles to generate a personalized career development plan"
        />
      )}
    </div>
  );
}

function ResourceFinder() {
  const [skills, setSkills] = useState("");
  const [format, setFormat] = useState("");
  const [finding, setFinding] = useState(false);
  const [resources, setResources] = useState<Record<string, unknown>[]>([]);
  const [studyOrder, setStudyOrder] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function handleFind() {
    if (!skills.trim()) return;
    try {
      setFinding(true);
      setError(null);
      const data = await upskillApi.resources({
        skills: skills.split(",").map((s) => s.trim()),
        format: format || undefined,
      });
      setResources(data.resources || []);
      setStudyOrder(data.study_order || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to find resources");
    } finally {
      setFinding(false);
    }
  }

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <h2 className="mb-4 text-lg font-semibold text-zinc-900 dark:text-white">
          Find Learning Resources
        </h2>
        <p className="mb-4 text-sm text-zinc-500">
          Discover curated courses, tutorials, and materials for your target skills
        </p>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="sm:col-span-2">
            <label className="mb-1 block text-xs font-medium text-zinc-500">
              Skills (comma-separated) *
            </label>
            <input
              type="text"
              placeholder="Python, machine learning, Docker"
              value={skills}
              onChange={(e) => setSkills(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleFind()}
              className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-zinc-500">Format</label>
            <select
              value={format}
              onChange={(e) => setFormat(e.target.value)}
              className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800"
            >
              <option value="">All formats</option>
              <option value="course">Courses</option>
              <option value="book">Books</option>
              <option value="tutorial">Tutorials</option>
              <option value="documentation">Documentation</option>
              <option value="video">Videos</option>
            </select>
          </div>
        </div>

        <div className="mt-4 flex justify-end">
          <Button onClick={handleFind} disabled={finding || !skills.trim()}>
            {finding ? <Loader2 size={16} className="animate-spin" /> : <BookOpen size={16} />}
            {finding ? "Finding..." : "Find Resources"}
          </Button>
        </div>

        {error && (
          <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-500/10 dark:text-red-400">
            {error}
          </div>
        )}
      </Card>

      {studyOrder.length > 0 && (
        <Card className="p-6">
          <h3 className="mb-3 text-sm font-semibold text-zinc-900 dark:text-white">
            Recommended Study Order
          </h3>
          <div className="flex flex-wrap gap-2">
            {studyOrder.map((skill, i) => (
              <div key={i} className="flex items-center gap-2">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-100 text-xs font-bold text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400">
                  {i + 1}
                </span>
                <span className="text-sm text-zinc-700 dark:text-zinc-300">{skill}</span>
                {i < studyOrder.length - 1 && (
                  <ChevronRight size={14} className="text-zinc-300" />
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      {resources.length > 0 && (
        <div className="space-y-3">
          {resources.map((res, i) => (
            <Card key={i} className="p-5">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-medium text-zinc-900 dark:text-white">
                    {String(res.title || res.name || "")}
                  </h3>
                  <p className="text-sm text-zinc-500">
                    {String(res.skill || "")} · {String(res.format || "")} · {String(res.provider || "")}
                  </p>
                  {res.description != null && String(res.description).length > 0 && (
                    <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
                      {String(res.description)}
                    </p>
                  )}
                </div>
                {res.url != null && String(res.url).length > 0 && (
                  <a
                    href={String(res.url)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="shrink-0 text-sm text-emerald-600 hover:underline"
                  >
                    Open →
                  </a>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {resources.length === 0 && !finding && (
        <EmptyState
          icon={BookOpen}
          title="No resources found yet"
          description="Enter skills you want to learn and discover curated learning materials"
        />
      )}
    </div>
  );
}
