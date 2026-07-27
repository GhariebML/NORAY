/**
 * NORAY API Client
 *
 * Thin wrapper around fetch for the NORAY FastAPI backend.
 */

// Bypass Next.js proxy on frontend to avoid socket timeouts with local LLMs
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

// ─── Smart Router API types ──────────────────────────────────

export interface SmartRouterStatus {
  status: {
    mode: string;
    current_provider: string;
    current_model: string;
    mode_label: string;
    is_local: boolean;
    offline_mode: boolean;
    monitoring_active: boolean;
    warm_up_completed: boolean;
    enabled_providers: string[];
  };
  health: Record<string, {
    name: string;
    healthy: boolean;
    status: string;
    circuit_state: string;
    latency_ms: number;
    last_error: string;
    uptime_percentage: number;
  }>;
  active_provider: string;
  active_model: string;
  offline_mode: boolean;
  local_models: Array<{
    name: string;
    size_gb: number;
    family: string;
    parameter_size: string;
  }>;
  local_ollama_running: boolean;
}

export interface ProviderAnalyticsData {
  providers: Record<string, {
    provider: string;
    total_requests: number;
    successful_requests: number;
    failed_requests: number;
    success_rate: number;
    total_tokens_input: number;
    total_tokens_output: number;
    total_estimated_cost: number;
    average_latency_ms: number;
    tokens_per_second: number;
    last_error: string;
  }>;
  aggregated: {
    total_requests: number;
    total_successful: number;
    total_failed: number;
    overall_success_rate: number;
    total_estimated_cost: number;
    total_tokens: number;
    active_providers: number;
    total_providers: number;
  };
}

export const smartRouterApi = {
  getStatus: () => request<SmartRouterStatus>("/api/ai/status"),
  getProviders: () => request<{ providers: any[] }>("/api/ai/providers"),
  setMode: (mode: string) =>
    request<{ status: string; mode: string }>("/api/ai/mode", {
      method: "POST",
      body: JSON.stringify({ mode }),
    }),
  toggleProvider: (provider: string, enabled: boolean) =>
    request<{ status: string; provider: string; enabled: boolean }>("/api/ai/toggle-provider", {
      method: "POST",
      body: JSON.stringify({ provider, enabled }),
    }),
  setPreferredModel: (model: string) =>
    request<{ status: string; model: string }>("/api/ai/preferred-model", {
      method: "POST",
      body: JSON.stringify({ model }),
    }),
  getAnalytics: () => request<ProviderAnalyticsData>("/api/ai/analytics"),
  setOfflineMode: (enabled: boolean) =>
    request<{ status: string; offline_mode: boolean; message: string }>("/api/ai/offline-mode", {
      method: "POST",
      body: JSON.stringify({ enabled }),
    }),
  getRoutingDecision: (query: string = "", context: string = "") =>
    request<any>(`/api/ai/routing-decision?query=${encodeURIComponent(query)}&context=${encodeURIComponent(context)}`),
};

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const errorBody = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${errorBody || res.statusText}`);
  }

  return res.json();
}

// ─── Profile ──────────────────────────────────────────────────

export const profileApi = {
  get: () => request<{ profile: Record<string, unknown>; meta: Record<string, unknown> }>("/api/profile"),
  update: (updates: Record<string, unknown>) =>
    request<{ profile: Record<string, unknown>; message: string }>("/api/profile", {
      method: "PUT",
      body: JSON.stringify({ updates, source: "web" }),
    }),
  importGithub: (username: string) =>
    request<{ message: string; repos_found: number; username: string }>("/api/profile/import/github", {
      method: "POST",
      body: JSON.stringify({ username }),
    }),
  importCv: async (file: File) => {
    const form = new FormData();
    form.append("file", file);
    const url = `${typeof window !== "undefined" ? "" : API_BASE}/api/profile/import/cv`;
    const res = await fetch(url, {
      method: "POST",
      body: form,
    });
    if (!res.ok) {
      const errorBody = await res.text().catch(() => "");
      throw new Error(`API ${res.status}: ${errorBody || res.statusText}`);
    }
    return res.json() as Promise<{ message: string; status: string; data: Record<string, unknown> }>;
  },
};

// ─── Jobs ─────────────────────────────────────────────────────

export interface Job {
  id?: string;
  title: string;
  company: string;
  location?: string;
  url?: string;
  fit_score?: number;
  match_reasons?: string[];
  missing_skills?: string[];
  status?: string;
  applied_date?: string;
  source?: string;
}

export const jobsApi = {
  search: (params: { focus_area?: string; broad?: boolean } = {}) =>
    request<{ jobs: Job[]; total_found: number; new_count: number }>("/api/jobs/search", {
      method: "POST",
      body: JSON.stringify(params),
    }),
  aiSearch: (params: { query: string; max_results?: number }) =>
    request<{
      query: string;
      parsed_intent: any;
      total_found: number;
      jobs: AIJobResult[];
      search_time_seconds: number;
    }>("/api/jobs/ai-search", {
      method: "POST",
      body: JSON.stringify(params),
    }),
  parseIntent: (query: string) =>
    request<{ status: string; intent: any }>("/api/jobs/parse-intent", {
      method: "POST",
      body: JSON.stringify({ query }),
    }),
  aiScore: (params: { company: string; role: string; country?: string; description?: string }) =>
    request<{ status: string; score: AIJobScore }>("/api/jobs/ai-score", {
      method: "POST",
      body: JSON.stringify(params),
    }),
  evaluate: (params: { job_url?: string; job_text?: string }) =>
    request<{ score: number; report: Record<string, unknown> }>("/api/jobs/evaluate", {
      method: "POST",
      body: JSON.stringify(params),
    }),
  apply: (params: {
    job_url?: string;
    job_text?: string;
    company: string;
    role?: string;
    generate_cv?: boolean;
    generate_cover_letter?: boolean;
  }) =>
    request<{ message: string; cv_path?: string; cover_letter_path?: string }>("/api/jobs/apply", {
      method: "POST",
      body: JSON.stringify(params),
    }),
  tracker: () =>
    request<{ applications: Job[]; stats: Record<string, unknown> }>("/api/jobs/tracker"),
};

export interface AIJobScore {
  overall_match: number;
  skill_match: number;
  role_alignment: number;
  ats_estimate: number;
  strengths: string[];
  gaps: string[];
  missing_skills: string[];
  recommendation: string;
  summary: string;
}

export interface AIJobResult {
  company: string;
  role: string;
  country: string;
  remote: boolean;
  salary: string;
  required_skills: string[];
  experience: string;
  description: string;
  apply_url: string;
  source: string;
  score: AIJobScore;
}

// ─── Scholarships ─────────────────────────────────────────────

export interface Scholarship {
  id?: string;
  name: string;
  portal: string;
  country?: string;
  degree_level?: string;
  amount?: string;
  deadline?: string;
  url?: string;
  eligibility_score?: number;
  match_reasons?: string[];
  status?: string;
}

export const scholarshipsApi = {
  search: (params: { target_degree?: string; target_country?: string; research_area?: string } = {}) =>
    request<{ scholarships: Scholarship[]; total_found: number }>("/api/scholarships/search", {
      method: "POST",
      body: JSON.stringify(params),
    }),
  aiSearch: (params: { query: string }) =>
    request<{
      query: string;
      parsed_intent: any;
      total_found: number;
      scholarships: AIScholarshipResult[];
      search_time_seconds: number;
    }>("/api/scholarships/ai-search", {
      method: "POST",
      body: JSON.stringify(params),
    }),
  parseIntent: (query: string) =>
    request<{ status: string; intent: any }>("/api/scholarships/parse-intent", {
      method: "POST",
      body: JSON.stringify({ query }),
    }),
  aiEligibility: (params: {
    name: string; provider?: string; country?: string;
    degree_level?: string; funding?: string; description?: string;
  }) =>
    request<{ status: string; eligibility: AIScholarshipEligibility }>("/api/scholarships/ai-eligibility", {
      method: "POST",
      body: JSON.stringify(params),
    }),
  apply: (params: {
    scholarship_info: string;
    scholarship_name: string;
    generate_sop?: boolean;
    generate_motivation?: boolean;
    generate_research_proposal?: boolean;
  }) =>
    request<{ message: string; sop?: string; motivation?: string; research_proposal?: string }>("/api/scholarships/apply", {
      method: "POST",
      body: JSON.stringify(params),
    }),
  tracker: () =>
    request<{ applications: Scholarship[]; stats: Record<string, unknown> }>("/api/scholarships/tracker"),
  deadlines: () =>
    request<{ upcoming: Scholarship[]; past: Scholarship[] }>("/api/scholarships/deadlines"),
};

export interface AIScholarshipEligibility {
  eligibility_score: number;
  why_eligible: string[];
  missing_documents: string[];
  recommended_timeline: string;
  competition_level: string;
  acceptance_difficulty: string;
  recommendation: string;
  summary: string;
}

export interface AIScholarshipResult {
  name: string;
  provider: string;
  country: string;
  university: string;
  degree_level: string;
  funding: string;
  deadline: string;
  requirements: string[];
  language: string;
  research_areas: string[];
  official_url: string;
  eligibility: AIScholarshipEligibility;
}

// ─── Documents (CV, SOP, etc.) ────────────────────────────────

export const documentsApi = {
  generateCv: (params: { job_url?: string; job_text?: string; company: string; role?: string }) =>
    request<{ message: string; cv_path: string }>("/api/cv/generate", {
      method: "POST",
      body: JSON.stringify(params),
    }),
  generate: (params: {
    doc_type: string;
    target: string;
    context?: string;
    session_id?: string;
    run_quality_check?: boolean;
  }) =>
    request<{
      doc_type: string;
      content: string;
      length: number;
      quality: {
        ats_score: number;
        grammar_score: number;
        keyword_coverage: number;
        readability_score: number;
        hallucination_risk: string;
        formatting_issues: string[];
        consistency_issues: string[];
        suggestions: string[];
        overall_quality: string;
      };
    }>("/api/cv/generate", {
      method: "POST",
      body: JSON.stringify(params),
    }),
  generateSop: (params: {
    scholarship_name?: string;
    university?: string;
    program?: string;
    research_interests?: string;
    word_limit?: number;
    context?: string;
  }) =>
    request<{ doc_type: string; content: string; length: number; quality: any }>("/api/cv/sop", {
      method: "POST",
      body: JSON.stringify(params),
    }),
  generateMotivation: (params: {
    scholarship_name?: string;
    program?: string;
    word_limit?: number;
    context?: string;
  }) =>
    request<{ doc_type: string; content: string; length: number; quality: any }>("/api/cv/motivation", {
      method: "POST",
      body: JSON.stringify(params),
    }),
  generateResearch: (params: {
    scholarship_name?: string;
    university?: string;
    program?: string;
    research_topics?: string;
    word_limit?: number;
    context?: string;
  }) =>
    request<{ doc_type: string; content: string; length: number; quality: any }>("/api/cv/research", {
      method: "POST",
      body: JSON.stringify(params),
    }),
  generateEmail: (params: { target: string; context?: string }) =>
    request<{ content: string; length: number }>("/api/cv/email", {
      method: "POST",
      body: JSON.stringify(params),
    }),
  generateLinkedin: (params: { target: string; context?: string }) =>
    request<{ content: string; length: number }>("/api/cv/linkedin", {
      method: "POST",
      body: JSON.stringify(params),
    }),
  checkQuality: (params: { target: string; doc_type?: string }) =>
    request<{ status: string; report: any }>("/api/cv/quality", {
      method: "POST",
      body: JSON.stringify(params),
    }),
  optimizeCv: (params: { cv_text: string; job_keywords?: string[] }) =>
    request<{ optimized: string; score: number }>("/api/cv/optimize", {
      method: "POST",
      body: JSON.stringify(params),
    }),
};

// ─── Applications ─────────────────────────────────────────────

export interface Application {
  id: string;
  type: "job" | "scholarship";
  title: string;
  organization: string;
  status: string;
  applied_date?: string;
  deadline?: string;
  priority?: string;
  notes?: string;
}

export const applicationsApi = {
  list: (params: { type?: string; status?: string } = {}) => {
    const searchParams = new URLSearchParams();
    if (params.type) searchParams.set("type", params.type);
    if (params.status) searchParams.set("status", params.status);
    const qs = searchParams.toString();
    return request<{ applications: Application[]; stats: Record<string, unknown> }>(
      `/api/applications${qs ? `?${qs}` : ""}`
    );
  },
  analytics: () =>
    request<Record<string, unknown>>("/api/applications/analytics"),
};

// ─── Upskill ──────────────────────────────────────────────────

export interface SkillGap {
  skill: string;
  category: string;
  priority: string;
  frequency: number;
  estimated_hours?: number;
  study_direction?: string;
}

export interface RoadmapPhase {
  phase: string;
  duration: string;
  milestones: { title: string; type: string; description: string }[];
}

export const upskillApi = {
  analyze: (params: { job_url?: string; job_text?: string; mode?: string }) =>
    request<{ gaps: SkillGap[]; learning_plan: Record<string, unknown>[]; recommendations: string[] }>(
      "/api/upskill/analyze",
      { method: "POST", body: JSON.stringify(params) }
    ),
  roadmap: (params: { timeline_months?: number; target_roles?: string[] } = {}) =>
    request<{ roadmap: RoadmapPhase[]; summary: string }>("/api/upskill/roadmap", {
      method: "POST",
      body: JSON.stringify(params),
    }),
  resources: (params: { skills?: string[]; format?: string }) =>
    request<{ resources: Record<string, unknown>[]; study_order: string[] }>("/api/upskill/resources", {
      method: "POST",
      body: JSON.stringify(params),
    }),
};

// ─── Workspace & Search ───────────────────────────────────────

export interface Citation {
  id: string;
  source: string;
  score: number;
  content?: string;
}

export interface ChatResponse {
  session_id: string;
  intent: string;
  response: string;
  citations: Citation[];
}

export interface SearchResult {
  id: string;
  score: number;
  content: string;
  payload: Record<string, any>;
}

export const workspaceApi = {
  chat: (params: { query: string; session_id?: string; temperature?: number }) =>
    request<ChatResponse & { explainability?: any }>("/api/workspace/chat", {
      method: "POST",
      body: JSON.stringify(params),
    }),
  search: (params: { query: string; limit?: number; filters?: Record<string, any> }) =>
    request<{ query: string; results: SearchResult[] }>("/api/workspace/search", {
      method: "POST",
      body: JSON.stringify(params),
    }),
  research: (params: { objective: string; max_depth?: number }) =>
    request<{
      session_id: string;
      objective: string;
      status: string;
      report: string;
      citations: any[];
      explainability: any;
    }>("/api/workspace/research", {
      method: "POST",
      body: JSON.stringify(params),
    }),
  uploadDoc: async (file: File, category: string = "general") => {
    const form = new FormData();
    form.append("file", file);
    form.append("category", category);
    const url = `${typeof window !== "undefined" ? "" : API_BASE}/api/documents/upload`;
    const res = await fetch(url, {
      method: "POST",
      body: form,
    });
    if (!res.ok) {
      const errorText = await res.text().catch(() => "");
      let parsedDetail = "";
      try {
        const jsonErr = JSON.parse(errorText);
        parsedDetail =
          typeof jsonErr.detail === "string"
            ? jsonErr.detail
            : jsonErr.detail?.detail || jsonErr.detail?.error || jsonErr.error || errorText;
      } catch {
        parsedDetail = errorText || res.statusText;
      }
      throw new Error(parsedDetail);
    }
    return res.json() as Promise<{ filename: string; chunks_count: number; strategy: string; category: string }>;
  },
  listDocs: () =>
    request<
      {
        id: string;
        source: string;
        category: string;
        content: string;
        doc_type?: string;
        summary?: string;
        keywords?: string[];
        chunks_count?: number;
        created_at?: string;
      }[]
    >("/api/documents/list"),
  getDocDetails: (id: string) =>
    request<{
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
    }>(`/api/documents/${id}`),
  reindexDoc: (id: string, category: string = "general") =>
    request<{ status: string; id: string; category: string }>("/api/documents/reindex", {
      method: "POST",
      body: JSON.stringify({ id, category }),
    }),
  deleteDoc: (id: string) =>
    request<{ status: string; id: string }>(`/api/documents/${id}`, {
      method: "DELETE",
    }),
  getGraphTriples: (limit?: number) =>
    request<{ triples: { source: string; relation: string; target: string }[]; nodes: string[] }>(
      `/api/workspace/graph/triples${limit ? `?limit=${limit}` : ""}`
    ),
};
