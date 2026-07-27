"""
NORAY — Profile Builder

Orchestrates all importers and merges data into a single career_profile.json.
Handles conflict detection, source prioritization, and backward-compatible
skill file generation.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from noray.config import (
    CAREER_PROFILE_PATH,
    DOCUMENTS_DIR,
)
from noray.shared.models import CareerProfile, ProfileMeta
from noray.shared.profile_store import (
    backup_profile,
    get_profile_diff,
    load_profile,
    merge_profile,
    profile_exists,
    save_profile,
    sync_to_skill_files,
)

# ─── Public API ───────────────────────────────────────────────

def build_profile(
    cv_path: Path | None = None,
    linkedin_path: Path | None = None,
    github_username: str | None = None,
    documents_dir: Path = DOCUMENTS_DIR,
    use_existing: bool = True,
) -> tuple[CareerProfile, dict[str, list[str]]]:
    """
    Build a complete career profile from available sources.
    
    Args:
        cv_path: Path to CV file (optional)
        linkedin_path: Path to LinkedIn export (optional)
        github_username: GitHub username (optional)
        documents_dir: Path to documents folder
        use_existing: If True, load and merge into existing profile
    
    Returns:
        Tuple of (CareerProfile, diff_dict)
        diff_dict describes what new data was found per section.
    """
    # Start with existing profile or fresh
    if use_existing and profile_exists():
        profile = load_profile()
    else:
        profile = CareerProfile(meta=ProfileMeta(
            version="1.0.0",
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
            sources=[],
        ))

    incoming = CareerProfile()  # Collect all new data here

    # ── Import from CV ──
    if cv_path and cv_path.exists():
        from noray.profile_engine.cv_importer import import_cv_to_profile
        import_cv_to_profile(cv_path, incoming)

    # ── Import from documents/cv/ ──
    cv_dir = documents_dir / "cv"
    if cv_dir.exists():
        for f in cv_dir.iterdir():
            if f.suffix.lower() in (".pdf", ".tex", ".docx") and f.name != ".gitkeep":
                try:
                    from noray.profile_engine.cv_importer import import_cv_to_profile
                    import_cv_to_profile(f, incoming)
                except Exception:
                    continue

    # ── Import from LinkedIn ──
    if linkedin_path and linkedin_path.exists():
        from noray.profile_engine.linkedin_importer import import_linkedin_to_profile
        import_linkedin_to_profile(linkedin_path, incoming)

    # ── Import from documents/linkedin/ ──
    linkedin_dir = documents_dir / "linkedin"
    if linkedin_dir.exists():
        for f in linkedin_dir.iterdir():
            if f.suffix.lower() == ".pdf" and f.name != ".gitkeep":
                try:
                    from noray.profile_engine.linkedin_importer import import_linkedin_to_profile
                    import_linkedin_to_profile(f, incoming)
                except Exception:
                    continue

    # ── Import from GitHub ──
    if github_username:
        from noray.profile_engine.github_importer import import_github_to_profile
        import_github_to_profile(github_username, incoming)

    # ── Import certificates from documents/diplomas/ ──
    diplomas_dir = documents_dir / "diplomas"
    if diplomas_dir.exists():
        from noray.profile_engine.certificate_parser import import_certificates_to_profile
        import_certificates_to_profile(diplomas_dir, incoming)

    # ── Import references from documents/references/ ──
    refs_dir = documents_dir / "references"
    if refs_dir.exists():
        _import_references(refs_dir, incoming)

    # ── Compute diff before merging ──
    diff = get_profile_diff(profile, incoming)

    # ── Merge incoming into existing ──
    profile = merge_profile(profile, incoming, source="profile_builder")

    return profile, diff


def auto_detect_sources(documents_dir: Path = DOCUMENTS_DIR) -> dict[str, list[Path]]:
    """
    Scan the documents folder and detect available sources.
    
    Returns:
        Dict mapping source type to list of file paths found.
    """
    sources: dict[str, list[Path]] = {
        "cv": [],
        "linkedin": [],
        "diplomas": [],
        "references": [],
        "applications": [],
    }

    if not documents_dir.exists():
        return sources

    for subdir_name in sources.keys():
        subdir_path = documents_dir / subdir_name
        if subdir_path.exists():
            for f in subdir_path.iterdir():
                if f.is_file() and f.name != ".gitkeep":
                    sources[subdir_name].append(f)

    return sources


def detect_github_from_profile(profile: CareerProfile) -> str | None:
    """
    Try to detect a GitHub username from the profile.
    Checks the github_url field and CV text.
    """
    if profile.github.username:
        return profile.github.username
    if profile.identity.github_url:
        url = profile.identity.github_url.rstrip("/")
        parts = url.split("/")
        if "github.com" in url and len(parts) > 0:
            return parts[-1]
    return None


def run_setup(
    cv_path: Path | None = None,
    linkedin_path: Path | None = None,
    github_username: str | None = None,
    documents_dir: Path = DOCUMENTS_DIR,
    save: bool = True,
    sync_legacy: bool = True,
) -> dict[str, Any]:
    """
    Full setup workflow: detect sources, build profile, save, sync.
    
    This is the high-level entry point for the /setup command.
    
    Returns:
        Dict with profile, diff, sources_found, and files_written.
    """
    # Auto-detect sources
    sources = auto_detect_sources(documents_dir)

    # Auto-detect GitHub if not provided
    if not github_username:
        # Try to find it from existing profile
        if profile_exists():
            existing = load_profile()
            github_username = detect_github_from_profile(existing)

    # Build profile
    profile, diff = build_profile(
        cv_path=cv_path,
        linkedin_path=linkedin_path,
        github_username=github_username,
        documents_dir=documents_dir,
    )

    result = {
        "profile": profile,
        "diff": diff,
        "sources_found": {k: len(v) for k, v in sources.items()},
        "files_written": [],
    }

    # Save profile
    if save:
        if profile_exists():
            backup_profile()
        save_profile(profile, source="setup")
        result["files_written"].append(str(CAREER_PROFILE_PATH))

    # Sync to legacy skill files
    if sync_legacy:
        written = sync_to_skill_files(profile)
        result["files_written"].extend(str(p) for p in written.values())

    return result


# ─── Internal Helpers ─────────────────────────────────────────

def _import_references(refs_dir: Path, profile: CareerProfile) -> None:
    """
    Extract behavioral signals from reference letters.
    Reference letters are rich sources of behavioral profile data.
    """
    for f in refs_dir.iterdir():
        if f.name == ".gitkeep" or f.is_dir():
            continue
        if f.suffix.lower() not in (".pdf", ".txt", ".md"):
            continue

        try:
            text = ""
            if f.suffix.lower() == ".pdf":
                from noray.profile_engine.cv_importer import _extract_from_pdf
                text = _extract_from_pdf(f)
            else:
                text = f.read_text(encoding="utf-8")

            if not text.strip():
                continue

            # Extract positive traits from reference language
            trait_keywords = {
                "dedicated", "hardworking", "innovative", "creative",
                "analytical", "leadership", "team player", "collaborative",
                "reliable", "proactive", "detail-oriented", "self-motivated",
                "excellent communication", "strong work ethic", "adaptable",
                "problem solver", "initiative", "passionate", "committed",
            }

            text_lower = text.lower()
            for trait in trait_keywords:
                if trait in text_lower:
                    if trait not in profile.behavioral.strengths:
                        profile.behavioral.strengths.append(trait.title())

        except Exception:
            continue

    if "reference_import" not in profile.meta.sources:
        profile.meta.sources.append("reference_import")
