"use client";

import { useState } from "react";
import {
  Search,
  GraduationCap,
  ExternalLink,
  Calendar,
  Globe,
  Loader2,
  Send,
} from "lucide-react";
import { PageHeader, Card, Button, Badge, EmptyState } from "@/components/ui";
import { scholarshipsApi, type Scholarship } from "@/lib/api";

export default function ScholarshipsPage() {
  const [scholarships, setScholarships] = useState<Scholarship[]>([]);
  const [searching, setSearching] = useState(false);
  const [targetDegree, setTargetDegree] = useState("");
  const [targetCountry, setTargetCountry] = useState("");
  const [researchArea, setResearchArea] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);
  const [applying, setApplying] = useState<string | null>(null);

  async function handleSearch() {
    try {
      setSearching(true);
      setError(null);
      const data = await scholarshipsApi.search({
        target_degree: targetDegree,
        target_country: targetCountry,
        research_area: researchArea,
      });
      setScholarships(data.scholarships || []);
      setSearched(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setSearching(false);
    }
  }

  async function handleApply(scholarship: Scholarship) {
    try {
      setApplying(scholarship.name);
      const info = `${scholarship.name} at ${scholarship.portal}. Country: ${scholarship.country || "N/A"}. Degree: ${scholarship.degree_level || "N/A"}. ${scholarship.url || ""}`;
      await scholarshipsApi.apply({
        scholarship_info: info,
        scholarship_name: scholarship.name,
        generate_sop: true,
        generate_motivation: true,
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
        title="Scholarship Search"
        description="Discover fully-funded scholarships and generate application materials"
      />

      {/* Search Bar */}
      <Card className="mb-6 p-6">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-zinc-500">Target Degree</label>
            <select
              value={targetDegree}
              onChange={(e) => setTargetDegree(e.target.value)}
              className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800"
            >
              <option value="">Any</option>
              <option value="masters">Master&apos;s</option>
              <option value="phd">PhD</option>
              <option value="postdoc">PostDoc</option>
              <option value="undergraduate">Undergraduate</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-zinc-500">Target Country</label>
            <input
              type="text"
              placeholder="e.g., Germany, UK, USA"
              value={targetCountry}
              onChange={(e) => setTargetCountry(e.target.value)}
              className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-zinc-500">Research Area</label>
            <input
              type="text"
              placeholder="e.g., machine learning, NLP"
              value={researchArea}
              onChange={(e) => setResearchArea(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800"
            />
          </div>
        </div>
        <div className="mt-4 flex justify-end">
          <Button onClick={handleSearch} disabled={searching}>
            {searching ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Search size={16} />
            )}
            {searching ? "Searching..." : "Search Scholarships"}
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
          icon={GraduationCap}
          title="Search for scholarships"
          description="Set your preferences and discover fully-funded scholarship opportunities worldwide"
        />
      ) : scholarships.length === 0 ? (
        <EmptyState
          icon={GraduationCap}
          title="No scholarships found"
          description="Try broadening your search criteria"
        />
      ) : (
        <>
          <p className="mb-4 text-sm text-zinc-500">
            Found {scholarships.length} scholarships — sorted by eligibility score
          </p>
          <div className="space-y-4">
            {scholarships.map((s, i) => (
              <Card key={i} className="p-5">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                  <div className="flex-1">
                    <div className="flex items-start gap-3">
                      <div className="rounded-lg bg-purple-50 p-2 dark:bg-purple-500/10">
                        <GraduationCap size={18} className="text-purple-600 dark:text-purple-400" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-zinc-900 dark:text-white">
                          {s.name}
                        </h3>
                        <div className="mt-1 flex flex-wrap items-center gap-2 text-sm text-zinc-500">
                          {s.portal && (
                            <span className="flex items-center gap-1">
                              <Globe size={12} /> {s.portal}
                            </span>
                          )}
                          {s.country && <span>· {s.country}</span>}
                          {s.degree_level && (
                            <>
                              <span>·</span>
                              <Badge>{s.degree_level}</Badge>
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    {s.deadline && (
                      <div className="mt-2 flex items-center gap-1.5 text-sm text-zinc-500">
                        <Calendar size={12} />
                        Deadline: {new Date(s.deadline).toLocaleDateString()}
                      </div>
                    )}

                    {/* Match Reasons */}
                    {s.match_reasons && s.match_reasons.length > 0 && (
                      <div className="mt-3">
                        <p className="mb-1 text-xs font-medium uppercase tracking-wider text-zinc-500">
                          Why it matches
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {s.match_reasons.map((reason, j) => (
                            <Badge key={j} variant="success">
                              {reason}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Right side: Score + Actions */}
                  <div className="flex flex-col items-end gap-3">
                    {s.eligibility_score !== undefined && (
                      <EligibilityScore score={s.eligibility_score} />
                    )}
                    <div className="flex gap-2">
                      {s.url && (
                        <a
                          href={s.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-200 px-3 py-1.5 text-xs font-medium text-zinc-600 transition-colors hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-400 dark:hover:bg-zinc-800"
                        >
                          <ExternalLink size={12} />
                          Portal
                        </a>
                      )}
                      <Button
                        onClick={() => handleApply(s)}
                        disabled={applying === s.name}
                        className="px-3 py-1.5 text-xs"
                      >
                        {applying === s.name ? (
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

function EligibilityScore({ score }: { score: number }) {
  const color =
    score >= 80
      ? "text-emerald-600 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-500/10"
      : score >= 60
      ? "text-amber-600 bg-amber-50 dark:text-amber-400 dark:bg-amber-500/10"
      : "text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-500/10";

  return (
    <div className={`flex items-center gap-1.5 rounded-lg px-3 py-2 ${color}`}>
      <span className="text-lg font-bold">{score}</span>
      <span className="text-xs opacity-70">eligible</span>
    </div>
  );
}
