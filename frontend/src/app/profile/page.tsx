"use client";

import { useEffect, useState } from "react";
import {
  User,
  GitBranch,
  FileUp,
  Save,
  Plus,
  Trash2,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { PageHeader, Card, Button, Badge, LoadingSpinner } from "@/components/ui";
import { profileApi } from "@/lib/api";

export default function ProfilePage() {
  const [profile, setProfile] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [githubUsername, setGithubUsername] = useState("");
  const [importingGithub, setImportingGithub] = useState(false);
  const [importingCv, setImportingCv] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    identity: true,
    education: true,
    experience: true,
    skills: true,
  });
  const [editMode, setEditMode] = useState(false);
  const [editData, setEditData] = useState<Record<string, string>>({});

  useEffect(() => {
    loadProfile();
  }, []);

  async function loadProfile() {
    try {
      setLoading(true);
      const data = await profileApi.get();
      setProfile(data.profile);
    } catch (err) {
      setMessage({ type: "error", text: "Failed to load profile. Is the API running?" });
    } finally {
      setLoading(false);
    }
  }

  async function handleGithubImport() {
    if (!githubUsername.trim()) return;
    try {
      setImportingGithub(true);
      setMessage(null);
      const result = await profileApi.importGithub(githubUsername);
      setMessage({ type: "success", text: result.message || `Imported from ${githubUsername}` });
      await loadProfile();
    } catch (err) {
      setMessage({ type: "error", text: err instanceof Error ? err.message : "GitHub import failed" });
    } finally {
      setImportingGithub(false);
    }
  }

  async function handleCvUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      setImportingCv(true);
      setMessage(null);
      const result = await profileApi.importCv(file);
      setMessage({ type: "success", text: result.message || `CV parsed: ${file.name}` });
      await loadProfile();
    } catch (err) {
      setMessage({ type: "error", text: err instanceof Error ? err.message : "CV upload failed" });
    } finally {
      setImportingCv(false);
      e.target.value = "";
    }
  }

  function toggleSection(key: string) {
    setExpandedSections((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  function startEditing() {
    const data: Record<string, string> = {};
    data["identity.name"] = S(identity.name);
    data["identity.email"] = S(identity.email);
    data["identity.phone"] = S(identity.phone);
    data["identity.linkedin_url"] = S(identity.linkedin_url);
    data["identity.github_url"] = S(identity.github_url);
    data["goals.career_objectives"] = ((profile?.goals as Record<string, unknown>)?.career_objectives as string[] || []).join(", ");
    data["goals.target_roles"] = ((profile?.goals as Record<string, unknown>)?.target_roles as string[] || []).join(", ");
    setEditData(data);
    setEditMode(true);
  }

  async function handleSave() {
    try {
      setSaving(true);
      const updates: Record<string, unknown> = {};
      updates.identity = {
        ...identity,
        name: editData["identity.name"] || "",
        email: editData["identity.email"] || "",
        phone: editData["identity.phone"] || "",
        linkedin_url: editData["identity.linkedin_url"] || "",
        github_url: editData["identity.github_url"] || "",
      };
      const goals = profile?.goals as Record<string, unknown> || {};
      updates.goals = {
        ...goals,
        career_objectives: editData["goals.career_objectives"] ? editData["goals.career_objectives"].split(",").map((s) => s.trim()).filter(Boolean) : [],
        target_roles: editData["goals.target_roles"] ? editData["goals.target_roles"].split(",").map((s) => s.trim()).filter(Boolean) : [],
      };
      await profileApi.update(updates);
      setMessage({ type: "success", text: "Profile updated successfully" });
      setEditMode(false);
      await loadProfile();
    } catch (err) {
      setMessage({ type: "error", text: "Failed to save profile" });
    } finally {
      setSaving(false);
    }
  }

  function updateEditField(key: string, value: string) {
    setEditData((prev) => ({ ...prev, [key]: value }));
  }

  if (loading) return <LoadingSpinner />;

  const identity = (profile?.identity as Record<string, unknown>) || {};
  const education = (profile?.education as Record<string, unknown>[]) || [];
  const experience = (profile?.experience as Record<string, unknown>[]) || [];
  const skills = (profile?.skills as Record<string, unknown>) || {};
  const certifications = (profile?.certifications as Record<string, unknown>[]) || [];
  const projects = (profile?.projects as Record<string, unknown>[]) || [];

  const S = (v: unknown): string => (v == null ? "" : String(v));
  const hasVal = (v: unknown): boolean => v != null && String(v).length > 0;

  return (
    <div>
      <PageHeader title="Career Profile" description="Your unified career profile — single source of truth">
        {editMode ? (
          <div className="flex gap-2">
            <Button onClick={() => setEditMode(false)} variant="secondary">Cancel</Button>
            <Button onClick={handleSave} disabled={saving}>
              <Save size={16} />
              {saving ? "Saving..." : "Save Changes"}
            </Button>
          </div>
        ) : (
          <Button onClick={startEditing} variant="secondary">
            <User size={16} />
            Edit Profile
          </Button>
        )}
      </PageHeader>

      {message && (
        <div
          className={`mb-6 rounded-lg p-4 text-sm ${
            message.type === "success"
              ? "border border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-500/10 dark:text-emerald-400"
              : "border border-red-200 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-500/10 dark:text-red-400"
          }`}
        >
          {message.text}
        </div>
      )}

      {/* Import Actions */}
      <Card className="mb-6 p-6">
        <h2 className="mb-4 text-lg font-semibold text-zinc-900 dark:text-white">Import Data</h2>
        <div className="flex flex-col gap-4 sm:flex-row">
          <div className="flex flex-1 gap-2">
            <input
              type="text"
              placeholder="GitHub username"
              value={githubUsername}
              onChange={(e) => setGithubUsername(e.target.value)}
              className="flex-1 rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800"
            />
            <Button onClick={handleGithubImport} disabled={importingGithub}>
              <GitBranch size={16} />
              {importingGithub ? "Importing..." : "Import GitHub"}
            </Button>
          </div>
          <div className="relative">
            <input
              type="file"
              accept=".pdf,.tex,.docx,.doc"
              onChange={handleCvUpload}
              className="absolute inset-0 cursor-pointer opacity-0"
              id="cv-upload"
            />
            <Button variant="secondary" disabled={importingCv} className="pointer-events-none">
              <FileUp size={16} />
              {importingCv ? "Uploading..." : "Upload CV"}
            </Button>
          </div>
        </div>
      </Card>

      {/* Identity Section */}
      <ProfileSection
        title="Identity"
        icon={<User size={18} />}
        expanded={expandedSections.identity}
        onToggle={() => toggleSection("identity")}
      >
        {editMode ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <EditField label="Name" field="identity.name" value={editData["identity.name"] || ""} onChange={updateEditField} />
            <EditField label="Email" field="identity.email" value={editData["identity.email"] || ""} onChange={updateEditField} />
            <EditField label="Phone" field="identity.phone" value={editData["identity.phone"] || ""} onChange={updateEditField} />
            <EditField label="LinkedIn" field="identity.linkedin_url" value={editData["identity.linkedin_url"] || ""} onChange={updateEditField} />
            <EditField label="GitHub" field="identity.github_url" value={editData["identity.github_url"] || ""} onChange={updateEditField} />
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Field label="Name" value={identity.name as string} />
              <Field label="Email" value={identity.email as string} />
              <Field label="Phone" value={identity.phone as string} />
              <Field
                label="Location"
                value={
                  identity.location
                    ? `${(identity.location as Record<string, unknown>).city || ""}, ${(identity.location as Record<string, unknown>).country || ""}`
                    : ""
                }
              />
              <Field label="LinkedIn" value={identity.linkedin_url as string} link />
              <Field label="GitHub" value={identity.github_url as string} link />
            </div>
            {(identity.languages as Array<{ language: string; proficiency: string }>)?.length > 0 && (
              <div className="mt-4">
                <p className="mb-2 text-xs font-medium uppercase tracking-wider text-zinc-500">Languages</p>
                <div className="flex flex-wrap gap-2">
                  {(identity.languages as Array<{ language: string; proficiency: string }>).map((lang, i) => (
                    <Badge key={i} variant="info">
                      {lang.language} — {lang.proficiency}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </ProfileSection>

      {/* Education */}
      <ProfileSection
        title={`Education (${education.length})`}
        icon={<User size={18} />}
        expanded={expandedSections.education}
        onToggle={() => toggleSection("education")}
      >
        {education.length === 0 ? (
          <p className="text-sm text-zinc-500">No education data yet</p>
        ) : (
          <div className="space-y-4">
            {education.map((edu, i) => (
              <div key={i} className="rounded-lg border border-zinc-100 p-4 dark:border-zinc-800">
                <p className="font-medium text-zinc-900 dark:text-white">
                  {S(edu.degree)} in {S(edu.field)}
                </p>
                <p className="text-sm text-zinc-500">
                  {S(edu.institution)} · {S(edu.start_year)}–{S(edu.end_year) || "Present"}
                </p>
                {hasVal(edu.gpa) && <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">GPA: {S(edu.gpa)}</p>}
                {hasVal(edu.thesis) && (
                  <p className="mt-1 text-sm italic text-zinc-600 dark:text-zinc-400">Thesis: {S(edu.thesis)}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </ProfileSection>

      {/* Experience */}
      <ProfileSection
        title={`Experience (${experience.length})`}
        icon={<User size={18} />}
        expanded={expandedSections.experience}
        onToggle={() => toggleSection("experience")}
      >
        {experience.length === 0 ? (
          <p className="text-sm text-zinc-500">No experience data yet</p>
        ) : (
          <div className="space-y-4">
            {experience.map((exp, i) => (
              <div key={i} className="rounded-lg border border-zinc-100 p-4 dark:border-zinc-800">
                <p className="font-medium text-zinc-900 dark:text-white">{S(exp.title)}</p>
                <p className="text-sm text-zinc-500">
                  {S(exp.company)} · {S(exp.location)} · {S(exp.start_date)}–{S(exp.end_date) || "Present"}
                </p>
                {(exp.responsibilities as string[])?.length > 0 && (
                  <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-zinc-600 dark:text-zinc-400">
                    {(exp.responsibilities as string[]).map((r, j) => (
                      <li key={j}>{r}</li>
                    ))}
                  </ul>
                )}
                {(exp.technologies as string[])?.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {(exp.technologies as string[]).map((t, j) => (
                      <Badge key={j}>{t}</Badge>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </ProfileSection>

      {/* Skills */}
      <ProfileSection
        title="Skills"
        icon={<User size={18} />}
        expanded={expandedSections.skills}
        onToggle={() => toggleSection("skills")}
      >
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {(["primary", "secondary", "domain", "tools"] as const).map((category) => {
            const items = skills[category] as string[] | undefined;
            if (!items?.length) return null;
            return (
              <div key={category}>
                <p className="mb-2 text-xs font-medium uppercase tracking-wider text-zinc-500">{category}</p>
                <div className="flex flex-wrap gap-1.5">
                  {items.map((skill, i) => (
                    <Badge key={i} variant="success">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </ProfileSection>

      {/* Certifications */}
      {certifications.length > 0 && (
        <ProfileSection
          title={`Certifications (${certifications.length})`}
          icon={<User size={18} />}
          expanded={false}
          onToggle={() => {}}
        >
          <div className="space-y-2">
            {certifications.map((cert, i) => (
              <div key={i} className="flex items-center justify-between rounded-lg border border-zinc-100 p-3 dark:border-zinc-800">
                <div>
                  <p className="text-sm font-medium text-zinc-900 dark:text-white">{S(cert.name)}</p>
                  <p className="text-xs text-zinc-500">{S(cert.issuer)} · {S(cert.date)}</p>
                </div>
                {hasVal(cert.credential_url) && (
                  <a href={S(cert.credential_url)} target="_blank" rel="noopener noreferrer" className="text-xs text-emerald-600 hover:underline">
                    Verify
                  </a>
                )}
              </div>
            ))}
          </div>
        </ProfileSection>
      )}

      {/* Projects */}
      {projects.length > 0 && (
        <ProfileSection
          title={`Projects (${projects.length})`}
          icon={<User size={18} />}
          expanded={false}
          onToggle={() => {}}
        >
          <div className="space-y-3">
            {projects.map((proj, i) => (
              <div key={i} className="rounded-lg border border-zinc-100 p-4 dark:border-zinc-800">
                <p className="font-medium text-zinc-900 dark:text-white">{S(proj.name)}</p>
                <p className="text-sm text-zinc-500">{S(proj.description)}</p>
                {(proj.technologies as string[])?.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {(proj.technologies as string[]).map((t, j) => (
                      <Badge key={j}>{t}</Badge>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </ProfileSection>
      )}
    </div>
  );
}

function ProfileSection({
  title,
  icon,
  expanded,
  onToggle,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  expanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <Card className="mb-4">
      <button
        onClick={onToggle}
        className="flex w-full items-center justify-between p-5 text-left"
      >
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-zinc-100 p-2 dark:bg-zinc-800">{icon}</div>
          <h2 className="text-base font-semibold text-zinc-900 dark:text-white">{title}</h2>
        </div>
        {expanded ? <ChevronDown size={18} className="text-zinc-400" /> : <ChevronRight size={18} className="text-zinc-400" />}
      </button>
      {expanded && <div className="border-t border-zinc-100 px-5 pb-5 pt-4 dark:border-zinc-800">{children}</div>}
    </Card>
  );
}

function Field({ label, value, link }: { label: string; value?: string; link?: boolean }) {
  if (!value || value === "undefined" || value === "null") return null;
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">{label}</p>
      {link ? (
        <a href={value} target="_blank" rel="noopener noreferrer" className="text-sm text-emerald-600 hover:underline">
          {value}
        </a>
      ) : (
        <p className="text-sm text-zinc-900 dark:text-white">{value}</p>
      )}
    </div>
  );
}

function EditField({ label, field, value, onChange }: { label: string; field: string; value: string; onChange: (field: string, value: string) => void }) {
  return (
    <div>
      <label className="mb-1 block text-xs font-medium uppercase tracking-wider text-zinc-500">{label}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(field, e.target.value)}
        className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-800"
      />
    </div>
  );
}
