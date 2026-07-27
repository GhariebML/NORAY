"use client";

import { useEffect, useState } from "react";
import {
  Brain,
  Search,
  Database,
  Layers,
  CheckCircle2,
  Trash2,
  RefreshCw,
} from "lucide-react";
import { PageHeader, Card, Badge } from "@/components/ui";
import { profileApi, workspaceApi } from "@/lib/api";

interface Fact {
  id: string;
  category: string;
  fact: string;
  timestamp: string;
}

interface Triple {
  source: string;
  relation: string;
  target: string;
}

export default function MemoryPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [facts, setFacts] = useState<Fact[]>([]);
  const [triples, setTriples] = useState<Triple[]>([]);
  const [loading, setLoading] = useState(false);

  async function fetchMemoryData() {
    setLoading(true);
    try {
      const [profData, graphData] = await Promise.all([
        profileApi.get(),
        workspaceApi.getGraphTriples(30)
      ]);

      // Map profile education and experiences to facts
      const mappedFacts: Fact[] = [];
      let factId = 1;

      const profile = profData.profile as any;
      if (profile) {
        if (profile.identity?.full_name) {
          mappedFacts.push({
            id: `f_${factId++}`,
            category: "Identity",
            fact: `Name: ${profile.identity.full_name} (${profile.identity.title || "Developer"})`,
            timestamp: "Persistent"
          });
        }
        if (profile.skills?.primary_languages) {
          mappedFacts.push({
            id: `f_${factId++}`,
            category: "Skill",
            fact: `Languages: ${profile.skills.primary_languages.join(", ")}`,
            timestamp: "Persistent"
          });
        }
        if (profile.education) {
          profile.education.forEach((edu: any) => {
            mappedFacts.push({
              id: `f_${factId++}`,
              category: "Education",
              fact: `Degree: ${edu.degree} in ${edu.major} from ${edu.institution} (GPA: ${edu.gpa || "N/A"})`,
              timestamp: "Persistent"
            });
          });
        }
        if (profile.experience) {
          profile.experience.forEach((exp: any) => {
            mappedFacts.push({
              id: `f_${factId++}`,
              category: "Experience",
              fact: `Role: ${exp.role} at ${exp.company} — ${exp.description}`,
              timestamp: "Persistent"
            });
          });
        }
      }

      // Default fallback facts if empty
      if (mappedFacts.length === 0) {
        mappedFacts.push(
          { id: "1", category: "Skill", fact: "Primary programming language: Python (PyTorch, FastAPI, NumPy)", timestamp: "2026-07-18" },
          { id: "2", category: "Experience", fact: "Engineered NORAY Agentic RAG Operating System & Dual-Tier Model Router", timestamp: "2026-07-18" },
          { id: "3", category: "Education", fact: "BSc in Computer Science & Artificial Intelligence (GPA: 3.8/4.0)", timestamp: "2026-07-17" }
        );
      }

      setFacts(mappedFacts);
      setTriples(graphData.triples || []);
    } catch (e) {
      console.error("Failed to load memory center telemetry", e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchMemoryData();
  }, []);

  const filteredFacts = facts.filter((f) =>
    f.fact.toLowerCase().includes(searchQuery.toLowerCase()) ||
    f.category.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6 text-gray-200">
      <PageHeader
        title="AI Memory Center"
        description="Explore persistent Facts, Knowledge Graph Triples, and Vector Store Indexing metadata"
      >
        <button
          onClick={fetchMemoryData}
          disabled={loading}
          className="p-1.5 rounded-lg border border-zinc-850 bg-zinc-950 text-slate-400 hover:text-slate-200 disabled:opacity-50 transition"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
        </button>
      </PageHeader>

      {/* Search Bar */}
      <Card className="p-4 bg-zinc-950/40 border border-zinc-900">
        <div className="flex items-center gap-3">
          <Search className="text-emerald-400" size={18} />
          <input
            type="text"
            placeholder="Search saved memory, candidate profile facts, and vector embeddings..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 bg-transparent text-xs text-zinc-150 placeholder-zinc-600 focus:outline-none"
          />
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        
        {/* Left Column: Persistent Facts Index (2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="p-6 bg-zinc-950/40 border border-zinc-900">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-sm font-bold text-zinc-150 uppercase tracking-wider flex items-center gap-2">
                <Brain className="text-emerald-400" size={16} />
                Canonical Profile Facts & Memory Context
              </h2>
              <Badge variant="success" className="px-2.5 py-0.5 text-[9px] font-mono">
                {filteredFacts.length} Facts Indexed
              </Badge>
            </div>

            <div className="space-y-3">
              {filteredFacts.map((item) => (
                <div
                  key={item.id}
                  className="flex items-start justify-between gap-4 rounded-xl border border-zinc-900 bg-zinc-950/30 p-4 transition-all hover:border-zinc-800"
                >
                  <div className="flex items-start gap-3">
                    <div className="rounded-lg bg-emerald-500/10 p-2 text-emerald-400 border border-emerald-500/20 mt-0.5">
                      <CheckCircle2 size={14} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <Badge className="bg-zinc-900 text-emerald-400 border border-zinc-850 text-[9px]">
                          {item.category}
                        </Badge>
                        <span className="text-[9px] text-zinc-500 font-mono">{item.timestamp}</span>
                      </div>
                      <p className="mt-1.5 text-xs text-zinc-300 font-sans leading-relaxed">
                        {item.fact}
                      </p>
                    </div>
                  </div>

                  <button
                    onClick={() => setFacts(facts.filter((f) => f.id !== item.id))}
                    className="text-zinc-650 hover:text-rose-400 transition-colors p-1"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              ))}
            </div>
          </Card>

          {/* Knowledge Graph Triples */}
          <Card className="p-6 bg-zinc-950/40 border border-zinc-900">
            <h2 className="mb-4 text-sm font-bold text-zinc-150 uppercase tracking-wider flex items-center gap-2">
              <Layers className="text-emerald-400" size={16} />
              Knowledge Graph Entity Relationships (GraphRAG)
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono text-[10px]">
              {triples.map((t, idx) => (
                <div key={idx} className="rounded-lg border border-zinc-900 bg-zinc-950/20 p-3 space-y-1">
                  <span className="block text-emerald-400 font-semibold">{t.source}</span>
                  <span className="block text-[9px] text-zinc-550 uppercase tracking-wider">↓ {t.relation}</span>
                  <span className="block text-zinc-300 font-medium">{t.target}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Right Column: Indexing Telemetry */}
        <div className="space-y-6">
          <Card className="p-6 bg-zinc-950/40 border border-zinc-900">
            <h3 className="mb-4 text-sm font-bold text-zinc-150 uppercase tracking-wider flex items-center gap-2">
              <Database className="text-emerald-400" size={16} />
              Vector & BM25 Storage Metrics
            </h3>

            <div className="space-y-4 text-xs font-mono">
              <div className="rounded-lg border border-zinc-900 bg-zinc-950/20 p-3 space-y-1">
                <span className="text-zinc-550 block text-[9px] uppercase font-bold">VECTOR STORE PROVIDER</span>
                <span className="text-emerald-400 font-bold block text-sm">Qdrant Singleton</span>
                <span className="text-[9px] text-zinc-500 block">Path: data/qdrant</span>
              </div>

              <div className="rounded-lg border border-zinc-900 bg-zinc-950/20 p-3 space-y-1">
                <span className="text-zinc-550 block text-[9px] uppercase font-bold">SPARSE LEXICAL INDEX</span>
                <span className="text-emerald-400 font-bold block text-sm">BM25 (rank_bm25)</span>
                <span className="text-[9px] text-zinc-500 block">Reciprocal Rank Fusion Enabled</span>
              </div>

              <div className="rounded-lg border border-zinc-900 bg-zinc-950/20 p-3 space-y-1">
                <span className="text-zinc-550 block text-[9px] uppercase font-bold">EMBEDDING MODEL</span>
                <span className="text-emerald-400 font-bold block text-sm">all-MiniLM-L6-v2 (384d)</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
