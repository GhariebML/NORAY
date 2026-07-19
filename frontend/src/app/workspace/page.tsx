"use client";

import { useState, useEffect, useRef, useMemo } from "react";
import { 
  Send, 
  Upload, 
  FileText, 
  Trash2, 
  MessageSquare, 
  Search, 
  BookOpen, 
  Database,
  Loader2,
  FileCheck,
  Globe,
  Sliders,
  Network,
  Compass,
  Cpu,
  Star,
  CheckCircle,
  HelpCircle,
  FileSearch,
  Sparkles,
  Info,
  Maximize2,
  Plus,
  Minimize2,
  Eye,
  Paperclip,
  Check
} from "lucide-react";
import { PageHeader, Card, Button, Badge, PageTransition } from "@/components/ui";
import { workspaceApi, type ChatResponse, type SearchResult } from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: { id: string; source: string; score: number }[];
  explainability?: {
    confidence_score: number;
    retrieved_nodes: any[];
    retrieved_edges: any[];
    retrieved_triples: string[];
    reasoning_steps: string[];
  };
}

interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  sessionId: string;
}

// Initial mockup nodes for the Interactive Knowledge Graph
interface GraphNode {
  id: string;
  label: string;
  type: "candidate" | "job" | "scholarship" | "skill" | "document";
  x: number;
  y: number;
}

interface GraphEdge {
  source: string;
  target: string;
  label: string;
}

export default function WorkspacePage() {
  // Resizable split-panes width (percent of screen)
  const [leftWidth, setLeftWidth] = useState(60); // 60% left
  const isResizingRef = useRef(false);

  // Chat sessions state
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string>("");
  const [chatLoading, setChatLoading] = useState(false);
  const [streamingText, setStreamingText] = useState("");
  const [input, setInput] = useState("");
  const [showHistory, setShowHistory] = useState(true);

  // Active right column tab
  const [activeRightTab, setActiveRightTab] = useState<"ingest" | "graph" | "research">("ingest");
  
  // Selected explainability to show on Right Column
  const [selectedExplain, setSelectedExplain] = useState<any>(null);

  // Search state
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);

  // Ingestion state
  const [docs, setDocs] = useState<{ id: string; source: string; category: string; content: string }[]>([]);
  const [uploadCategory, setUploadCategory] = useState("general");
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  // Deep Research state
  const [researchObjective, setResearchObjective] = useState("");
  const [researchDepth, setResearchDepth] = useState(2);
  const [researchLoading, setResearchLoading] = useState(false);
  const [researchReport, setResearchReport] = useState("");
  const [researchCitations, setResearchCitations] = useState<any[]>([]);
  const [researchSteps, setResearchSteps] = useState<string[]>([]);
  
  // Interactive Knowledge Graph state
  const [graphNodes, setGraphNodes] = useState<GraphNode[]>([]);
  const [graphEdges, setGraphEdges] = useState<GraphEdge[]>([]);
  const [selectedGraphNode, setSelectedGraphNode] = useState<GraphNode | null>(null);
  const [graphSearchQuery, setGraphSearchQuery] = useState("");
  const [zoomLevel, setZoomLevel] = useState(1);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const [draggingNodeId, setDraggingNodeId] = useState<string | null>(null);
  const [isPanning, setIsPanning] = useState(false);
  const panStartRef = useRef({ x: 0, y: 0 });

  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);

  // Load Sessions and Documents at startup
  useEffect(() => {
    loadDocs();
    initMockSessions();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [sessions, activeSessionId, streamingText]);

  // Document management
  async function loadDocs() {
    try {
      const data = await workspaceApi.listDocs();
      setDocs(data || []);
      
      // Seed Knowledge Graph with nodes representing actual documents + related entities
      seedGraphFromDocs(data || []);
    } catch (err) {
      console.error("Failed to load documents", err);
    }
  }

  const activeSession = useMemo(() => {
    return sessions.find(s => s.id === activeSessionId) || null;
  }, [sessions, activeSessionId]);

  function initMockSessions() {
    const saved = localStorage.getItem("noray-chat-sessions");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (parsed.length > 0) {
          setSessions(parsed);
          setActiveSessionId(parsed[0].id);
          return;
        }
      } catch (e) {
        console.error(e);
      }
    }

    const defaultSession: ChatSession = {
      id: "default-session",
      title: "General Workspace Chat",
      sessionId: "",
      messages: [
        {
          id: "welcome-msg",
          role: "assistant",
          content: "Hello! I am your NORAY AI Operating System. I can plan, reason, conduct deep research, and parse your profiles or scholarship guidelines. Ask me any goal!"
        }
      ]
    };
    setSessions([defaultSession]);
    setActiveSessionId(defaultSession.id);
  }

  function saveSessions(updated: ChatSession[]) {
    setSessions(updated);
    localStorage.setItem("noray-chat-sessions", JSON.stringify(updated));
  }

  function handleCreateNewSession() {
    const newSession: ChatSession = {
      id: Math.random().toString(36).substring(2, 9),
      title: `New Session #${sessions.length + 1}`,
      sessionId: "",
      messages: [
        {
          id: Math.random().toString(36).substring(2, 9),
          role: "assistant",
          content: "Hello! Starting a new session. How can I help you match jobs or refine your CV today?"
        }
      ]
    };
    const updated = [newSession, ...sessions];
    saveSessions(updated);
    setActiveSessionId(newSession.id);
  }

  function handleDeleteSession(id: string, e: React.MouseEvent) {
    e.stopPropagation();
    if (sessions.length <= 1) return;
    const updated = sessions.filter(s => s.id !== id);
    saveSessions(updated);
    if (activeSessionId === id) {
      setActiveSessionId(updated[0].id);
    }
  }

  // Resizing event handlers
  const handleMouseDown = () => {
    isResizingRef.current = true;
    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (!isResizingRef.current || !containerRef.current) return;
    const containerRect = containerRef.current.getBoundingClientRect();
    const newLeftWidth = ((e.clientX - containerRect.left) / containerRect.width) * 100;
    if (newLeftWidth > 25 && newLeftWidth < 75) {
      setLeftWidth(newLeftWidth);
    }
  };

  const handleMouseUp = () => {
    isResizingRef.current = false;
    document.removeEventListener("mousemove", handleMouseMove);
    document.removeEventListener("mouseup", handleMouseUp);
  };

  // Simulated word-by-word streaming effect
  function simulateStream(fullText: string, citations: any, explain: any) {
    let index = 0;
    setStreamingText("");
    const words = fullText.split(" ");
    
    const interval = setInterval(() => {
      if (index < words.length) {
        setStreamingText((prev) => prev + (index === 0 ? "" : " ") + words[index]);
        index++;
      } else {
        clearInterval(interval);
        
        // Save the finished message to the active session
        const assistantMsg: Message = {
          id: Math.random().toString(36).substring(2, 9),
          role: "assistant",
          content: fullText,
          citations,
          explainability: explain
        };

        const updated = sessions.map(s => {
          if (s.id === activeSessionId) {
            return {
              ...s,
              messages: [...s.messages, assistantMsg]
            };
          }
          return s;
        });
        saveSessions(updated);
        setStreamingText("");
        setChatLoading(false);
      }
    }, 35); // 35ms per word for high responsive feel
  }

  // Handle Chat submit
  async function handleChatSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || chatLoading || !activeSession) return;

    const userMsgText = input;
    setInput("");
    
    const userMsg: Message = {
      id: Math.random().toString(36).substring(2, 9),
      role: "user",
      content: userMsgText
    };

    // Add user message to session
    const currentSession = { ...activeSession, messages: [...activeSession.messages, userMsg] };
    const updatedWithUser = sessions.map(s => s.id === activeSessionId ? currentSession : s);
    setSessions(updatedWithUser);
    
    setChatLoading(true);

    try {
      const resp = await workspaceApi.chat({
        query: userMsgText,
        session_id: activeSession.sessionId || undefined
      });

      // Update sessionId on the session object
      if (resp.session_id && activeSession.sessionId !== resp.session_id) {
        currentSession.sessionId = resp.session_id;
      }

      // Auto title session based on first query
      if (currentSession.title.startsWith("New Session")) {
        currentSession.title = userMsgText.slice(0, 24) + (userMsgText.length > 24 ? "..." : "");
      }

      // Populate interactive Knowledge Graph dynamically from RAG reasoning details
      if (resp.explainability) {
        setSelectedExplain(resp.explainability);
        
        // Dynamically add entities from explainability to Knowledge Graph
        addExplainabilityToGraph(resp.explainability, userMsgText);
      }

      // Stream the assistant response
      simulateStream(resp.response, resp.citations, resp.explainability);

    } catch (err) {
      const errorMsg: Message = {
        id: Math.random().toString(36).substring(2, 9),
        role: "assistant",
        content: `Error connecting to assistant: ${err instanceof Error ? err.message : "Network failure"}`
      };
      const updatedWithError = sessions.map(s => {
        if (s.id === activeSessionId) {
          return { ...s, messages: [...s.messages, errorMsg] };
        }
        return s;
      });
      saveSessions(updatedWithError);
      setChatLoading(false);
    }
  }

  // Seed Knowledge Graph nodes
  function seedGraphFromDocs(docsList: any[]) {
    const nodes: GraphNode[] = [
      { id: "candidate-me", label: "Candidate (Self)", type: "candidate", x: 200, y: 200 },
      { id: "skills-node", label: "Python, Next.js, ML", type: "skill", x: 200, y: 100 },
    ];
    const edges: GraphEdge[] = [
      { source: "candidate-me", target: "skills-node", label: "POSSESSES" }
    ];

    docsList.forEach((doc, idx) => {
      const docId = `doc-${doc.id}`;
      const angle = (idx / Math.max(1, docsList.length)) * Math.PI * 2;
      const x = 200 + Math.cos(angle) * 120;
      const y = 200 + Math.sin(angle) * 120;
      
      nodes.push({
        id: docId,
        label: doc.source.length > 20 ? doc.source.slice(0, 17) + "..." : doc.source,
        type: "document",
        x,
        y
      });

      edges.push({
        source: "candidate-me",
        target: docId,
        label: "INGESTED"
      });
    });

    setGraphNodes(nodes);
    setGraphEdges(edges);
  }

  // Add search reasoning results to Graph RAG visualization dynamically
  function addExplainabilityToGraph(explain: any, query: string) {
    const updatedNodes = [...graphNodes];
    const updatedEdges = [...graphEdges];

    // Add query node
    const queryId = `query-${Math.random().toString(36).substring(2, 5)}`;
    updatedNodes.push({
      id: queryId,
      label: `Query: "${query.slice(0, 15)}..."`,
      type: "candidate",
      x: 350,
      y: 200
    });

    // Link query to Candidate self
    updatedEdges.push({
      source: queryId,
      target: "candidate-me",
      label: "ASKED_BY"
    });

    // Parse citation files as referenced nodes
    if (explain.retrieved_triples) {
      explain.retrieved_triples.forEach((triple: string, idx: number) => {
        // Split text triple like "(Mohamed, HAS_SKILL, AI)"
        const cleaned = triple.replace(/[()]/g, "");
        const parts = cleaned.split(",").map(p => p.trim());
        if (parts.length === 3) {
          const [subject, rel, object] = parts;
          const subId = `triple-node-${subject.toLowerCase().replace(/\s+/g, "-")}`;
          const objId = `triple-node-${object.toLowerCase().replace(/\s+/g, "-")}`;

          if (!updatedNodes.some(n => n.id === subId)) {
            updatedNodes.push({
              id: subId,
              label: subject,
              type: "candidate",
              x: 100 + Math.random() * 200,
              y: 100 + Math.random() * 200
            });
          }

          if (!updatedNodes.some(n => n.id === objId)) {
            updatedNodes.push({
              id: objId,
              label: object,
              type: "skill",
              x: 100 + Math.random() * 200,
              y: 100 + Math.random() * 200
            });
          }

          updatedEdges.push({
            source: subId,
            target: objId,
            label: rel
          });
        }
      });
    }

    setGraphNodes(updatedNodes);
    setGraphEdges(updatedEdges);
  }

  // Interactive Graph Zoom, Pan & Drag Handlers
  const handleGraphZoom = (direction: "in" | "out") => {
    setZoomLevel(prev => direction === "in" ? Math.min(prev + 0.15, 2.5) : Math.max(prev - 0.15, 0.4));
  };

  const handleGraphNodeMouseDown = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setDraggingNodeId(id);
  };

  const handleSvgMouseDown = (e: React.MouseEvent) => {
    if (draggingNodeId) return;
    setIsPanning(true);
    panStartRef.current = { x: e.clientX - panOffset.x, y: e.clientY - panOffset.y };
  };

  const handleSvgMouseMove = (e: React.MouseEvent) => {
    if (draggingNodeId) {
      // Update coordinates of dragged node relative to SVG viewbox
      const svgRect = svgRef.current?.getBoundingClientRect();
      if (svgRect) {
        // Simple scaling math
        const x = (e.clientX - svgRect.left - panOffset.x) / zoomLevel;
        const y = (e.clientY - svgRect.top - panOffset.y) / zoomLevel;
        
        setGraphNodes(prev => prev.map(n => n.id === draggingNodeId ? { ...n, x, y } : n));
      }
    } else if (isPanning) {
      setPanOffset({
        x: e.clientX - panStartRef.current.x,
        y: e.clientY - panStartRef.current.y
      });
    }
  };

  const handleSvgMouseUp = () => {
    setDraggingNodeId(null);
    setIsPanning(false);
  };

  // Node search highlight
  const highlightedNodeIds = useMemo(() => {
    if (!graphSearchQuery) return new Set<string>();
    return new Set(
      graphNodes
        .filter(n => n.label.toLowerCase().includes(graphSearchQuery.toLowerCase()))
        .map(n => n.id)
    );
  }, [graphNodes, graphSearchQuery]);

  // Deep Research Execution
  async function handleRunResearch(e: React.FormEvent) {
    e.preventDefault();
    if (!researchObjective.trim() || researchLoading) return;

    setResearchLoading(true);
    setResearchReport("");
    setResearchCitations([]);
    setResearchSteps(["Analyzing Research Objective...", "Triggering Deep web index query expansion..."]);
    
    try {
      const resp = await workspaceApi.research({
        objective: researchObjective,
        max_depth: researchDepth
      });
      setResearchReport(resp.report);
      setResearchCitations(resp.citations || []);
      setResearchSteps(resp.explainability?.reasoning_steps || ["Finished research extraction."]);
    } catch (err) {
      setResearchReport(`Research synthesis failed: ${err instanceof Error ? err.message : "Error"}`);
    } finally {
      setResearchLoading(false);
    }
  }

  // File Upload Handlers
  function handleDrag(e: React.DragEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }

  async function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      uploadFile(e.dataTransfer.files[0]);
    }
  }

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files && e.target.files[0]) {
      uploadFile(e.target.files[0]);
    }
  }

  async function uploadFile(file: File) {
    setUploading(true);
    try {
      await workspaceApi.uploadDoc(file, uploadCategory);
      await loadDocs();
    } catch (err) {
      alert(`Ingestion failed: ${err instanceof Error ? err.message : "Error"}`);
    } finally {
      setUploading(false);
    }
  }

  async function handleDeleteDoc(id: string) {
    if (!confirm("Are you sure you want to delete this document from the vector store?")) return;
    try {
      await workspaceApi.deleteDoc(id);
      setDocs(prev => prev.filter(d => d.id !== id));
      setGraphNodes(prev => prev.filter(n => n.id !== `doc-${id}`));
    } catch (err) {
      alert(`Delete failed: ${err instanceof Error ? err.message : "Error"}`);
    }
  }

  return (
    <PageTransition>
      <div className="flex flex-col h-[calc(100vh-100px)] bg-zinc-950 text-zinc-100">
        <PageHeader 
          title="AI Workspace Canvas" 
          description="Premium agentic RAG interface featuring interactive knowledge mapping, document ingestion, and deep research."
        />

        <div ref={containerRef} className="flex flex-1 overflow-hidden min-h-0 border border-zinc-800/80 rounded-2xl bg-zinc-900/10 backdrop-blur-md relative">
          
          {/* 1. Collapsible Sessions History sidebar (Leftmost) */}
          <AnimatePresence>
            {showHistory && (
              <motion.div
                initial={{ width: 0, opacity: 0 }}
                animate={{ width: 220, opacity: 1 }}
                exit={{ width: 0, opacity: 0 }}
                transition={{ duration: 0.25 }}
                className="border-r border-zinc-800/80 bg-zinc-950/70 flex flex-col shrink-0 overflow-hidden h-full"
              >
                <div className="p-3 border-b border-zinc-850 flex items-center justify-between shrink-0">
                  <span className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider">Conversations</span>
                  <button 
                    onClick={handleCreateNewSession}
                    className="flex h-5 w-5 items-center justify-center rounded border border-emerald-500/20 bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 transition"
                  >
                    <Plus size={12} />
                  </button>
                </div>
                
                {/* Session list items */}
                <div className="flex-1 overflow-y-auto p-2 space-y-1">
                  {sessions.map(s => {
                    const active = s.id === activeSessionId;
                    return (
                      <button
                        key={s.id}
                        onClick={() => {
                          setActiveSessionId(s.id);
                          // Auto set explainability if available in last message
                          const lastAssist = [...s.messages].reverse().find(m => m.role === "assistant");
                          setSelectedExplain(lastAssist?.explainability || null);
                        }}
                        className={`w-full text-left px-2.5 py-2 rounded-lg text-xs flex items-center justify-between gap-2 group transition ${
                          active
                            ? "bg-zinc-800 border border-zinc-700/60 text-emerald-400 font-semibold"
                            : "text-zinc-400 hover:bg-zinc-900/60 hover:text-zinc-200"
                        }`}
                      >
                        <span className="truncate flex-1">{s.title}</span>
                        {sessions.length > 1 && (
                          <span 
                            onClick={(e) => handleDeleteSession(s.id, e)}
                            className="opacity-0 group-hover:opacity-100 text-zinc-500 hover:text-red-400 p-0.5 shrink-0 transition"
                          >
                            <Trash2 size={11} />
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Button to toggle history drawer */}
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="absolute left-2 top-3 z-20 flex h-6 w-6 items-center justify-center rounded border border-zinc-800 bg-zinc-900/80 text-zinc-400 hover:text-zinc-200"
          >
            <MessageSquare size={13} />
          </button>

          {/* 2. Main Chat Panel (Left pane of split) */}
          <div 
            style={{ width: `${leftWidth}%` }}
            className="flex flex-col border-r border-zinc-800/80 bg-zinc-900/10 shrink-0 h-full relative"
          >
            <div className="p-3 pl-10 border-b border-zinc-800/80 bg-zinc-950/60 flex items-center justify-between shrink-0">
              <div className="flex items-center gap-2">
                <Sparkles className="text-emerald-400 animate-pulse" size={14} />
                <span className="text-xs font-bold text-zinc-300">Agentic Reasoning Thread</span>
              </div>
              {activeSession?.sessionId && (
                <Badge variant="success" className="font-mono text-[9px]">
                  SID: {activeSession.sessionId.slice(0, 6)}
                </Badge>
              )}
            </div>

            {/* Chat message list area */}
            <div className="flex-1 p-4 overflow-y-auto space-y-4">
              {activeSession?.messages.map((msg) => (
                <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[85%] rounded-xl p-3.5 text-xs leading-relaxed border ${
                    msg.role === "user" 
                      ? "bg-emerald-600 border-emerald-500/20 text-white rounded-br-none shadow-[0_2px_10px_-3px_rgba(16,185,129,0.2)]" 
                      : "bg-zinc-900 border-zinc-800 text-zinc-200 rounded-bl-none shadow-sm"
                  }`}>
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                    
                    {/* Citations block */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="mt-2.5 pt-2.5 border-t border-zinc-850">
                        <span className="text-[9px] font-bold text-zinc-500 block mb-1">Retrieval Citations:</span>
                        <div className="flex flex-wrap gap-1.5">
                          {msg.citations.map((c, idx) => (
                            <span key={idx} className="inline-flex items-center gap-1 text-[9px] px-2 py-0.5 rounded bg-zinc-950 border border-zinc-800 text-zinc-400">
                              <BookOpen size={10} className="text-zinc-500" />
                              {c.source}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Reasoning expand button */}
                    {msg.explainability && (
                      <div className="mt-2 pt-2 border-t border-zinc-850 flex justify-end">
                        <button
                          onClick={() => {
                            setSelectedExplain(msg.explainability);
                            setActiveRightTab("graph");
                          }}
                          className="text-[10px] text-emerald-400 hover:text-emerald-300 font-semibold flex items-center gap-1 transition"
                        >
                          <Info size={11} />
                          Inspect Planning DAG & Graph Relations
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {/* Streaming Assistant text */}
              {streamingText && (
                <div className="flex justify-start">
                  <div className="bg-zinc-900 border border-zinc-800 rounded-xl rounded-bl-none p-3.5 text-xs text-zinc-200 leading-relaxed max-w-[85%]">
                    <p className="whitespace-pre-wrap">{streamingText}</p>
                    <span className="inline-block w-1.5 h-3 bg-emerald-500 animate-pulse ml-0.5" />
                  </div>
                </div>
              )}

              {/* Loader */}
              {chatLoading && !streamingText && (
                <div className="flex justify-start">
                  <div className="bg-zinc-900 border border-zinc-800 rounded-xl rounded-bl-none p-3.5 flex items-center gap-2 text-zinc-400 text-xs">
                    <Loader2 className="animate-spin text-emerald-400" size={14} />
                    <span>Agent routing queries and expanding context nodes...</span>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Message input form */}
            <form onSubmit={handleChatSubmit} className="p-3 border-t border-zinc-800 bg-zinc-950/60 flex gap-2 shrink-0">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about DAAD requirements, matching jobs, or resume edits..."
                className="flex-1 px-4 py-2.5 text-xs bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-200 placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                disabled={chatLoading}
              />
              <Button type="submit" disabled={chatLoading || !input.trim()} className="px-4">
                <Send size={13} />
              </Button>
            </form>
          </div>

          {/* Resize Handle Divider */}
          <div 
            onMouseDown={handleMouseDown}
            className="resize-handle-horizontal shrink-0 self-stretch z-10"
          />

          {/* 3. Action tabs Column (Right pane of split) */}
          <div className="flex-1 flex flex-col bg-zinc-950/30 overflow-hidden h-full">
            
            {/* Tab Selector */}
            <div className="flex border-b border-zinc-800 bg-zinc-950/80 p-1 shrink-0">
              <button
                onClick={() => setActiveRightTab("ingest")}
                className={`flex-1 py-2 text-xs font-semibold rounded flex items-center justify-center gap-1.5 transition ${
                  activeRightTab === "ingest" 
                    ? "bg-zinc-800 text-emerald-400" 
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                <Database size={12} />
                <span>Ingestion</span>
              </button>
              
              <button
                onClick={() => setActiveRightTab("graph")}
                className={`flex-1 py-2 text-xs font-semibold rounded flex items-center justify-center gap-1.5 transition ${
                  activeRightTab === "graph" 
                    ? "bg-zinc-800 text-emerald-400" 
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                <Network size={12} />
                <span>Interactive Graph RAG</span>
              </button>
              
              <button
                onClick={() => setActiveRightTab("research")}
                className={`flex-1 py-2 text-xs font-semibold rounded flex items-center justify-center gap-1.5 transition ${
                  activeRightTab === "research" 
                    ? "bg-zinc-800 text-emerald-400" 
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                <Compass size={12} />
                <span>Deep Research</span>
              </button>
            </div>

            {/* Tab Body contents */}
            <div className="flex-1 p-4 overflow-y-auto min-h-0">
              
              {/* TAB 1: INGESTION ZONE */}
              {activeRightTab === "ingest" && (
                <div className="space-y-4">
                  <Card className="p-4 border-zinc-800 bg-zinc-900/40">
                    <h3 className="font-semibold text-xs flex items-center gap-2 mb-2 text-zinc-300">
                      <Upload size={14} className="text-zinc-500" />
                      <span>Ingest Document to Vector Store</span>
                    </h3>
                    <div className="flex items-center gap-2 mb-3">
                      <select
                        value={uploadCategory}
                        onChange={(e) => setUploadCategory(e.target.value)}
                        className="w-full px-2 py-1.5 text-xs bg-zinc-950 border border-zinc-850 rounded text-zinc-300 cursor-pointer focus:outline-none focus:ring-1 focus:ring-emerald-500"
                      >
                        <option value="general">General (Wiki / Knowledge)</option>
                        <option value="career">CVs & Career Profiles</option>
                        <option value="scholarship">Scholarship Guidelines</option>
                      </select>
                    </div>

                    <div 
                      onDragEnter={handleDrag}
                      onDragOver={handleDrag}
                      onDragLeave={handleDrag}
                      onDrop={handleDrop}
                      onClick={() => fileInputRef.current?.click()}
                      className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-all ${
                        dragActive 
                          ? "border-emerald-500 bg-emerald-950/20" 
                          : "border-zinc-800 hover:border-zinc-700"
                      }`}
                    >
                      <input 
                        ref={fileInputRef}
                        type="file" 
                        onChange={handleFileSelect} 
                        className="hidden"
                        accept=".pdf,.docx,.txt,.md"
                      />
                      {uploading ? (
                        <div className="flex flex-col items-center gap-2 text-xs text-zinc-500">
                          <Loader2 className="animate-spin text-emerald-400" size={24} />
                          <span>Chunking and running embedding index pipelines...</span>
                        </div>
                      ) : (
                        <div className="flex flex-col items-center gap-1.5 text-xs text-zinc-400">
                          <Paperclip size={20} className="text-zinc-500" />
                          <span className="font-medium text-zinc-300">Select or drop file namespace</span>
                          <span className="text-[10px] text-zinc-500">PDF, Word, Text, Markdown (max 10MB)</span>
                        </div>
                      )}
                    </div>
                  </Card>

                  {/* List of processed documents namespace */}
                  <Card className="p-4 border-zinc-800 bg-zinc-900/40">
                    <span className="text-xs font-semibold text-zinc-400 block mb-2">Processed Chunks ({docs.length})</span>
                    <div className="space-y-1.5 max-h-[260px] overflow-y-auto pr-1">
                      {docs.map((doc, idx) => (
                        <div key={idx} className="flex justify-between items-center gap-2 p-2 border border-zinc-850 rounded bg-zinc-950/60 text-[10px]">
                          <div className="flex items-center gap-1.5 min-w-0">
                            <FileCheck size={12} className="text-emerald-500 shrink-0" />
                            <span className="truncate text-zinc-300">{doc.source}</span>
                            <span className="text-[8px] text-zinc-500 px-1 py-0.5 rounded bg-zinc-900">{doc.category}</span>
                          </div>
                          <button 
                            onClick={() => handleDeleteDoc(doc.id)}
                            className="text-zinc-500 hover:text-red-400 p-1 transition"
                          >
                            <Trash2 size={12} />
                          </button>
                        </div>
                      ))}
                      {docs.length === 0 && (
                        <p className="text-center text-[10px] text-zinc-500 py-4">No documents indexed yet.</p>
                      )}
                    </div>
                  </Card>
                </div>
              )}

              {/* TAB 2: INTERACTIVE KNOWLEDGE GRAPH RAG */}
              {activeRightTab === "graph" && (
                <div className="space-y-4 h-full flex flex-col min-h-0">
                  
                  {/* Confidence Summary & Details Panel */}
                  <div className="grid grid-cols-2 gap-3 shrink-0">
                    <Card className="p-3 border-zinc-800 bg-zinc-900/40 flex items-center justify-between">
                      <span className="text-[10px] font-semibold text-zinc-400">Grounding Confidence</span>
                      <span className="font-mono text-sm font-bold text-emerald-400">
                        {selectedExplain ? `${(selectedExplain.confidence_score * 100).toFixed(0)}%` : "0%"}
                      </span>
                    </Card>
                    <Card className="p-3 border-zinc-800 bg-zinc-900/40 flex items-center justify-between">
                      <span className="text-[10px] font-semibold text-zinc-400">Triples Traversed</span>
                      <span className="font-mono text-sm font-bold text-emerald-400">
                        {selectedExplain?.retrieved_triples?.length ?? 0}
                      </span>
                    </Card>
                  </div>

                  {/* Interactive SVG Diagram Controls */}
                  <Card className="p-4 border-zinc-800 bg-zinc-900/40 flex-1 flex flex-col min-h-[300px] relative overflow-hidden">
                    <div className="flex justify-between items-center gap-2 mb-3 shrink-0">
                      <div className="relative flex-1">
                        <Search className="absolute left-2 top-2 text-zinc-500" size={12} />
                        <input
                          type="text"
                          value={graphSearchQuery}
                          onChange={(e) => setGraphSearchQuery(e.target.value)}
                          placeholder="Search nodes..."
                          className="w-full pl-7 pr-3 py-1 bg-zinc-950 border border-zinc-800 rounded text-[10px] text-zinc-200 focus:outline-none"
                        />
                      </div>
                      
                      {/* Zoom Controls */}
                      <div className="flex gap-1 shrink-0">
                        <button 
                          onClick={() => handleGraphZoom("out")} 
                          className="px-2 py-1 bg-zinc-950 border border-zinc-800 text-[10px] rounded hover:border-zinc-700"
                        >
                          -
                        </button>
                        <button 
                          onClick={() => handleGraphZoom("in")} 
                          className="px-2 py-1 bg-zinc-950 border border-zinc-800 text-[10px] rounded hover:border-zinc-700"
                        >
                          +
                        </button>
                        <button 
                          onClick={() => { setZoomLevel(1); setPanOffset({ x: 0, y: 0 }); }} 
                          className="px-2 py-1 bg-zinc-950 border border-zinc-800 text-[10px] rounded hover:border-zinc-700"
                        >
                          Reset
                        </button>
                      </div>
                    </div>

                    {/* Interactive SVG Graph Area */}
                    <div className="flex-1 border border-zinc-950 rounded-lg bg-zinc-950/60 overflow-hidden relative">
                      <svg
                        ref={svgRef}
                        width="100%"
                        height="100%"
                        className="cursor-grab active:cursor-grabbing"
                        onMouseDown={handleSvgMouseDown}
                        onMouseMove={handleSvgMouseMove}
                        onMouseUp={handleSvgMouseUp}
                        onMouseLeave={handleSvgMouseUp}
                      >
                        {/* Define SVG marker arrows */}
                        <defs>
                          <marker
                            id="arrow"
                            viewBox="0 0 10 10"
                            refX="18"
                            refY="5"
                            markerWidth="6"
                            markerHeight="6"
                            orient="auto-start-reverse"
                          >
                            <path d="M 0 0 L 10 5 L 0 10 z" fill="#27272a" />
                          </marker>
                        </defs>

                        {/* Transformed Group containing nodes & links */}
                        <g transform={`translate(${panOffset.x}, ${panOffset.y}) scale(${zoomLevel})`}>
                          
                          {/* 1. Draw Links */}
                          {graphEdges.map((edge, idx) => {
                            const sourceNode = graphNodes.find(n => n.id === edge.source);
                            const targetNode = graphNodes.find(n => n.id === edge.target);
                            if (!sourceNode || !targetNode) return null;

                            return (
                              <g key={idx}>
                                <line
                                  x1={sourceNode.x}
                                  y1={sourceNode.y}
                                  x2={targetNode.x}
                                  y2={targetNode.y}
                                  stroke="#27272a"
                                  strokeWidth="1.5"
                                  strokeDasharray="4, 4"
                                  className="animate-[stroke-dash_5s_linear_infinite]"
                                  markerEnd="url(#arrow)"
                                />
                                <text
                                  x={(sourceNode.x + targetNode.x) / 2}
                                  y={(sourceNode.y + targetNode.y) / 2 - 4}
                                  fill="#52525b"
                                  fontSize="7"
                                  fontFamily="monospace"
                                  textAnchor="middle"
                                >
                                  {edge.label}
                                </text>
                              </g>
                            );
                          })}

                          {/* 2. Draw Nodes */}
                          {graphNodes.map((node) => {
                            const isHighlighted = highlightedNodeIds.has(node.id);
                            const isSelected = selectedGraphNode?.id === node.id;
                            
                            // Define color mapping per node type
                            const nodeColor = 
                              node.type === "candidate" ? "#10b981" : // emerald
                              node.type === "document" ? "#3b82f6" :  // blue
                              node.type === "skill" ? "#8b5cf6" :     // purple
                              "#f59e0b";                             // amber

                            return (
                              <g
                                key={node.id}
                                transform={`translate(${node.x}, ${node.y})`}
                                onMouseDown={(e) => handleGraphNodeMouseDown(node.id, e)}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setSelectedGraphNode(node);
                                }}
                                className="cursor-pointer group"
                              >
                                {/* Highlight ring */}
                                {(isHighlighted || isSelected) && (
                                  <circle
                                    r="15"
                                    fill="none"
                                    stroke={isHighlighted ? "#fbbf24" : "#10b981"}
                                    strokeWidth="1.5"
                                    className={isHighlighted ? "animate-pulse" : ""}
                                  />
                                )}
                                
                                <circle
                                  r="9"
                                  fill={nodeColor}
                                  stroke="#09090b"
                                  strokeWidth="1.5"
                                />

                                {/* Label text */}
                                <text
                                  y="18"
                                  fill="#d4d4d8"
                                  fontSize="7"
                                  fontWeight="semibold"
                                  textAnchor="middle"
                                  className="pointer-events-none group-hover:fill-white transition"
                                >
                                  {node.label}
                                </text>
                              </g>
                            );
                          })}

                        </g>
                      </svg>

                      {/* Floating reset overlay info */}
                      <span className="absolute bottom-2 left-2 text-[8px] text-zinc-500 font-mono pointer-events-none">
                        Drag nodes. Drag canvas to pan. Scroll or use controls to zoom.
                      </span>
                    </div>

                    {/* Node Inspect details bottom tray */}
                    <AnimatePresence>
                      {selectedGraphNode && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="mt-3 p-2.5 border border-zinc-800 bg-zinc-950 rounded-lg text-[10px] shrink-0"
                        >
                          <div className="flex justify-between items-center mb-1">
                            <span className="font-bold text-zinc-200 capitalize">Entity Details ({selectedGraphNode.type})</span>
                            <button 
                              onClick={() => setSelectedGraphNode(null)}
                              className="text-zinc-500 hover:text-zinc-300"
                            >
                              Close
                            </button>
                          </div>
                          <p className="font-mono text-emerald-400">ID: {selectedGraphNode.id}</p>
                          <p className="text-zinc-400 mt-0.5">Label: {selectedGraphNode.label}</p>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </Card>

                  {/* Planning DAG timeline progress step lists */}
                  {selectedExplain && (
                    <Card className="p-4 border-zinc-800 bg-zinc-900/40 shrink-0">
                      <h4 className="text-[10px] font-bold uppercase tracking-wider text-zinc-400 mb-2 flex items-center gap-1.5">
                        <Cpu size={12} className="text-emerald-400" />
                        <span>Executed Planning DAG Timeline</span>
                      </h4>
                      <div className="space-y-1.5 max-h-[160px] overflow-y-auto">
                        {selectedExplain.reasoning_steps?.map((step: string, idx: number) => (
                          <div key={idx} className="flex items-start gap-2 text-[10px] text-zinc-300">
                            <span className="text-emerald-500 shrink-0">✓</span>
                            <span>{step}</span>
                          </div>
                        ))}
                      </div>
                    </Card>
                  )}

                </div>
              )}

              {/* TAB 3: DEEP RESEARCH Objective Panel */}
              {activeRightTab === "research" && (
                <div className="space-y-4">
                  <Card className="p-4 border-zinc-800 bg-zinc-900/40">
                    <h3 className="font-semibold text-xs flex items-center gap-2 mb-2 text-zinc-300">
                      <Compass size={14} className="text-emerald-400" />
                      <span>Run Deep Research Objective</span>
                    </h3>
                    <form onSubmit={handleRunResearch} className="space-y-3">
                      <textarea
                        value={researchObjective}
                        onChange={(e) => setResearchObjective(e.target.value)}
                        placeholder="e.g., Gather all eligibility criteria and deadlines for PhD funding in Europe, then draft a recommendation report."
                        rows={3}
                        className="w-full p-2.5 text-xs bg-zinc-950 border border-zinc-850 rounded text-zinc-200 placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                      />
                      
                      <div className="flex justify-between items-center text-xs">
                        <span className="text-zinc-500">Search Iteration Depth:</span>
                        <select
                          value={researchDepth}
                          onChange={(e) => setResearchDepth(Number(e.target.value))}
                          className="px-2 py-1 bg-zinc-950 border border-zinc-850 rounded text-zinc-300 cursor-pointer"
                        >
                          <option value="1">Level 1 (Fast)</option>
                          <option value="2">Level 2 (Normal)</option>
                          <option value="3">Level 3 (Deep)</option>
                        </select>
                      </div>

                      <Button 
                        type="submit" 
                        disabled={researchLoading || !researchObjective.trim()} 
                        className="w-full"
                      >
                        {researchLoading ? (
                          <span className="flex items-center justify-center gap-1.5">
                            <Loader2 className="animate-spin" size={13} />
                            Researching Web & Docs...
                          </span>
                        ) : "Launch Research Agent"}
                      </Button>
                    </form>
                  </Card>

                  {/* Progressive logs */}
                  {researchSteps.length > 0 && (
                    <Card className="p-3 border-zinc-800 bg-zinc-900/40 text-xs">
                      <span className="font-bold text-zinc-400 block mb-2 uppercase tracking-wide text-[10px]">Research Log Steps</span>
                      <div className="space-y-2">
                        {researchSteps.map((step, idx) => (
                          <div key={idx} className="flex items-start gap-2 text-[10px] text-zinc-300 leading-normal">
                            <span className="text-emerald-500">●</span>
                            <span>{step}</span>
                          </div>
                        ))}
                      </div>
                    </Card>
                  )}

                  {/* Research Output Report */}
                  {researchReport && (
                    <Card className="p-4 border-zinc-850 bg-zinc-950 max-h-[350px] overflow-y-auto">
                      <div className="flex justify-between items-center mb-3 pb-2 border-b border-zinc-850">
                        <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Research Output Synthesis</span>
                        <Button 
                          variant="ghost"
                          onClick={() => {
                            navigator.clipboard.writeText(researchReport);
                            alert("Report copied to clipboard.");
                          }}
                          className="text-[9px] p-1 h-auto text-zinc-400 hover:text-zinc-200"
                        >
                          Copy Report
                        </Button>
                      </div>
                      <div className="text-xs text-zinc-300 leading-relaxed whitespace-pre-wrap">
                        {researchReport}
                      </div>
                    </Card>
                  )}
                </div>
              )}

            </div>
          </div>

        </div>
      </div>
    </PageTransition>
  );
}
