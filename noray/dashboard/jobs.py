"""
NORAY — Job Application Tracker

Track job applications, statuses, and outcomes.
Replaces the legacy job_search_tracker.csv with JSON storage.
Supports migration from CSV format.
"""

from __future__ import annotations
import csv
import json
from pathlib import Path
from datetime import datetime
from typing import Any
from dataclasses import dataclass, field

from noray.config import DATA_DIR, JOB_TRACKER_PATH


TRACKER_PATH = DATA_DIR / "job_applications.json"


@dataclass
class JobApplication:
    """A tracked job application."""
    id: str = ""
    company: str = ""
    role: str = ""
    sector: str = ""
    location: str = ""
    url: str = ""
    status: str = "discovered"  # discovered, applied, interview, offer, rejected, withdrawn
    fit_rating: int = 0         # 0-100
    applied_date: str = ""
    last_updated: str = ""
    contact_person: str = ""
    notes: str = ""
    cv_file: str = ""
    cover_letter_file: str = ""
    source: str = ""            # jobindex, linkedin, google, etc.
    salary_range: str = ""
    interview_dates: list[str] = field(default_factory=list)
    role_type: str = ""         # full-time, part-time, contract, etc.
    channel: str = ""           # web, referral, recruiter, etc.


# ─── CRUD Operations ──────────────────────────────────────────

def load_applications() -> list[JobApplication]:
    """Load all tracked job applications from JSON."""
    if not TRACKER_PATH.exists():
        return []
    try:
        data = json.loads(TRACKER_PATH.read_text(encoding="utf-8"))
        return [JobApplication(**app) for app in data.get("applications", [])]
    except (json.JSONDecodeError, Exception):
        return []


def save_applications(applications: list[JobApplication]) -> None:
    """Save job applications to disk."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "updated_at": datetime.utcnow().isoformat(),
        "count": len(applications),
        "applications": [_serialize(app) for app in applications],
    }
    TRACKER_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def add_application(application: JobApplication) -> JobApplication:
    """Add a new job application to the tracker."""
    applications = load_applications()
    application.id = f"job_{len(applications) + 1:04d}"
    application.last_updated = datetime.utcnow().isoformat()
    if not application.applied_date:
        application.applied_date = datetime.utcnow().strftime("%Y-%m-%d")
    applications.append(application)
    save_applications(applications)
    return application


def update_application(app_id: str, updates: dict[str, Any]) -> JobApplication | None:
    """Update an existing job application."""
    applications = load_applications()
    for app in applications:
        if app.id == app_id:
            for key, value in updates.items():
                if hasattr(app, key):
                    setattr(app, key, value)
            app.last_updated = datetime.utcnow().isoformat()
            save_applications(applications)
            return app
    return None


def get_application(app_id: str) -> JobApplication | None:
    """Get a single application by ID."""
    applications = load_applications()
    for app in applications:
        if app.id == app_id:
            return app
    return None


def delete_application(app_id: str) -> bool:
    """Delete an application by ID."""
    applications = load_applications()
    original_count = len(applications)
    applications = [app for app in applications if app.id != app_id]
    if len(applications) < original_count:
        save_applications(applications)
        return True
    return False


# ─── Queries ──────────────────────────────────────────────────

def get_application_stats() -> dict[str, Any]:
    """Get summary statistics for job applications."""
    applications = load_applications()
    status_counts = {}
    for app in applications:
        status_counts[app.status] = status_counts.get(app.status, 0) + 1

    fit_ratings = [a.fit_rating for a in applications if a.fit_rating > 0]

    return {
        "total": len(applications),
        "by_status": status_counts,
        "avg_fit_rating": sum(fit_ratings) / len(fit_ratings) if fit_ratings else 0,
        "companies_applied": len(set(a.company for a in applications if a.status == "applied")),
    }


def get_applications_by_status(status: str) -> list[JobApplication]:
    """Get all applications with a specific status."""
    return [app for app in load_applications() if app.status == status]


def get_recent_applications(days: int = 30) -> list[JobApplication]:
    """Get applications from the last N days."""
    cutoff = datetime.utcnow().strftime("%Y-%m-%d")
    applications = load_applications()
    recent = []
    for app in applications:
        if app.applied_date:
            try:
                app_date = datetime.strptime(app.applied_date, "%Y-%m-%d")
                if (datetime.utcnow() - app_date).days <= days:
                    recent.append(app)
            except ValueError:
                pass
    return sorted(recent, key=lambda a: a.applied_date, reverse=True)


# ─── CSV Migration ────────────────────────────────────────────

def migrate_from_csv(csv_path: Path = JOB_TRACKER_PATH) -> int:
    """
    Migrate applications from the legacy CSV tracker to JSON.
    
    CSV columns: date, company, sector, role, role_type, channel, status,
    contact_person, fit_rating, notes, cv_file, cover_letter_file, source
    
    Returns:
        Number of applications migrated.
    """
    if not csv_path.exists():
        return 0

    applications = load_applications()
    existing_keys = {(a.company.lower(), a.role.lower()) for a in applications}
    migrated = 0

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                company = (row.get("company") or "").strip()
                role = (row.get("role") or "").strip()
                if not company or not role:
                    continue

                key = (company.lower(), role.lower())
                if key in existing_keys:
                    continue  # Skip duplicates

                app = JobApplication(
                    id=f"job_{len(applications) + migrated + 1:04d}",
                    company=company,
                    role=role,
                    sector=(row.get("sector") or "").strip(),
                    status=(row.get("status") or "discovered").strip(),
                    fit_rating=int((row.get("fit_rating") or "0").strip() or "0"),
                    applied_date=(row.get("date") or "").strip(),
                    contact_person=(row.get("contact_person") or "").strip(),
                    notes=(row.get("notes") or "").strip(),
                    cv_file=(row.get("cv_file") or "").strip(),
                    cover_letter_file=(row.get("cover_letter_file") or "").strip(),
                    source=(row.get("source") or "").strip(),
                    role_type=(row.get("role_type") or "").strip(),
                    channel=(row.get("channel") or "").strip(),
                    last_updated=datetime.utcnow().isoformat(),
                )
                applications.append(app)
                existing_keys.add(key)
                migrated += 1

        if migrated > 0:
            save_applications(applications)

    except Exception as e:
        print(f"CSV migration error: {e}")

    return migrated


# ─── Helpers ──────────────────────────────────────────────────

def _serialize(app: JobApplication) -> dict[str, Any]:
    """Serialize a JobApplication to a dict."""
    return {
        "id": app.id,
        "company": app.company,
        "role": app.role,
        "sector": app.sector,
        "location": app.location,
        "url": app.url,
        "status": app.status,
        "fit_rating": app.fit_rating,
        "applied_date": app.applied_date,
        "last_updated": app.last_updated,
        "contact_person": app.contact_person,
        "notes": app.notes,
        "cv_file": app.cv_file,
        "cover_letter_file": app.cover_letter_file,
        "source": app.source,
        "salary_range": app.salary_range,
        "interview_dates": app.interview_dates,
        "role_type": app.role_type,
        "channel": app.channel,
    }
