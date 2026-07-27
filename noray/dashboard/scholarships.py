"""
NORAY — Scholarship Application Tracker

Track scholarship applications, deadlines, statuses, and outcomes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from noray.config import DATA_DIR

TRACKER_PATH = DATA_DIR / "scholarship_applications.json"


@dataclass
class ScholarshipApplication:
    """A tracked scholarship application."""
    id: str = ""
    name: str = ""
    provider: str = ""
    country: str = ""
    degree_level: str = ""
    url: str = ""
    status: str = "discovered"      # discovered, preparing, submitted, interview, awarded, rejected
    eligibility_score: int = 0       # 0-100
    deadline: str = ""
    applied_date: str = ""
    last_updated: str = ""
    notes: str = ""
    documents_submitted: list[str] = field(default_factory=list)
    sop_file: str = ""
    motivation_file: str = ""
    research_proposal_file: str = ""
    recommendation_letters: list[str] = field(default_factory=list)
    amount: str = ""
    funding_type: str = ""           # fully_funded, partial, tuition_waiver
    source: str = ""                 # portal key


# ─── CRUD ─────────────────────────────────────────────────────

def load_applications() -> list[ScholarshipApplication]:
    """Load all tracked scholarship applications."""
    if not TRACKER_PATH.exists():
        return []
    try:
        data = json.loads(TRACKER_PATH.read_text(encoding="utf-8"))
        return [ScholarshipApplication(**app) for app in data.get("applications", [])]
    except (json.JSONDecodeError, Exception):
        return []


def save_applications(applications: list[ScholarshipApplication]) -> None:
    """Save scholarship applications to disk."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(applications),
        "applications": [_serialize(app) for app in applications],
    }
    TRACKER_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def add_application(application: ScholarshipApplication) -> ScholarshipApplication:
    """Add a new scholarship application."""
    applications = load_applications()
    application.id = f"sch_{len(applications) + 1:04d}"
    application.last_updated = datetime.now(timezone.utc).isoformat()
    if not application.applied_date:
        application.applied_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    applications.append(application)
    save_applications(applications)
    return application


def update_application(app_id: str, updates: dict[str, Any]) -> ScholarshipApplication | None:
    """Update an existing scholarship application."""
    applications = load_applications()
    for app in applications:
        if app.id == app_id:
            for key, value in updates.items():
                if hasattr(app, key):
                    setattr(app, key, value)
            app.last_updated = datetime.now(timezone.utc).isoformat()
            save_applications(applications)
            return app
    return None


def get_application(app_id: str) -> ScholarshipApplication | None:
    """Get a single application by ID."""
    for app in load_applications():
        if app.id == app_id:
            return app
    return None


def delete_application(app_id: str) -> bool:
    """Delete an application by ID."""
    applications = load_applications()
    original = len(applications)
    applications = [a for a in applications if a.id != app_id]
    if len(applications) < original:
        save_applications(applications)
        return True
    return False


# ─── Queries ──────────────────────────────────────────────────

def get_application_stats() -> dict[str, Any]:
    """Get summary statistics."""
    applications = load_applications()
    status_counts = {}
    for app in applications:
        status_counts[app.status] = status_counts.get(app.status, 0) + 1

    return {
        "total": len(applications),
        "by_status": status_counts,
        "upcoming_deadlines": len(get_upcoming_deadlines(30)),
        "providers": len(set(a.provider for a in applications if a.provider)),
    }


def get_upcoming_deadlines(days: int = 30) -> list[ScholarshipApplication]:
    """Get scholarships with deadlines in the next N days."""
    applications = load_applications()
    upcoming = []
    now = datetime.now(timezone.utc)

    for app in applications:
        if app.deadline and app.status in ("discovered", "preparing"):
            try:
                deadline = datetime.strptime(app.deadline, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                delta = (deadline - now).days
                if 0 <= delta <= days:
                    upcoming.append(app)
            except ValueError:
                pass

    return sorted(upcoming, key=lambda a: a.deadline)


def get_applications_by_status(status: str) -> list[ScholarshipApplication]:
    """Get applications by status."""
    return [a for a in load_applications() if a.status == status]


# ─── Helpers ──────────────────────────────────────────────────

def _serialize(app: ScholarshipApplication) -> dict[str, Any]:
    """Serialize to dict."""
    return {
        "id": app.id,
        "name": app.name,
        "provider": app.provider,
        "country": app.country,
        "degree_level": app.degree_level,
        "url": app.url,
        "status": app.status,
        "eligibility_score": app.eligibility_score,
        "deadline": app.deadline,
        "applied_date": app.applied_date,
        "last_updated": app.last_updated,
        "notes": app.notes,
        "documents_submitted": app.documents_submitted,
        "sop_file": app.sop_file,
        "motivation_file": app.motivation_file,
        "research_proposal_file": app.research_proposal_file,
        "recommendation_letters": app.recommendation_letters,
        "amount": app.amount,
        "funding_type": app.funding_type,
        "source": app.source,
    }
