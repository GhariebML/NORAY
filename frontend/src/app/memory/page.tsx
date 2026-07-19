"use client";

import { useState } from "react";
import {
  Brain,
  Search,
  Database,
  Layers,
  Sparkles,
  CheckCircle2,
  Clock,
  Trash2,
  Plus,
} from "lucide-react";
import { PageHeader, Card, Button, Badge } from "@/components/ui";

export default function MemoryPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [facts, setFacts] = useState([
    { id: "1", category: "Skill", fact: "Primary programming language: Python (PyTorch, FastAPI, NumPy)", timestamp: "2026-07-18" },
    { id: "2", category: "Experience", fact: "Engineered NORAY Agentic RAG Operating System & Dual-Tier Model Router", timestamp: "2026-07-18" },
    { id: "3", category: "Education", fact: "BSc in Computer Science & Artificial Intelligence (GPA: 3.8/4.0)", timestamp: "2026-07-17" },
    { id: "4", category: "Scholarship Goal", fact: "Targeting DAAD EPOS & Chevening Master's Fellowships in Germany & UK", timestamp: "2026-07-19" },
  ]);

  const [triples] = useState([
    { subject: "Gharieb Mohamed", predicate: "EXPERT_IN", object: "Agentic RAG & Vector Stores" },
    { subject: "NORAY Operating System", predicate: "USES_VECTOR_STORE", object: "Qdrant Singleton (384-dim)" },
    { subject: "Model Router", predicate: "ROUTES_TO", object: "Ollama (qwen2.5-coder:7b)" },
    { subject: "CV Generator", predicate: "COMPILES_TO", object: "Microsoft Word (.docx)" },
  ]);

  const filteredFacts = facts.filter((f) =>
    f.fact.toLowerCase().includes(searchQuery.toLowerCase()) ||
    f.category.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div>
      <PageHeader
        title="AI Memory Center"
        description="Explore persistent Facts, Knowledge Graph Triples, and Vector Store Indexing metadata"
      />

      {/* Search Bar */}
      <Card className="mb-6 p-4">
        <div className="flex items-center gap-3">
          <Search className="text-emerald-400" size={18} />
          <input
            type="text"
            placeholder="Search saved memory, candidate profile facts, and vector embeddings..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="flex-1 bg-transparent text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none"
          />
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left Column: Persistent Facts Index (2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="p-6">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-base font-bold text-zinc-100 font-heading flex items-center gap-2">
                <Brain className="text-emerald-400" size={20} />
                Canonical Profile Facts & Memory Context
              </h2>
              <Badge variant="success" className="px-2.5 py-0.5 text-xs">
                {filteredFacts.length} Facts Indexed
              </Badge>
            </div>

            <div className="space-y-3">
              {filteredFacts.map((item) => (
                <div
                  key={item.id}
                  className="flex items-start justify-between gap-4 rounded-xl border border-zinc-800 bg-[#161f2d]/80 p-4 transition-all hover:border-emerald-500/30"
                >
                  <div className="flex items-start gap-3">
                    <div className="rounded-lg bg-emerald-500/10 p-2 text-emerald-400 border border-emerald-500/20 mt-0.5">
                      <CheckCircle2 size={16} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <Badge className="bg-zinc-800 text-emerald-400 border border-zinc-700 text-[10px]">
                          {item.category}
                        </Badge>
                        <span className="text-[10px] text-zinc-500 font-mono">{item.timestamp}</span>
                      </div>
                      <p className="mt-1.5 text-xs text-zinc-200 font-sans leading-relaxed">
                        {item.fact}
                      </p>
                    </div>
                  </div>

                  <button
                    onClick={() => setFacts(facts.filter((f) => f.id !== item.id))}
                    className="text-zinc-500 hover:text-red-400 transition-colors p-1"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
            </div>
          </Card>

          {/* Knowledge Graph Triples */}
          <Card className="p-6">
            <h2 className="mb-4 text-base font-bold text-zinc-100 font-heading flex items-center gap-2">
              <Layers className="text-cyan-400" size={20} />
              Knowledge Graph Entity Relationships (GraphRAG)
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 font-mono text-xs">
              {triples.map((t, idx) => (
                <div key={idx} className="rounded-lg border border-zinc-800 bg-[#111827] p-3 space-y-1">
                  <span className="block text-emerald-400 font-semibold">{t.subject}</span>
                  <span className="block text-[10px] text-zinc-500 uppercase tracking-wider">↓ {t.predicate}</span>
                  <span className="block text-zinc-300 font-medium">{t.object}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Right Column: Indexing Telemetry */}
        <div className="space-y-6">
          <Card className="p-6">
            <h3 className="mb-4 text-sm font-bold text-zinc-100 font-heading flex items-center gap-2">
              <Database className="text-emerald-400" size={18} />
              Vector & BM25 Storage Metrics
            </h3>

            <div className="space-y-4 text-xs font-mono">
              <div className="rounded-lg border border-zinc-800 bg-[#111827] p-3 space-y-1">
                <span className="text-zinc-400 block text-[10px]">VECTOR STORE PROVIDER</span>
                <span className="text-emerald-400 font-bold block text-sm">Qdrant Singleton</span>
                <span className="text-[10px] text-zinc-500 block">Path: data/qdrant</span>
              </div>

              <div className="rounded-lg border border-zinc-800 bg-[#111827] p-3 space-y-1">
                <span className="text-zinc-400 block text-[10px]">SPARSE LEXICAL INDEX</span>
                <span className="text-cyan-400 font-bold block text-sm">BM25 (rank_bm25)</span>
                <span className="text-[10px] text-zinc-500 block">Reciprocal Rank Fusion Enabled</span>
              </div>

              <div className="rounded-lg border border-zinc-800 bg-[#111827] p-3 space-y-1">
                <span className="text-zinc-400 block text-[10px]">EMBEDDING DIMENSION</span>
                <span className="text-amber-400 font-bold block text-sm">384 (all-MiniLM-L6-v2)</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
