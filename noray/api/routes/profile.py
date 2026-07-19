"""
NORAY — Profile API Routes

Endpoints for managing the career profile.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
import tempfile
import os

from noray.shared.profile_store import load_profile, save_profile
from noray.shared.models import CareerProfile
from noray.api.schemas import ProfileResponse, ProfileUpdateRequest, ImportGithubRequest

router = APIRouter()


@router.get("", response_model=ProfileResponse)
async def get_profile():
    """Retrieve the current career profile."""
    profile = load_profile()
    return ProfileResponse(
        profile=profile.model_dump(mode="json"),
        meta=profile.meta.model_dump(mode="json"),
    )


@router.put("")
async def update_profile(request: ProfileUpdateRequest):
    """Update the career profile."""
    profile = load_profile()
    # Apply updates
    for key, value in request.updates.items():
        if hasattr(profile, key):
            setattr(profile, key, value)
    save_profile(profile, source=request.source)
    return {"status": "updated", "message": "Profile updated successfully"}


@router.post("/import/github")
async def import_github(request: ImportGithubRequest):
    """Import profile data from GitHub."""
    from noray.profile_engine.github_importer import import_github_to_profile
    try:
        profile = load_profile()
        profile = import_github_to_profile(request.username, profile)
        save_profile(profile, source="github_import")
        repo_count = len(profile.github.repos) if profile.github else 0
        return {
            "status": "imported",
            "message": f"Successfully imported {repo_count} repos from {request.username}",
            "username": request.username,
            "repos_found": repo_count,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/import/cv")
async def import_cv(file: UploadFile = File(...)):
    """Import profile data from an uploaded CV file."""
    from noray.profile_engine.cv_importer import parse_cv
    from pathlib import Path
    import logging

    logger = logging.getLogger(__name__)

    # Extract extension safely using pathlib (never trust raw filename directly)
    original_filename = file.filename or "cv.pdf"
    suffix = Path(original_filename).suffix.lower() or ".pdf"

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=None) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        logger.info("CV upload saved to temp: %s (original: %s)", tmp_path, original_filename)
        result = parse_cv(Path(tmp_path))
        return {
            "status": "parsed",
            "message": f"CV parsed: {original_filename}",
            "data": result,
        }
    except Exception as e:
        logger.error("CV import failed for %s: %s", original_filename, str(e))
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
