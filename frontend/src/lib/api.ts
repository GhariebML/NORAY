/**
 * NORAY API Client
 *
 * Thin wrapper around fetch for the NORAY FastAPI backend.
 */

// Bypass Next.js proxy on frontend to avoid socket timeouts with local LLMs
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

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

// ─── Documents (CV, SOP, etc.) ────────────────────────────────

export const documentsApi = {
  generateCv: (params: { job_url?: string; job_text?: string; company: string; role?: string }) =>
    request<{ message: string; cv_path: string }>("/api/cv/generate", {
      method: "POST",
      body: JSON.stringify(params),
    }),
  optimizeCv: (params: { cv_text: string; job_keywords?: string[] }) =>
    request<{ optimized: string; score: number }>("/api/cv/optimize", {
      method: "POST",
      body: JSON.stringify(params),
    }),
  generateSop: (params: { scholarship_info: string; research_interests?: string[]; word_limit?: number }) =>
    request<{ sop: string; word_count: number }>("/api/sop/sop", {
      method: "POST",
      body: JSON.stringify(params),
    }),
  generateMotivation: (params: { scholarship_info: string; word_limit?: number }) =>
    request<{ motivation: string; word_count: number }>("/api/sop/motivation", {
      method: "POST",
      body: JSON.stringify(params),
    }),
  generateResearch: (params: { scholarship_info: string; research_interests?: string[]; word_limit?: number }) =>
    request<{ research_proposal: string; word_count: number }>("/api/sop/research", {
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
      const errorBody = await res.text().catch(() => "");
      throw new Error(`API ${res.status}: ${errorBody || res.statusText}`);
    }
    return res.json() as Promise<{ filename: string; chunks_count: number; strategy: string; category: string }>;
  },
  listDocs: () =>
    request<{ id: string; source: string; category: string; content: string }[]>("/api/documents/list"),
  deleteDoc: (id: string) =>
    request<{ status: string; id: string }>(`/api/documents/${id}`, {
      method: "DELETE",
    }),
};
