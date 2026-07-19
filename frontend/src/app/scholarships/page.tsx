"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  GraduationCap,
  ExternalLink,
  Calendar,
  Globe,
  Loader2,
  Sparkles,
  DollarSign,
  CheckCircle2,
  Award,
  ArrowRight,
} from "lucide-react";
import { PageHeader, Card, Button, Badge, EmptyState } from "@/components/ui";
import { scholarshipsApi, type Scholarship } from "@/lib/api";

export default function ScholarshipsPage() {
  const router = useRouter();
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
      setError(err instanceof Error ? err.message : "Scholarship search failed");
    } finally {
      setSearching(false);
    }
  }

  async function handleApply(scholarship: Scholarship) {
    try {
      setApplying(scholarship.name);
      const info = `${scholarship.name} (${scholarship.portal || scholarship.provider}). Location: ${scholarship.country || "International"}. Degree: ${scholarship.degree_level || "Master's/PhD"}. Amount: ${scholarship.amount || "Fully Funded"}. Link: ${scholarship.url || ""}`;
      await scholarshipsApi.apply({
        scholarship_info: info,
        scholarship_name: scholarship.name,
        generate_sop: true,
        generate_motivation: true,
      });
      router.push("/documents");
    } catch (err) {
      alert("Failed to initiate application draft");
    } finally {
      setApplying(null);
    }
  }

  return (
    <div>
      <PageHeader
        title="Scholarship Search Engine"
        description="Discover 100% fully-funded global scholarships, fellowships, and research grants with tailored SOP drafting"
      />

      {/* Search Bar */}
      <Card className="mb-6 p-6">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-zinc-400">Target Degree</label>
            <select
              value={targetDegree}
              onChange={(e) => setTargetDegree(e.target.value)}
              className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-white"
            >
              <option value="">Any Degree Level</option>
              <option value="masters">Master&apos;s (MSc / MA)</option>
              <option value="phd">PhD / Doctorate</option>
              <option value="postdoc">Postdoctoral Fellowship</option>
              <option value="undergraduate">Undergraduate (BSc)</option>
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-zinc-400">Target Country / Region</label>
            <input
              type="text"
              placeholder="e.g., Germany, UK, USA, EU, Japan"
              value={targetCountry}
              onChange={(e) => setTargetCountry(e.target.value)}
              className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-white"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-zinc-400">Research Area / Specialization</label>
            <input
              type="text"
              placeholder="e.g., Machine Learning, Computer Vision, Robotics"
              value={researchArea}
              onChange={(e) => setResearchArea(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2.5 text-sm dark:border-zinc-700 dark:bg-zinc-800 dark:text-white"
            />
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <Button onClick={handleSearch} disabled={searching} className="bg-emerald-600 hover:bg-emerald-500 text-white font-medium px-5">
            {searching ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Search size={16} />
            )}
            {searching ? "Searching Global Portals..." : "Discover Scholarships"}
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
          title="Search 13+ Global Scholarship Databases"
          description="Filter DAAD, Chevening, Fulbright, Erasmus Mundus, Gates Cambridge & MEXT by degree, location, and research domain."
        />
      ) : scholarships.length === 0 ? (
        <EmptyState
          icon={GraduationCap}
          title="No exact scholarship matches found"
          description="Try clearing your degree or country filters to expand your search across all global grant portals."
        />
      ) : (
        <>
          <div className="mb-4 flex items-center justify-between">
            <p className="text-sm font-medium text-zinc-400">
              Found <span className="text-emerald-400 font-semibold">{scholarships.length}</span> fully-funded opportunities — ranked by eligibility match
            </p>
          </div>

          <div className="space-y-4">
            {scholarships.map((s, i) => {
              const score = s.eligibility_score ?? (s as any).fit_score ?? 85;
              const providerName = s.portal || (s as any).provider || s.name;
              const reasons = s.match_reasons || (s as any).eligibility_notes || [];
              const amountText = (s as any).amount || "Full Tuition + Monthly Stipend";

              return (
                <Card key={i} className="p-6 transition-all hover:border-emerald-500/30">
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                    <div className="flex-1">
                      <div className="flex items-start gap-3">
                        <div className="rounded-xl bg-emerald-500/10 p-2.5 text-emerald-400 border border-emerald-500/20">
                          <GraduationCap size={22} />
                        </div>
                        <div>
                          <h3 className="text-base font-bold text-zinc-900 dark:text-white flex items-center gap-2">
                            {s.name}
                          </h3>
                          <div className="mt-1.5 flex flex-wrap items-center gap-3 text-xs text-zinc-400">
                            <span className="flex items-center gap-1 font-medium text-zinc-300">
                              <Globe size={13} className="text-emerald-400" /> {s.country || providerName}
                            </span>
                            <span>•</span>
                            <Badge variant="default" className="text-xs bg-zinc-800 text-zinc-300 border border-zinc-700">
                              {s.degree_level || "MSc / PhD"}
                            </Badge>
                            <span>•</span>
                            <span className="flex items-center gap-1 text-emerald-400 font-medium">
                              <DollarSign size={13} /> {amountText}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Benefits & Deadline Bar */}
                      <div className="mt-4 flex flex-wrap items-center gap-4 text-xs text-zinc-400 border-t border-b border-zinc-800/80 py-2.5">
                        {s.deadline && (
                          <div className="flex items-center gap-1.5 font-medium text-amber-400">
                            <Calendar size={13} />
                            Deadline: {s.deadline}
                          </div>
                        )}
                        <div className="flex items-center gap-1 text-emerald-400">
                          <CheckCircle2 size={13} /> 100% Tuition Covered
                        </div>
                      </div>

                      {/* Why it matches */}
                      {reasons.length > 0 && (
                        <div className="mt-3">
                          <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-zinc-500">
                            Profile Match Analysis
                          </p>
                          <div className="flex flex-wrap gap-1.5">
                            {reasons.map((reason: string, j: number) => (
                              <span
                                key={j}
                                className="rounded-md bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 text-xs text-emerald-300 font-medium"
                              >
                                ✓ {reason}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Right side: Match Pill + Action Buttons */}
                    <div className="flex flex-col items-end justify-between gap-4 self-stretch border-t border-zinc-800 pt-4 lg:border-t-0 lg:pt-0">
                      <div className="flex items-center gap-2 rounded-lg bg-emerald-500/10 px-3 py-1.5 border border-emerald-500/20">
                        <Award size={16} className="text-emerald-400" />
                        <span className="text-sm font-bold text-emerald-400">{score}% Eligibility Match</span>
                      </div>

                      <div className="flex items-center gap-2 w-full lg:w-auto">
                        {s.url && (
                          <a
                            href={s.url.startsWith("http") ? s.url : `https://${s.url}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1.5 rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-xs font-medium text-zinc-300 hover:bg-zinc-700 transition-colors"
                          >
                            Official Portal <ExternalLink size={13} />
                          </a>
                        )}

                        <Button
                          onClick={() => handleApply(s)}
                          disabled={applying === s.name}
                          className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs px-3.5 py-2 flex items-center gap-1.5 shadow-md"
                        >
                          {applying === s.name ? (
                            <Loader2 size={13} className="animate-spin" />
                          ) : (
                            <Sparkles size={13} />
                          )}
                          Apply & Draft SOP <ArrowRight size={13} />
                        </Button>
                      </div>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
