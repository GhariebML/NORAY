"use client";

import { useState, useCallback } from "react";
import {
  Search, Briefcase, MapPin, Globe,
  ExternalLink, FileText, Mail, Bookmark,
  TrendingUp,
  Loader2, Sparkles,
} from "lucide-react";
import { PageHeader, Card, Badge, Button } from "@/components/ui";
import { jobsApi, type AIJobResult, type AIJobScore } from "@/lib/api";

type SortKey = "match" | "newest" | "salary";

export default function JobsPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<AIJobResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [searchTime, setSearchTime] = useState(0);
  const [parsedIntent, setParsedIntent] = useState<any>(null);

  const [sortBy, setSortBy] = useState<SortKey>("match");
  const [filterRemote, setFilterRemote] = useState(false);
  const [filterCountry] = useState("");
  const [filterMinScore, setFilterMinScore] = useState(0);

  const fetchResults = useCallback(async () => {
    if (!query.trim()) return;
    setLoading(true);
    setSearched(true);
    try {
      const data = await jobsApi.aiSearch({ query, max_results: 40 });
      setResults(data.jobs || []);
      setParsedIntent(data.parsed_intent);
      setSearchTime(data.search_time_seconds);
    } catch (err: any) {
      console.error("AI job search failed", err);
    } finally {
      setLoading(false);
    }
  }, [query]);

  const filtered = results
    .filter((j) => !filterRemote || j.remote)
    .filter((j) => !filterCountry || j.country.toLowerCase().includes(filterCountry.toLowerCase()))
    .filter((j) => (j.score?.overall_match || 0) >= filterMinScore)
    .sort((a, b) => {
      if (sortBy === "match") return (b.score?.overall_match || 0) - (a.score?.overall_match || 0);
      return 0;
    });

  return (
    <div className="flex flex-col h-full select-none">
      <PageHeader
        title="AI Job Search Engine"
        description="Natural language job discovery with AI scoring and multi-provider search"
      />

      {/* AI Search Bar */}
      <div className="mb-6">
        <div className="flex items-center gap-2">
          <div className="flex-1 relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && fetchResults()}
              placeholder='e.g. "Machine Learning Engineer in Germany" or "Remote AI jobs using Python"'
              className="w-full rounded-xl border border-zinc-800 bg-zinc-900/60 pl-9 pr-4 py-3 text-sm text-zinc-200 placeholder-zinc-500 focus:border-emerald-500 focus:outline-none"
            />
          </div>
          <Button onClick={fetchResults} disabled={loading || !query.trim()} variant="primary" className="h-11">
            {loading ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
            {loading ? "Searching..." : "AI Search"}
          </Button>
        </div>

        {parsedIntent && (
          <div className="mt-2 flex flex-wrap gap-1.5 text-[10px] text-zinc-500">
            <Badge variant="info">Role: {parsedIntent.role}</Badge>
            {parsedIntent.country && <Badge variant="info">Country: {parsedIntent.country}</Badge>}
            {parsedIntent.remote && <Badge variant="success">Remote</Badge>}
            <Badge variant="info">Level: {parsedIntent.experience_level}</Badge>
            {parsedIntent.skills?.slice(0, 3).map((s: string) => (
              <Badge key={s} variant="outline">{s}</Badge>
            ))}
          </div>
        )}
      </div>

      {/* Results Summary */}
      {searched && !loading && (
        <div className="flex items-center justify-between mb-4 text-[11px] text-zinc-400">
          <span>
            Found <strong className="text-zinc-200">{filtered.length}</strong> AI-scored jobs
            {searchTime > 0 && ` in ${searchTime}s`}
          </span>
          <div className="flex items-center gap-3">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortKey)}
              className="bg-zinc-900 border border-zinc-800 rounded px-2 py-1 text-[10px] text-zinc-300"
            >
              <option value="match">Sort: AI Match</option>
              <option value="newest">Sort: Newest</option>
            </select>
            <label className="flex items-center gap-1.5">
              <input type="checkbox" checked={filterRemote} onChange={(e) => setFilterRemote(e.target.checked)} className="accent-emerald-500" />
              <span>Remote only</span>
            </label>
            <input
              type="number"
              placeholder="Min match %"
              value={filterMinScore}
              onChange={(e) => setFilterMinScore(Number(e.target.value))}
              className="w-20 bg-zinc-900 border border-zinc-800 rounded px-2 py-1 text-[10px] text-zinc-300"
              min={0} max={100}
            />
          </div>
        </div>
      )}

      {/* Results Grid */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-1">
        {loading && (
          <div className="flex items-center justify-center py-16 text-zinc-500">
            <Loader2 size={20} className="animate-spin mr-3" />
            <span>Analyzing intent, searching providers, AI-scoring results...</span>
          </div>
        )}

        {!loading && searched && filtered.length === 0 && (
          <div className="text-center py-16 text-zinc-500">
            <Search size={32} className="mx-auto mb-3 opacity-30" />
            <p className="text-sm">No jobs found matching your criteria.</p>
            <p className="text-[11px] mt-1">Try a different search or adjust filters.</p>
          </div>
        )}

        {!loading && filtered.map((job, idx) => {
          const score = job.score || {} as AIJobScore;
          const matchColor = score.overall_match >= 80 ? "text-emerald-400" : score.overall_match >= 50 ? "text-amber-400" : "text-red-400";
          const matchBg = score.overall_match >= 80 ? "bg-emerald-950/20 border-emerald-500/20" : score.overall_match >= 50 ? "bg-amber-950/20 border-amber-500/20" : "bg-red-950/20 border-red-500/20";
          const recBadge = score.recommendation === "strong apply" ? "success" : score.recommendation === "consider" ? "warning" : "danger";

          return (
            <Card key={`${job.source}-${idx}`} className="p-4 hover:bg-zinc-800/30 transition-colors">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-sm font-semibold text-white truncate">{job.role}</h3>
                    <Badge variant={recBadge as any} className="text-[9px] uppercase">
                      {score.recommendation}
                    </Badge>
                  </div>
                  <p className="text-xs text-zinc-400 mb-2">{job.company}</p>

                  <div className="flex flex-wrap gap-3 text-[10px] text-zinc-500 mb-2">
                    {job.country && <span className="flex items-center gap-1"><MapPin size={10} />{job.country}</span>}
                    {job.remote && <span className="flex items-center gap-1 text-emerald-400"><Globe size={10} />Remote</span>}
                    <span className="flex items-center gap-1"><Briefcase size={10} />{job.source}</span>
                  </div>

                  <p className="text-[10px] text-zinc-500 line-clamp-2 mb-2">{job.description}</p>

                  {score.strengths && score.strengths.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-1">
                      {score.strengths.slice(0, 3).map((s, i) => (
                        <span key={i} className="px-1.5 py-0.5 rounded bg-emerald-950/20 text-emerald-400 text-[9px]">{s}</span>
                      ))}
                    </div>
                  )}

                  {score.gaps && score.gaps.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {score.gaps.slice(0, 2).map((g, i) => (
                        <span key={i} className="px-1.5 py-0.5 rounded bg-amber-950/20 text-amber-400 text-[9px]">{g}</span>
                      ))}
                    </div>
                  )}
                </div>

                {/* AI Match Score */}
                <div className={`flex flex-col items-center p-3 rounded-lg border min-w-[72px] ${matchBg}`}>
                  <span className={`text-lg font-bold font-heading ${matchColor}`}>{score.overall_match || "?"}</span>
                  <span className="text-[9px] text-zinc-500">Match %</span>
                  {score.ats_estimate > 0 && (
                    <span className="text-[8px] text-zinc-600 mt-1">ATS: {score.ats_estimate}%</span>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 mt-3 pt-3 border-t border-zinc-800/60">
                {job.apply_url && (
                  <a href={job.apply_url} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-600 text-zinc-950 text-[10px] font-bold hover:bg-emerald-500 transition-colors">
                    <ExternalLink size={10} /> Apply
                  </a>
                )}
                <button
                  onClick={() => jobsApi.aiScore({ company: job.company, role: job.role, country: job.country, description: job.description })}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-zinc-800 text-zinc-400 text-[10px] hover:text-white transition-colors"
                >
                  <TrendingUp size={10} /> AI Analysis
                </button>
                <button
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-zinc-800 text-zinc-400 text-[10px] hover:text-white transition-colors"
                >
                  <FileText size={10} /> Generate CV
                </button>
                <button
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-zinc-800 text-zinc-400 text-[10px] hover:text-white transition-colors"
                >
                  <Mail size={10} /> Cover Letter
                </button>
                <button className="ml-auto text-zinc-600 hover:text-zinc-300">
                  <Bookmark size={13} />
                </button>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
