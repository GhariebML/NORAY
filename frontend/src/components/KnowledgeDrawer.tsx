"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  X,
  Upload,
  Search,
  FileText,
  Trash2,
  RefreshCw,
  Eye,
  CheckCircle2,
  AlertCircle,
  Loader2,
  FolderTree,
  Sparkles,
  Layers,
  Database,
  Clock,
  Tag,
  BookOpen,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { workspaceApi } from "@/lib/api";
import { knowledgeService, knowledgeEventBus, type QueueItem } from "@/lib/knowledgeService";

interface KnowledgeDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

interface IndexedDoc {
  id: string;
  source: string;
  category: string;
  content: string;
  doc_type?: string;
  summary?: string;
  keywords?: string[];
  chunks_count?: number;
  created_at?: string;
}

interface DocDetail {
  id: string;
  source: string;
  category: string;
  content: string;
  doc_type: string;
  summary: string;
  keywords: string[];
  language: string;
  reading_time_min: number;
  word_count: number;
  chunks_count: number;
  created_at: string;
  updated_at: string;
}

export function KnowledgeDrawer({ isOpen, onClose }: KnowledgeDrawerProps) {
  const [dragActive, setDragActive] = useState(false);
  const [category, setCategory] = useState("general");
  const [searchQuery, setSearchQuery] = useState("");
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [documents, setDocuments] = useState<IndexedDoc[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<DocDetail | null>(null);
  const [, setLoadingDetail] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const unsubscribeQueue = knowledgeService.subscribeQueue((updatedQueue) => {
      setQueue(updatedQueue);
    });

    const unsubscribeEvent = knowledgeEventBus.subscribe((event) => {
      if (
        event.type === "DocumentUploaded" ||
        event.type === "KnowledgeUpdated" ||
        event.type === "DocumentDeleted"
      ) {
        loadDocuments();
      }
    });

    if (isOpen) {
      loadDocuments();
    }

    return () => {
      unsubscribeQueue();
      unsubscribeEvent();
    };
  }, [isOpen]);

  // Global Clipboard Paste listener (Ctrl+V)
  useEffect(() => {
    if (!isOpen) return;

    const handlePaste = (e: ClipboardEvent) => {
      if (e.clipboardData && e.clipboardData.files && e.clipboardData.files.length > 0) {
        e.preventDefault();
        knowledgeService.uploadFiles(Array.from(e.clipboardData.files), category);
      }
    };

    window.addEventListener("paste", handlePaste);
    return () => window.removeEventListener("paste", handlePaste);
  }, [isOpen, category]);

  async function loadDocuments() {
    setLoadingDocs(true);
    try {
      const data = await workspaceApi.listDocs();
      setDocuments(data || []);
    } catch (err) {
      console.error("Failed to load documents", err);
    } finally {
      setLoadingDocs(false);
    }
  }

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      knowledgeService.uploadFiles(Array.from(e.dataTransfer.files), category);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      knowledgeService.uploadFiles(Array.from(e.target.files), category);
    }
  };

  const handlePreview = async (id: string) => {
    setLoadingDetail(true);
    try {
      const details = await workspaceApi.getDocDetails(id);
      setSelectedDoc(details);
    } catch (err) {
      console.error("Failed to load document details", err);
      // Fallback detail
      const fallback = documents.find((d) => d.id === id);
      if (fallback) {
        setSelectedDoc({
          id: fallback.id,
          source: fallback.source,
          category: fallback.category,
          content: fallback.content,
          doc_type: fallback.doc_type || "Document",
          summary: fallback.summary || fallback.content.slice(0, 200),
          keywords: fallback.keywords || [],
          language: "en",
          reading_time_min: 1,
          word_count: fallback.content.split(/\s+/).length,
          chunks_count: fallback.chunks_count || 1,
          created_at: fallback.created_at || new Date().toISOString(),
          updated_at: new Date().toISOString(),
        });
      }
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to remove this knowledge document from Qdrant vector & BM25 indices?"))
      return;
    try {
      await workspaceApi.deleteDoc(id);
      loadDocuments();
      if (selectedDoc?.id === id) setSelectedDoc(null);
    } catch (err) {
      console.error("Delete failed", err);
    }
  };

  const handleReindex = async (id: string) => {
    try {
      await workspaceApi.reindexDoc(id, category);
      loadDocuments();
    } catch (err) {
      console.error("Reindex failed", err);
    }
  };

  const filteredDocs = documents.filter((doc) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      doc.source.toLowerCase().includes(q) ||
      doc.category.toLowerCase().includes(q) ||
      (doc.doc_type && doc.doc_type.toLowerCase().includes(q)) ||
      doc.content.toLowerCase().includes(q)
    );
  });

  const categoriesList = [
    { value: "general", label: "General Knowledge Base" },
    { value: "resume", label: "Career & Resumes" },
    { value: "scholarship", label: "Grants & Scholarships" },
    { value: "research", label: "Academic Research & Papers" },
    { value: "projects", label: "Engineering Projects" },
    { value: "career", label: "Career & Cover Letters" },
    { value: "personal_memory", label: "Personal Identity & Memory" },
    { value: "custom", label: "Custom Namespace" },
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm"
          />

          {/* Slide-Over Main Drawer */}
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="fixed inset-y-0 right-0 z-50 w-full max-w-3xl bg-[#09090b] border-l border-zinc-850 shadow-2xl flex flex-col font-mono text-xs text-zinc-300 overflow-hidden"
          >
            {/* Header */}
            <div className="p-5 border-b border-zinc-900 bg-zinc-950/80 backdrop-blur-md flex items-center justify-between shrink-0">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                  <Database size={18} />
                </div>
                <div>
                  <h2 className="text-sm font-bold text-zinc-100 uppercase tracking-wide flex items-center gap-2">
                    Knowledge Center
                    <span className="text-[10px] text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full font-mono">
                      System-Wide Service
                    </span>
                  </h2>
                  <p className="text-[11px] text-zinc-400 mt-0.5">
                    Upload documents to expand your AI vector memory across all NORAY modules.
                  </p>
                </div>
              </div>

              <button
                onClick={onClose}
                className="p-1.5 rounded-lg border border-zinc-800 bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-white transition"
              >
                <X size={16} />
              </button>
            </div>

            {/* Scrollable Content Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              
              {/* Namespace Selector & Controls */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-[10px] uppercase font-bold text-zinc-400 flex items-center gap-1.5">
                    <FolderTree size={12} className="text-emerald-400" />
                    <span>Target Namespace</span>
                  </label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:border-emerald-500 font-mono"
                  >
                    {categoriesList.map((cat) => (
                      <option key={cat.value} value={cat.value}>
                        {cat.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="text-[10px] uppercase font-bold text-zinc-400 flex items-center gap-1.5">
                    <Search size={12} className="text-emerald-400" />
                    <span>Search Knowledge Base</span>
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      placeholder="Filter by filename, keywords, or content..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full bg-zinc-950 border border-zinc-800 rounded-lg pl-8 pr-3 py-2 text-zinc-200 focus:outline-none focus:border-emerald-500 font-mono placeholder:text-zinc-500"
                    />
                    <Search size={13} className="absolute left-2.5 top-2.5 text-zinc-400" />
                  </div>
                </div>
              </div>

              {/* Drag & Drop Zone */}
              <div
                onDragEnter={handleDrag}
                onDragOver={handleDrag}
                onDragLeave={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center gap-3 text-center cursor-pointer transition-all duration-300 ${
                  dragActive
                    ? "border-emerald-400 bg-emerald-500/10 shadow-[0_0_30px_rgba(16,185,129,0.15)]"
                    : "border-zinc-800 hover:border-zinc-700 bg-zinc-950/40"
                }`}
              >
                <input
                  type="file"
                  multiple
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  className="hidden"
                  accept=".pdf,.docx,.txt,.md,.markdown,.csv,.png,.jpg,.jpeg,.tiff,.bmp,.xlsx,.xls,.pptx"
                />
                <div className="p-3.5 rounded-full bg-zinc-900 border border-zinc-800 text-zinc-400">
                  <Upload size={22} className={dragActive ? "text-emerald-400 animate-bounce" : ""} />
                </div>
                <div>
                  <p className="font-bold text-zinc-200 text-sm">
                    Drop files here or <span className="text-emerald-400 hover:underline">Browse Files</span>
                  </p>
                  <p className="text-[10px] text-zinc-400 mt-1">
                    Supports PDF, DOCX, TXT, MD, CSV, XLSX, PPTX, PNG, JPG (Max: 50MB) • Press <kbd className="px-1 py-0.5 rounded bg-zinc-900 text-zinc-400 border border-zinc-800">Ctrl+V</kbd> to paste
                  </p>
                </div>

                {/* Formats Badges */}
                <div className="flex flex-wrap justify-center gap-1.5 pt-1">
                  {["PDF", "DOCX", "PPTX", "XLSX", "TXT", "MD", "CSV", "Images"].map((fmt) => (
                    <span
                      key={fmt}
                      className="px-2 py-0.5 rounded bg-zinc-900/80 text-zinc-400 text-[9px] border border-zinc-800 font-mono"
                    >
                      {fmt}
                    </span>
                  ))}
                </div>
              </div>

              {/* Active Upload Processing Queue */}
              {queue.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs uppercase font-bold text-zinc-400 tracking-wider flex items-center gap-2">
                      <Sparkles size={13} className="text-emerald-400 animate-pulse" />
                      Active Ingestion Queue ({queue.filter((q) => q.status !== "completed").length} active)
                    </h3>
                    <button
                      onClick={() => knowledgeService.clearCompleted()}
                      className="text-[10px] text-zinc-400 hover:text-zinc-200"
                    >
                      Clear Completed
                    </button>
                  </div>

                  <div className="space-y-2.5">
                    {queue.map((item) => (
                      <div key={item.id} className="p-3.5 rounded-xl bg-zinc-950 border border-zinc-850 space-y-2.5">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2 truncate">
                            <FileText size={14} className="text-emerald-400 shrink-0" />
                            <span className="font-bold text-zinc-200 truncate">{item.file.name}</span>
                            <span className="text-[9px] text-zinc-400 bg-zinc-900 border border-zinc-800 px-1.5 py-0.5 rounded font-mono">
                              {item.category}
                            </span>
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            <span className="text-[10px] text-zinc-400 font-mono">{item.stage}</span>
                            {item.status === "completed" && <CheckCircle2 size={13} className="text-emerald-400" />}
                            {item.status === "failed" && <AlertCircle size={13} className="text-rose-450" />}
                            {item.status !== "completed" && item.status !== "failed" && (
                              <Loader2 size={13} className="animate-spin text-emerald-400" />
                            )}
                            {item.status === "failed" && (
                              <button
                                onClick={() => knowledgeService.retry(item.id)}
                                className="p-1 hover:text-emerald-400"
                                title="Retry"
                              >
                                <RefreshCw size={12} />
                              </button>
                            )}
                            <button
                              onClick={() => knowledgeService.cancel(item.id)}
                              className="p-1 hover:text-rose-450"
                              title="Cancel"
                            >
                              <X size={12} />
                            </button>
                          </div>
                        </div>

                        {/* Progress Bar */}
                        <div className="h-1.5 w-full bg-zinc-900 rounded-full overflow-hidden">
                          <div
                            className={`h-full transition-all duration-300 ${
                              item.status === "failed" ? "bg-rose-600" : "bg-emerald-500"
                            }`}
                            style={{ width: `${item.progress}%` }}
                          />
                        </div>

                        {/* Logs & Error Details */}
                        <div className="p-2 rounded bg-zinc-900/60 border border-zinc-800/60 text-[9px] font-mono max-h-24 overflow-y-auto leading-relaxed">
                          {item.error && (
                            <div className="text-rose-400 font-bold mb-1 border-b border-rose-500/20 pb-1">
                              ✖ Failure Cause: {item.error}
                            </div>
                          )}
                          {item.logs.map((log, idx) => (
                            <div key={idx} className="text-zinc-400">{log}</div>
                          ))}
                        </div>

                        {/* Developer Debug Panel */}
                        <details className="text-[9px] text-zinc-500 font-mono pt-0.5 border-t border-zinc-900/60">
                          <summary className="cursor-pointer hover:text-emerald-400 select-none">
                            Developer Debug Panel (Stage: {item.stage})
                          </summary>
                          <div className="mt-1 p-2 rounded bg-zinc-950 border border-zinc-900 space-y-1 text-zinc-400">
                            <div>Provider: <span className="text-emerald-400">Local SentenceTransformers (MiniLM-L6-v2)</span></div>
                            <div>Vector Dim: <span className="text-emerald-400">384d</span></div>
                            <div>Namespace: <span className="text-emerald-400">{item.category}</span></div>
                            <div>Correlation ID: <span className="text-zinc-500">req_{item.id}</span></div>
                            {item.error && <div className="text-rose-400 break-all">Trace: {item.error}</div>}
                          </div>
                        </details>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Indexed Knowledge Library Table */}
              <div className="space-y-3">
                <div className="flex items-center justify-between border-b border-zinc-900 pb-2">
                  <h3 className="text-xs uppercase font-bold text-zinc-300 tracking-wider flex items-center gap-2">
                    <Layers size={13} className="text-emerald-400" />
                    System Knowledge Library ({filteredDocs.length})
                  </h3>
                  <button
                    onClick={loadDocuments}
                    className="p-1 rounded text-zinc-400 hover:text-white transition"
                    title="Refresh Library"
                  >
                    <RefreshCw size={12} className={loadingDocs ? "animate-spin" : ""} />
                  </button>
                </div>

                {loadingDocs ? (
                  <div className="flex items-center justify-center gap-2 text-zinc-400 py-12 italic">
                    <Loader2 size={14} className="animate-spin text-emerald-400" />
                    <span>Loading Qdrant & BM25 Knowledge Store...</span>
                  </div>
                ) : filteredDocs.length === 0 ? (
                  <div className="text-center text-zinc-500 py-12 italic text-[11px] border border-dashed border-zinc-900 rounded-xl">
                    No documents indexed in this query space. Click "+ Add Knowledge" to upload files.
                  </div>
                ) : (
                  <div className="space-y-2 max-h-[420px] overflow-y-auto pr-1">
                    {filteredDocs.map((doc) => (
                      <div
                        key={doc.id}
                        className="p-3.5 rounded-xl border border-zinc-850 bg-zinc-950/60 hover:border-zinc-700 transition flex items-center justify-between gap-4 group"
                      >
                        <div className="flex items-center gap-3 truncate">
                          <div className="p-2 rounded-lg bg-zinc-900 border border-zinc-800 text-emerald-400 shrink-0">
                            <FileText size={16} />
                          </div>
                          <div className="truncate">
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-zinc-200 truncate">{doc.source}</span>
                              <span className="text-[9px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-1.5 py-0.5 rounded font-mono uppercase">
                                {doc.doc_type || "Document"}
                              </span>
                            </div>
                            <p className="text-[10px] text-zinc-400 truncate mt-0.5">
                              "{doc.summary || doc.content}"
                            </p>
                          </div>
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-2 shrink-0">
                          <button
                            onClick={() => handlePreview(doc.id)}
                            className="px-2.5 py-1 rounded bg-zinc-900 border border-zinc-800 text-emerald-400 hover:bg-emerald-500/10 transition flex items-center gap-1 text-[10px]"
                          >
                            <Eye size={11} /> Preview
                          </button>
                          <button
                            onClick={() => handleReindex(doc.id)}
                            className="p-1.5 rounded bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-zinc-200 transition"
                            title="Re-index Document"
                          >
                            <RefreshCw size={12} />
                          </button>
                          <button
                            onClick={() => handleDelete(doc.id)}
                            className="p-1.5 rounded bg-zinc-900 border border-zinc-800 text-rose-450 hover:text-rose-400 transition"
                            title="Delete Document"
                          >
                            <Trash2 size={12} />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

            </div>
          </motion.div>

          {/* Secondary Detail & Chunk Explorer Side Drawer */}
          <AnimatePresence>
            {selectedDoc && (
              <motion.div
                initial={{ x: "100%" }}
                animate={{ x: 0 }}
                exit={{ x: "100%" }}
                transition={{ type: "spring", damping: 25, stiffness: 200 }}
                className="fixed inset-y-0 right-0 z-50 w-full max-w-lg bg-[#0c0c0e] border-l border-zinc-800 p-6 shadow-2xl flex flex-col font-mono text-xs text-zinc-300 overflow-hidden"
              >
                {/* Secondary Header */}
                <div className="flex items-center justify-between border-b border-zinc-900 pb-3 mb-4">
                  <div>
                    <h3 className="font-bold text-zinc-100 truncate max-w-[280px]">{selectedDoc.source}</h3>
                    <span className="text-[9px] text-zinc-400 font-mono">ID: {selectedDoc.id}</span>
                  </div>
                  <button
                    onClick={() => setSelectedDoc(null)}
                    className="p-1.5 rounded bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white"
                  >
                    <X size={14} />
                  </button>
                </div>

                <div className="flex-1 overflow-y-auto space-y-4 pr-1">
                  {/* Metadata Cards */}
                  <div className="grid grid-cols-2 gap-2 text-[10px]">
                    <div className="p-2.5 rounded bg-zinc-950 border border-zinc-900 space-y-1">
                      <span className="text-zinc-400 flex items-center gap-1">
                        <Tag size={10} className="text-emerald-400" /> Type:
                      </span>
                      <span className="font-bold text-zinc-200">{selectedDoc.doc_type}</span>
                    </div>
                    <div className="p-2.5 rounded bg-zinc-950 border border-zinc-900 space-y-1">
                      <span className="text-zinc-400 flex items-center gap-1">
                        <FolderTree size={10} className="text-emerald-400" /> Namespace:
                      </span>
                      <span className="font-bold text-zinc-200">{selectedDoc.category}</span>
                    </div>
                    <div className="p-2.5 rounded bg-zinc-950 border border-zinc-900 space-y-1">
                      <span className="text-zinc-400 flex items-center gap-1">
                        <BookOpen size={10} className="text-emerald-400" /> Chunks Count:
                      </span>
                      <span className="font-bold text-zinc-200">{selectedDoc.chunks_count} Chunks</span>
                    </div>
                    <div className="p-2.5 rounded bg-zinc-950 border border-zinc-900 space-y-1">
                      <span className="text-zinc-400 flex items-center gap-1">
                        <Clock size={10} className="text-emerald-400" /> Reading Time:
                      </span>
                      <span className="font-bold text-zinc-200">{selectedDoc.reading_time_min} mins ({selectedDoc.word_count} words)</span>
                    </div>
                  </div>

                  {/* AI Generated Summary */}
                  <div className="space-y-1.5">
                    <span className="text-[10px] uppercase font-bold text-zinc-400 flex items-center gap-1.5">
                      <Sparkles size={11} className="text-emerald-400" />
                      AI Summary & Overview
                    </span>
                    <div className="p-3 rounded bg-zinc-950 border border-zinc-900 text-[11px] text-zinc-300 leading-relaxed font-sans italic">
                      "{selectedDoc.summary}"
                    </div>
                  </div>

                  {/* Keywords */}
                  {selectedDoc.keywords && selectedDoc.keywords.length > 0 && (
                    <div className="space-y-1.5">
                      <span className="text-[10px] uppercase font-bold text-zinc-400">Extracted Keywords</span>
                      <div className="flex flex-wrap gap-1.5">
                        {selectedDoc.keywords.map((kw, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[9px]"
                          >
                            #{kw}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Chunk Content Preview */}
                  <div className="space-y-1.5">
                    <span className="text-[10px] uppercase font-bold text-zinc-400 flex items-center gap-1.5">
                      <Layers size={11} className="text-emerald-400" />
                      Vector Chunk Content Preview
                    </span>
                    <div className="p-3.5 rounded bg-zinc-950 border border-zinc-900 font-sans text-[11px] text-zinc-300 leading-relaxed max-h-64 overflow-y-auto whitespace-pre-wrap">
                      {selectedDoc.content}
                    </div>
                  </div>
                </div>

                {/* Footer Controls */}
                <div className="border-t border-zinc-900 pt-3 flex justify-between items-center text-[10px] text-zinc-400">
                  <span>Created: {new Date(selectedDoc.created_at).toLocaleDateString()}</span>
                  <button
                    onClick={() => handleDelete(selectedDoc.id)}
                    className="px-3 py-1 rounded bg-rose-500/10 border border-rose-500/20 text-rose-400 hover:bg-rose-500/20 transition font-bold"
                  >
                    Delete Document
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </>
      )}
    </AnimatePresence>
  );
}
