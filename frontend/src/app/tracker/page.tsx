"use client";

import { useEffect, useState } from "react";
import {
  ClipboardList,
  Briefcase,
  GraduationCap,
  Filter,
  Loader2,
} from "lucide-react";
import { PageHeader, Card, Button, Badge, LoadingSpinner, EmptyState } from "@/components/ui";
import { applicationsApi, type Application } from "@/lib/api";

const STATUS_OPTIONS = [
  "all",
  "discovered",
  "preparing",
  "submitted",
  "interview",
  "shortlisted",
  "awarded",
  "accepted",
  "rejected",
];

const STATUS_VARIANT: Record<string, "default" | "success" | "warning" | "danger" | "info"> = {
  discovered: "default",
  preparing: "info",
  submitted: "warning",
  interview: "info",
  shortlisted: "info",
  awarded: "success",
  accepted: "success",
  rejected: "danger",
};

export default function TrackerPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState<"all" | "job" | "scholarship">("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [stats, setStats] = useState<Record<string, unknown>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadApplications();
  }, [typeFilter, statusFilter]);

  async function loadApplications() {
    try {
      setLoading(true);
      setError(null);
      const params: Record<string, string> = {};
      if (typeFilter !== "all") params.type = typeFilter;
      if (statusFilter !== "all") params.status = statusFilter;
      const data = await applicationsApi.list(params);
      setApplications(data.applications || []);
      setStats(data.stats || {});
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load applications");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Application Tracker"
        description="Unified view of all your job and scholarship applications"
      >
        <Button onClick={loadApplications} variant="secondary">
          Refresh
        </Button>
      </PageHeader>

      {/* Filters */}
      <Card className="mb-6 p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter size={16} className="text-zinc-400" />
            <span className="text-sm font-medium text-zinc-500">Filters:</span>
          </div>

          <div className="flex gap-1.5">
            {(["all", "job", "scholarship"] as const).map((type) => (
              <button
                key={type}
                onClick={() => setTypeFilter(type)}
                className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                  typeFilter === type
                    ? "bg-emerald-600 text-white"
                    : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-700"
                }`}
              >
                {type === "all" ? "All" : type === "job" ? "Jobs" : "Scholarships"}
              </button>
            ))}
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-zinc-300 bg-white px-3 py-1.5 text-xs dark:border-zinc-700 dark:bg-zinc-800"
          >
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s === "all" ? "All Statuses" : s.charAt(0).toUpperCase() + s.slice(1)}
              </option>
            ))}
          </select>
        </div>
      </Card>

      {/* Stats Summary */}
      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-lg border border-zinc-200 bg-white p-3 text-center dark:border-zinc-800 dark:bg-zinc-900">
          <p className="text-2xl font-bold text-zinc-900 dark:text-white">
            {(stats.total as number) || applications.length}
          </p>
          <p className="text-xs text-zinc-500">Total</p>
        </div>
        <div className="rounded-lg border border-zinc-200 bg-white p-3 text-center dark:border-zinc-800 dark:bg-zinc-900">
          <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
            {(stats.active as number) || 0}
          </p>
          <p className="text-xs text-zinc-500">Active</p>
        </div>
        <div className="rounded-lg border border-zinc-200 bg-white p-3 text-center dark:border-zinc-800 dark:bg-zinc-900">
          <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
            {(stats.successful as number) || 0}
          </p>
          <p className="text-xs text-zinc-500">Successful</p>
        </div>
        <div className="rounded-lg border border-zinc-200 bg-white p-3 text-center dark:border-zinc-800 dark:bg-zinc-900">
          <p className="text-2xl font-bold text-amber-600 dark:text-amber-400">
            {(stats.pending as number) || 0}
          </p>
          <p className="text-xs text-zinc-500">Pending</p>
        </div>
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-500/10 dark:text-red-400">
          {error}
        </div>
      )}

      {loading ? (
        <LoadingSpinner />
      ) : applications.length === 0 ? (
        <EmptyState
          icon={ClipboardList}
          title="No applications tracked"
          description="Start by searching for jobs or scholarships and applying. Applications will appear here automatically."
        />
      ) : (
        <div className="space-y-3">
          {applications.map((app) => (
            <Card key={app.id} className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className={`rounded-lg p-2 ${
                      app.type === "job"
                        ? "bg-blue-50 text-blue-600 dark:bg-blue-500/10 dark:text-blue-400"
                        : "bg-purple-50 text-purple-600 dark:bg-purple-500/10 dark:text-purple-400"
                    }`}
                  >
                    {app.type === "job" ? (
                      <Briefcase size={16} />
                    ) : (
                      <GraduationCap size={16} />
                    )}
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-zinc-900 dark:text-white">
                      {app.title}
                    </h3>
                    <p className="text-xs text-zinc-500">{app.organization}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  {app.deadline && (
                    <span className="hidden text-xs text-zinc-400 sm:block">
                      Due: {new Date(app.deadline).toLocaleDateString()}
                    </span>
                  )}
                  {app.applied_date && (
                    <span className="hidden text-xs text-zinc-400 sm:block">
                      Applied: {new Date(app.applied_date).toLocaleDateString()}
                    </span>
                  )}
                  <Badge variant={STATUS_VARIANT[app.status] || "default"}>
                    {app.status}
                  </Badge>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
