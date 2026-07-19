"""
NORAY — GitHub Importer

Fetch GitHub profile data (repos, languages, contributions) via the GitHub API.
No authentication required for public profiles.
Rate limit: 60 requests/hour for unauthenticated requests.
"""

from __future__ import annotations
import json
import urllib.request
import urllib.error
from typing import Any

from noray.shared.models import CareerProfile, GitHubProfile, Project


# ─── Public API ───────────────────────────────────────────────

def fetch_github_profile(username: str) -> dict[str, Any]:
    """
    Fetch GitHub profile data for a given username.
    
    Uses the public GitHub API (no auth required for public profiles).
    Fetches: user info, repos (up to 100), languages per repo.
    
    Args:
        username: GitHub username
    
    Returns:
        Dict with username, repos, languages, contribution stats
    """
    user_data = _api_get(f"https://api.github.com/users/{username}")
    if "error" in user_data:
        return user_data

    repos_data = _api_get(f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated&direction=desc")
    if isinstance(repos_data, dict) and "error" in repos_data:
        return repos_data

    repos = []
    languages = set()
    topics_all = set()

    for repo in repos_data:
        if repo.get("fork"):
            continue  # Skip forks

        # Fetch languages for this repo
        repo_langs = {}
        try:
            langs_data = _api_get(repo["languages_url"])
            if isinstance(langs_data, dict) and "error" not in langs_data:
                repo_langs = langs_data
                languages.update(repo_langs.keys())
        except Exception:
            pass

        topics = repo.get("topics", [])
        topics_all.update(topics)

        repo_info = {
            "name": repo["name"],
            "description": repo.get("description") or "",
            "language": repo.get("language") or "",
            "languages": repo_langs,
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "topics": topics,
            "url": repo["html_url"],
            "homepage": repo.get("homepage") or "",
            "created_at": repo.get("created_at", ""),
            "updated_at": repo.get("updated_at", ""),
            "size_kb": repo.get("size", 0),
            "archived": repo.get("archived", False),
        }
        repos.append(repo_info)

    # Sort by stars + recency (weighted)
    repos.sort(key=lambda r: (r["stars"] * 2 + (1 if r["updated_at"] > "2025" else 0)), reverse=True)

    return {
        "username": username,
        "name": user_data.get("name") or "",
        "bio": user_data.get("bio") or "",
        "company": user_data.get("company") or "",
        "location": user_data.get("location") or "",
        "blog": user_data.get("blog") or "",
        "public_repos": user_data.get("public_repos", 0),
        "followers": user_data.get("followers", 0),
        "following": user_data.get("following", 0),
        "repos": repos,
        "languages": sorted(languages),
        "topics": sorted(topics_all),
        "total_repos": len(repos),
        "total_stars": sum(r["stars"] for r in repos),
    }


def fetch_repo_details(owner: str, repo_name: str) -> dict[str, Any]:
    """
    Fetch detailed information about a specific repository.
    
    Args:
        owner: Repository owner username
        repo_name: Repository name
    
    Returns:
        Dict with detailed repo info including README
    """
    repo = _api_get(f"https://api.github.com/repos/{owner}/{repo_name}")
    if "error" in repo:
        return repo

    # Fetch README
    readme_text = ""
    try:
        readme_data = _api_get(f"https://api.github.com/repos/{owner}/{repo_name}/readme", raw=True)
        if isinstance(readme_data, bytes):
            import base64
            readme_text = base64.b64decode(readme_data).decode("utf-8", errors="replace")
    except Exception:
        pass

    # Fetch languages
    langs = _api_get(f"https://api.github.com/repos/{owner}/{repo_name}/languages")

    return {
        "name": repo["name"],
        "description": repo.get("description") or "",
        "language": repo.get("language") or "",
        "languages": langs if isinstance(langs, dict) else {},
        "stars": repo.get("stargazers_count", 0),
        "forks": repo.get("forks_count", 0),
        "topics": repo.get("topics", []),
        "url": repo["html_url"],
        "homepage": repo.get("homepage") or "",
        "created_at": repo.get("created_at", ""),
        "updated_at": repo.get("updated_at", ""),
        "license": (repo.get("license") or {}).get("name") or "",
        "default_branch": repo.get("default_branch", "main"),
        "readme": readme_text[:5000],  # First 5000 chars
    }


# ─── Profile Integration ─────────────────────────────────────

def import_github_to_profile(username: str, profile: CareerProfile) -> CareerProfile:
    """
    Fetch GitHub data and merge into the profile.
    
    Maps GitHub repos to the projects section and updates
    the skills/tools list with discovered languages.
    """
    github_data = fetch_github_profile(username)

    if "error" in github_data:
        return profile

    # Update GitHub profile section
    profile.github = GitHubProfile(
        username=username,
        repos=github_data["repos"][:20],  # Top 20 repos
        languages=github_data["languages"],
        contributions=github_data.get("total_stars", 0),
        highlights=[
            f"⭐ {r['name']}: {r['description']}"
            for r in github_data["repos"][:5]
            if r["stars"] > 0
        ],
    )

    # Map top repos to projects
    existing_proj_names = {p.name.lower() for p in profile.projects}
    for repo in github_data["repos"][:10]:  # Top 10
        if repo["name"].lower() not in existing_proj_names and repo.get("description"):
            profile.projects.append(Project(
                name=repo["name"],
                description=repo["description"],
                technologies=list(repo.get("languages", {}).keys()) or ([repo["language"]] if repo["language"] else []),
                url=repo["url"],
                highlights=[f"⭐ {repo['stars']} stars"] if repo["stars"] > 0 else [],
            ))

    # Add discovered languages to skills.tools
    existing_tools = set(profile.skills.tools)
    for lang in github_data["languages"]:
        if lang not in existing_tools:
            profile.skills.tools.append(lang)
            existing_tools.add(lang)

    # Add topics to skills.domain
    existing_domain = set(profile.skills.domain)
    for topic in github_data.get("topics", []):
        if topic not in existing_domain and topic not in existing_tools:
            profile.skills.domain.append(topic)
            existing_domain.add(topic)

    if "github_import" not in profile.meta.sources:
        profile.meta.sources.append("github_import")

    return profile


# ─── Internal Helpers ─────────────────────────────────────────

def _api_get(url: str, raw: bool = False) -> Any:
    """
    Make a GET request to the GitHub API.
    
    Args:
        url: API endpoint URL
        raw: If True, return raw bytes (for README content)
    
    Returns:
        Parsed JSON response, raw bytes, or error dict
    """
    headers = {
        "User-Agent": "NORAY/0.1",
        "Accept": "application/vnd.github.v3+json",
    }

    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            if raw:
                return response.read()
            return json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"error": f"Not found: {url}", "status": 404}
        elif e.code == 403:
            return {"error": "GitHub API rate limit exceeded. Try again later or add a GitHub token.", "status": 403}
        elif e.code == 429:
            return {"error": "GitHub API rate limit exceeded. Wait before retrying.", "status": 429}
        return {"error": f"GitHub API error: {e.code} {e.reason}", "status": e.code}

    except urllib.error.URLError as e:
        return {"error": f"Network error: {e.reason}", "status": 0}

    except Exception as e:
        return {"error": str(e), "status": 0}
