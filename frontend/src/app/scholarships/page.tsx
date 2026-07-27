"use client";

import { useState, useCallback } from "react";
import {
  Search, GraduationCap, Globe, DollarSign, Calendar,
  ExternalLink, FileText, Mail, Bookmark, CheckCircle2,
  AlertTriangle, Loader2, Sparkles, Award, Clock,
} from "lucide-react";
import { PageHeader, Card, Badge, Button } from "@/components/ui";
import { scholarshipsApi, type AIScholarshipResult, type AIScholarshipEligibility } from "@/lib/api";

export default function ScholarshipsPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<AIScholarshipResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [parsedIntent, setParsedIntent] = useState<any>(null);

  const [filterCountry, setFilterCountry] = useState("");
  const [filterMinScore, setFilterMinScore] = useState(0);
  const [expandedScholarship, setExpandedScholarship] = useState<string | null>(null);

  const fetchResults = useCallback(async () => {
    if (!query.trim()) return;
    setLoading(true);
    setSearched(true);
    try {
      const data = await scholarshipsApi.aiSearch({ query });
      setResults(data.scholarships || []);
      setParsedIntent(data.parsed_intent);
    } catch (err: any) {
      console.error("AI scholarship search failed", err);
    } finally {
      setLoading(false);
    }
  }, [query]);

  const filtered = results
    .filter((s) => !filterCountry || s.country.toLowerCase().includes(filterCountry.toLowerCase()))
    .filter((s) => (s.eligibility?.eligibility_score || 0) >= filterMinScore);

  function getCompetitionColor(level: string): string {
    if (level === "low") return "text-emerald-400";
    if (level === "medium") return "text-amber-400";
    if (level === "high") return "text-orange-400";
    return "text-red-400";
  }

  return (
    <div className="flex flex-col h-full select-none">
      <PageHeader
        title="AI Scholarship Discovery Engine"
        description="Natural language scholarship search with AI eligibility analysis"
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
              placeholder='e.g. "PhD AI Germany" or "Masters scholarship in Europe"'
              className="w-full rounded-xl border border-zinc-800 bg-zinc-900/60 pl-9 pr-4 py-3 text-sm text-zinc-200 placeholder-zinc-500 focus:border-emerald-500 focus:outline-none"
            />
          </div>
          <Button onClick={fetchResults} disabled={loading || !query.trim()} variant="primary" className="h-11">
            {loading ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
            {loading ? "Analyzing..." : "AI Search"}
          </Button>
        </div>

        {parsedIntent && (
          <div className="mt-2 flex flex-wrap gap-1.5 text-[10px] text-zinc-500">
            <Badge variant="info">Degree: {parsedIntent.degree_level}</Badge>
            {parsedIntent.country && <Badge variant="info">Country: {parsedIntent.country}</Badge>}
            {parsedIntent.research_area && <Badge variant="info">Field: {parsedIntent.research_area}</Badge>}
            {parsedIntent.funding_type && <Badge variant="info">Funding: {parsedIntent.funding_type}</Badge>}
          </div>
        )}
      </div>

      {/* Filters */}
      {searched && !loading && (
        <div className="flex items-center justify-between mb-4 text-[11px] text-zinc-400">
          <span>
            Found <strong className="text-zinc-200">{filtered.length}</strong> scholarships with AI analysis
          </span>
          <div className="flex items-center gap-3">
            <input
              type="text"
              placeholder="Filter country..."
              value={filterCountry}
              onChange={(e) => setFilterCountry(e.target.value)}
              className="w-28 bg-zinc-900 border border-zinc-800 rounded px-2 py-1 text-[10px] text-zinc-300"
            />
            <input
              type="number"
              placeholder="Min eligibility %"
              value={filterMinScore}
              onChange={(e) => setFilterMinScore(Number(e.target.value))}
              className="w-24 bg-zinc-900 border border-zinc-800 rounded px-2 py-1 text-[10px] text-zinc-300"
              min={0} max={100}
            />
          </div>
        </div>
      )}

      {/* Results */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-1">
        {loading && (
          <div className="flex items-center justify-center py-16 text-zinc-500">
            <Loader2 size={20} className="animate-spin mr-3" />
            <span>Analyzing intent, searching scholarships, scoring eligibility...</span>
          </div>
        )}

        {!loading && searched && filtered.length === 0 && (
          <div className="text-center py-16 text-zinc-500">
            <GraduationCap size={32} className="mx-auto mb-3 opacity-30" />
            <p className="text-sm">No scholarships found matching your criteria.</p>
          </div>
        )}

        {!loading && filtered.map((sch, idx) => {
          const elig = sch.eligibility || {} as AIScholarshipEligibility;
          const isExpanded = expandedScholarship === sch.name;

          return (
            <Card key={`${sch.name}-${idx}`} className="p-4 hover:bg-zinc-800/30 transition-colors">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-sm font-semibold text-white">{sch.name}</h3>
                    {elig.recommendation && (
                      <Badge variant={elig.recommendation === "strongly_recommend" ? "success" : "warning"} className="text-[9px] uppercase">
                        {elig.recommendation.replace("_", " ")}
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-zinc-400 mb-2">{sch.provider}</p>

                  <div className="flex flex-wrap gap-3 text-[10px] text-zinc-500 mb-2">
                    <span className="flex items-center gap-1"><Globe size={10} />{sch.country}</span>
                    <span className="flex items-center gap-1"><GraduationCap size={10} />{sch.degree_level}</span>
                    <span className="flex items-center gap-1"><DollarSign size={10} />{sch.funding}</span>
                    {sch.deadline && <span className="flex items-center gap-1"><Calendar size={10} />{sch.deadline}</span>}
                  </div>

                  {/* Eligibility Analysis */}
                  <div className="flex flex-wrap gap-1 mb-1">
                    {elig.why_eligible?.slice(0, 2).map((r: string, i: number) => (
                      <span key={i} className="px-1.5 py-0.5 rounded bg-emerald-950/20 text-emerald-400 text-[9px] flex items-center gap-1">
                        <CheckCircle2 size={8} />{r}
                      </span>
                    ))}
                    {elig.missing_documents?.slice(0, 2).map((d: string, i: number) => (
                      <span key={i} className="px-1.5 py-0.5 rounded bg-amber-950/20 text-amber-400 text-[9px] flex items-center gap-1">
                        <AlertTriangle size={8} />{d}
                      </span>
                    ))}
                  </div>

                  {isExpanded && (
                    <div className="mt-3 p-3 rounded-lg bg-zinc-900/50 border border-zinc-800 text-[10px] space-y-2">
                      {elig.summary && <p className="text-zinc-300">{elig.summary}</p>}
                      {elig.recommended_timeline && (
                        <div className="flex items-center gap-1 text-cyan-400">
                          <Clock size={10} /> Timeline: {elig.recommended_timeline}
                        </div>
                      )}
                      {elig.missing_documents && elig.missing_documents.length > 0 && (
                        <div>
                          <span className="text-zinc-500">Missing documents: </span>
                          <span className="text-amber-400">{elig.missing_documents.join(", ")}</span>
                        </div>
                      )}
                      {elig.competition_level && (
                        <div>
                          <span className="text-zinc-500">Competition: </span>
                          <span className={getCompetitionColor(elig.competition_level)}>{elig.competition_level}</span>
                          <span className="text-zinc-500 ml-2">Difficulty: </span>
                          <span className={getCompetitionColor(elig.acceptance_difficulty)}>{elig.acceptance_difficulty}</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Eligibility Score */}
                <div className={`flex flex-col items-center p-3 rounded-lg border min-w-[72px] ${
                  elig.eligibility_score >= 70 ? "bg-emerald-950/20 border-emerald-500/20" :
                  elig.eligibility_score >= 40 ? "bg-amber-950/20 border-amber-500/20" :
                  "bg-red-950/20 border-red-500/20"
                }`}>
                  <span className={`text-lg font-bold font-heading ${
                    elig.eligibility_score >= 70 ? "text-emerald-400" :
                    elig.eligibility_score >= 40 ? "text-amber-400" : "text-red-400"
                  }`}>{elig.eligibility_score || "?"}</span>
                  <span className="text-[9px] text-zinc-500">Eligibility</span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 mt-3 pt-3 border-t border-zinc-800/60">
                {sch.official_url && (
                  <a href={sch.official_url} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-600 text-zinc-950 text-[10px] font-bold hover:bg-emerald-500 transition-colors">
                    <ExternalLink size={10} /> Official Site
                  </a>
                )}
                <button
                  onClick={() => setExpandedScholarship(isExpanded ? null : sch.name)}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-zinc-800 text-zinc-400 text-[10px] hover:text-white transition-colors"
                >
                  <Award size={10} /> {isExpanded ? "Hide Analysis" : "AI Analysis"}
                </button>
                <button className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-zinc-800 text-zinc-400 text-[10px] hover:text-white transition-colors">
                  <FileText size={10} /> Generate SOP
                </button>
                <button className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-zinc-800 text-zinc-400 text-[10px] hover:text-white transition-colors">
                  <Mail size={10} /> Email Professor
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
