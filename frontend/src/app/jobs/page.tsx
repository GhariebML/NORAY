"use client";

import { useState } from "react";
import {
  Search,
  Briefcase,
  ExternalLink,
  Star,
  AlertTriangle,
  Loader2,
  Send,
} from "lucide-react";
import { PageHeader, Card, Button, Badge, EmptyState } from "@/components/ui";
import { jobsApi, type Job } from "@/lib/api";

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [searching, setSearching] = useState(false);
  const [focusArea, setFocusArea] = useState("");
  const [broad, setBroad] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);
  const [applying, setApplying] = useState<string | null>(null);

  async function handleSearch() {
    try {
      setSearching(true);
      setError(null);
      const data = await jobsApi.search({ focus_area: focusArea, broad });
      setJobs(data.jobs || []);
      setSearched(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setSearching(false);
    }
  }

  async function handleApply(job: Job) {
    try {
      setApplying(job.url || job.title);
      await jobsApi.apply({
        job_url: job.url,
        company: job.company,
        role: job.title,
        generate_cv: true,
        generate_cover_letter: true,
      });
      alert("Application materials generated! Check the Documents page.");
    } catch (err) {
      alert("Failed to generate application materials");
    } finally {
      setApplying(null);
    }
  }

  return (
    <div>
      <PageHeader
        title="Job Search"
        description="Discover and evaluate job opportunities with AI-powered fit scoring"
      />

      {/* Search Bar */}
      <Card className="mb-6 p-6">
        <div className="flex flex-col gap-4 sm:flex-row">
          <div className="relative flex-1">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
            <input
              type="text"
              placeholder="Focus area (e.g., data science, ML engineer, Python developer)"
              value={focusArea}
              onChange={(e) => setFocusArea(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              className="w-full rounded-lg border border-zinc-300 bg-white py-2.5 pl-10 pr-4 text-sm dark:border-zinc-700 dark:bg-zinc-800"
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-zinc-600 dark:text-zinc-400">
            <input
              type="checkbox"
              checked={broad}
              onChange={(e) => setBroad(e.target.checked)}
              className="rounded border-zinc-300"
            />
            Broad search
          </label>
          <Button onClick={handleSearch} disabled={searching}>
            {searching ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Search size={16} />
            )}
            {searching ? "Searching..." : "Search Jobs"}
          </Button>
        </div>
      </Card>

      {error && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-500/10 dark:text-red-400">
          {error}
        </div>
      )}

      {/* Results */}
      {!searched ? (
        <EmptyState
          icon={Briefcase}
          title="Search for jobs"
          description="Enter a focus area and click search to discover job opportunities tailored to your profile"
        />
      ) : jobs.length === 0 ? (
        <EmptyState
          icon={Briefcase}
          title="No jobs found"
          description="Try broadening your search or using different keywords"
        />
      ) : (
        <>
          <p className="mb-4 text-sm text-zinc-500">
            Found {jobs.length} jobs — sorted by fit score
          </p>
          <div className="space-y-4">
            {jobs.map((job, i) => (
              <Card key={i} className="p-5">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                  <div className="flex-1">
                    <div className="flex items-start gap-3">
                      <div className="rounded-lg bg-blue-50 p-2 dark:bg-blue-500/10">
                        <Briefcase size={18} className="text-blue-600 dark:text-blue-400" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-zinc-900 dark:text-white">
                          {job.title}
                        </h3>
                        <p className="text-sm text-zinc-500">
                          {job.company}
                          {job.location ? ` · ${job.location}` : ""}
                          {job.source ? ` · ${job.source}` : ""}
                        </p>
                      </div>
                    </div>

                    {/* Match Reasons */}
                    {job.match_reasons && job.match_reasons.length > 0 && (
                      <div className="mt-3">
                        <p className="mb-1 text-xs font-medium uppercase tracking-wider text-zinc-500">
                          Why it matches
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {job.match_reasons.map((reason, j) => (
                            <Badge key={j} variant="success">
                              {reason}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Missing Skills */}
                    {job.missing_skills && job.missing_skills.length > 0 && (
                      <div className="mt-2">
                        <p className="mb-1 text-xs font-medium uppercase tracking-wider text-zinc-500">
                          Skills to develop
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {job.missing_skills.map((skill, j) => (
                            <Badge key={j} variant="warning">
                              <AlertTriangle size={10} className="mr-1" />
                              {skill}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Right side: Score + Actions */}
                  <div className="flex flex-col items-end gap-3">
                    {job.fit_score !== undefined && (
                      <FitScore score={job.fit_score} />
                    )}
                    <div className="flex gap-2">
                      {job.url && (
                        <a
                          href={job.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-200 px-3 py-1.5 text-xs font-medium text-zinc-600 transition-colors hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-400 dark:hover:bg-zinc-800"
                        >
                          <ExternalLink size={12} />
                          View
                        </a>
                      )}
                      <Button
                        onClick={() => handleApply(job)}
                        disabled={applying === (job.url || job.title)}
                        className="px-3 py-1.5 text-xs"
                      >
                        {applying === (job.url || job.title) ? (
                          <Loader2 size={12} className="animate-spin" />
                        ) : (
                          <Send size={12} />
                        )}
                        Apply
                      </Button>
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function FitScore({ score }: { score: number }) {
  const color =
    score >= 80
      ? "text-emerald-600 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-500/10"
      : score >= 60
      ? "text-amber-600 bg-amber-50 dark:text-amber-400 dark:bg-amber-500/10"
      : "text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-500/10";

  return (
    <div className={`flex items-center gap-1.5 rounded-lg px-3 py-2 ${color}`}>
      <Star size={14} />
      <span className="text-lg font-bold">{score}</span>
      <span className="text-xs opacity-70">fit</span>
    </div>
  );
}
