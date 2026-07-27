import asyncio
import logging
import re
from abc import ABC, abstractmethod

import httpx

from noray.career_agent.job_search import JobPosting
from noray.config import settings

logger = logging.getLogger("noray.career_agent.providers")

class BaseJobProvider(ABC):
    """Abstract Base Class for all Job Search Providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The identifier/name of the provider."""
        pass

    @abstractmethod
    async def search(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        """Execute a search query on the provider and return normalized JobPostings."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the provider has all necessary API keys/configuration to run."""
        pass


class RemoteOkProvider(BaseJobProvider):
    """Public RemoteOK Job Provider (No API key required)."""

    @property
    def name(self) -> str:
        return "remoteok"

    def is_configured(self) -> bool:
        return True

    async def search(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        url = "https://remoteok.com/api"
        # RemoteOK uses tags for search. We pass query as a tag parameter
        # and also filter positional descriptions locally if needed.
        params = {}
        cleaned_query = query.lower().strip()
        if cleaned_query:
            # RemoteOK uses hyphenated tags (e.g. machine-learning, react)
            tag = cleaned_query.replace(" ", "-")
            params["tag"] = tag

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                logger.info(f"[RemoteOK] Fetching jobs for query: '{query}'")
                response = await client.get(url, params=params, headers=headers)
                if response.status_code != 200:
                    logger.error(f"[RemoteOK] Failed request. Status: {response.status_code}")
                    return []

                data = response.json()
                if not isinstance(data, list) or len(data) <= 1:
                    return []

                # Skip the first element which is the RemoteOK legal warning / advertisement
                job_items = data[1:]
                jobs: list[JobPosting] = []

                for item in job_items:
                    if not isinstance(item, dict) or "position" not in item:
                        continue

                    title = item.get("position", "")
                    company = item.get("company", "")
                    job_url = item.get("url", "")
                    description = item.get("description", "")
                    loc = item.get("location", "") or "Remote"
                    posted_epoch = item.get("date")

                    posted_date = ""
                    if posted_epoch:
                        try:
                            # Convert ISO-8601 or epoch to standard date string
                            posted_date = posted_epoch.split("T")[0]
                        except Exception:
                            posted_date = str(posted_epoch)

                    # Normalize HTML tags in description
                    clean_desc = re.sub(r"<[^>]*>", " ", description).strip()
                    # Collapse multiple spaces
                    clean_desc = re.sub(r"\s+", " ", clean_desc)

                    jobs.append(JobPosting(
                        title=title,
                        company=company,
                        location=loc,
                        url=job_url,
                        description=clean_desc,
                        posted_date=posted_date,
                        source="remoteok",
                        language="en"
                    ))

                    if len(jobs) >= limit:
                        break

                logger.info(f"[RemoteOK] Found {len(jobs)} jobs.")
                return jobs

        except Exception as e:
            logger.error(f"[RemoteOK] Error during search: {e}", exc_info=True)
            return []


class AdzunaProvider(BaseJobProvider):
    """Adzuna Job Search Provider (Requires app_id and app_key)."""

    @property
    def name(self) -> str:
        return "adzuna"

    def is_configured(self) -> bool:
        return bool(settings.ADZUNA_APP_ID and settings.ADZUNA_APP_KEY)

    async def search(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        if not self.is_configured():
            logger.warning("[Adzuna] Provider is not configured. Missing credentials.")
            return []

        # Supported countries: us, gb, ca, au, de, fr, nl, etc.
        # We can try to parse from location or default to us.
        country = "us"
        if location:
            loc_lower = location.lower()
            if "united kingdom" in loc_lower or " uk" in loc_lower or "gb" in loc_lower:
                country = "gb"
            elif "canada" in loc_lower or "ca" in loc_lower:
                country = "ca"
            elif "germany" in loc_lower or "de" in loc_lower:
                country = "de"
            elif "denmark" in loc_lower or "dk" in loc_lower:
                # Adzuna does not natively support dk in standard free tier sometimes, but let's check
                pass

        url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
        params = {
            "app_id": settings.ADZUNA_APP_ID,
            "app_key": settings.ADZUNA_APP_KEY,
            "results_per_page": limit,
            "what": query,
        }
        if location:
            params["where"] = location

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                logger.info(f"[Adzuna] Fetching jobs for query: '{query}' in {country}")
                response = await client.get(url, params=params)
                if response.status_code != 200:
                    logger.error(f"[Adzuna] API failure. Status: {response.status_code}, Msg: {response.text}")
                    return []

                data = response.json()
                results = data.get("results", [])
                jobs: list[JobPosting] = []

                for item in results:
                    title = re.sub(r"<[^>]*>", "", item.get("title", "")).strip()
                    company = item.get("company", {}).get("display_name", "")
                    loc_display = item.get("location", {}).get("display_name", "")
                    job_url = item.get("redirect_url", "")
                    description = re.sub(r"<[^>]*>", "", item.get("description", "")).strip()
                    created = item.get("created", "")

                    posted_date = ""
                    if created:
                        posted_date = created.split("T")[0]

                    jobs.append(JobPosting(
                        title=title,
                        company=company,
                        location=loc_display,
                        url=job_url,
                        description=description,
                        posted_date=posted_date,
                        source="adzuna",
                        language="en"
                    ))

                logger.info(f"[Adzuna] Found {len(jobs)} jobs.")
                return jobs

        except Exception as e:
            logger.error(f"[Adzuna] Error during search: {e}", exc_info=True)
            return []


class SerpapiProvider(BaseJobProvider):
    """SerpAPI Google Jobs Provider (Requires api_key)."""

    @property
    def name(self) -> str:
        return "serpapi"

    def is_configured(self) -> bool:
        return bool(settings.SERPAPI_API_KEY)

    async def search(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        if not self.is_configured():
            logger.warning("[SerpAPI] Provider is not configured. Missing API Key.")
            return []

        url = "https://serpapi.com/search.json"
        q_str = query
        if location:
            q_str = f"{query} in {location}"

        params = {
            "engine": "google_jobs",
            "q": q_str,
            "api_key": settings.SERPAPI_API_KEY,
            "num": limit
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                logger.info(f"[SerpAPI] Fetching Google Jobs for query: '{q_str}'")
                response = await client.get(url, params=params)
                if response.status_code != 200:
                    logger.error(f"[SerpAPI] API failure. Status: {response.status_code}, Msg: {response.text}")
                    return []

                data = response.json()
                results = data.get("jobs_results", [])
                jobs: list[JobPosting] = []

                for item in results:
                    title = item.get("title", "")
                    company = item.get("company_name", "")
                    loc = item.get("location", "")
                    description = item.get("description", "")

                    # Google Jobs doesn't directly offer a single source URL, but has share_link
                    job_url = item.get("share_link", "") or item.get("related_links", [{}])[0].get("link", "")

                    # Estimate posted date from detected extensions
                    posted_date = ""
                    posted_at = item.get("detected_extensions", {}).get("posted_at", "")
                    if posted_at:
                        # e.g. "3 days ago" or "18 hours ago"
                        posted_date = posted_at

                    jobs.append(JobPosting(
                        title=title,
                        company=company,
                        location=loc,
                        url=job_url,
                        description=description,
                        posted_date=posted_date,
                        source="google_jobs",
                        language="en"
                    ))

                logger.info(f"[SerpAPI] Found {len(jobs)} jobs.")
                return jobs

        except Exception as e:
            logger.error(f"[SerpAPI] Error during search: {e}", exc_info=True)
            return []


class TavilyProvider(BaseJobProvider):
    """Tavily Search API Job Search Provider (Requires api_key)."""

    @property
    def name(self) -> str:
        return "tavily"

    def is_configured(self) -> bool:
        return bool(settings.TAVILY_API_KEY)

    async def search(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        if not self.is_configured():
            logger.warning("[Tavily] Provider is not configured. Missing API Key.")
            return []

        url = "https://api.tavily.com/search"
        search_query = f"site:greenhouse.io OR site:lever.co OR site:ashbyhq.com \"{query}\" jobs"
        if location:
            search_query += f" \"{location}\""

        payload = {
            "api_key": settings.TAVILY_API_KEY,
            "query": search_query,
            "search_depth": "light",
            "max_results": min(limit, 10),
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                logger.info(f"[Tavily] Fetching search results for query: '{search_query}'")
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    logger.error(f"[Tavily] API failure. Status: {response.status_code}, Msg: {response.text}")
                    return []

                data = response.json()
                results = data.get("results", [])
                jobs: list[JobPosting] = []

                for item in results:
                    title_raw = item.get("title", "")
                    job_url = item.get("url", "")
                    content = item.get("content", "")

                    # Attempt to parse company name from URL or title
                    company = "Unknown"
                    greenhouse_match = re.search(r"greenhouse\.io/([^/]+)", job_url)
                    lever_match = re.search(r"lever\.co/([^/]+)", job_url)
                    ashby_match = re.search(r"ashbyhq\.com/([^/]+)", job_url)

                    if greenhouse_match:
                        company = greenhouse_match.group(1).capitalize()
                    elif lever_match:
                        company = lever_match.group(1).capitalize()
                    elif ashby_match:
                        company = ashby_match.group(1).capitalize()
                    else:
                        title_parts = title_raw.split(" - ")
                        if len(title_parts) > 1:
                            company = title_parts[-1]
                            title_raw = " - ".join(title_parts[:-1])

                    # Basic title cleaning
                    title = re.sub(r"(Job|Career|Opening|Position|hiring)\b", "", title_raw, flags=re.IGNORECASE).strip()

                    jobs.append(JobPosting(
                        title=title or title_raw,
                        company=company,
                        location=location or "Remote / Web",
                        url=job_url,
                        description=content,
                        source="tavily",
                        language="en"
                    ))

                logger.info(f"[Tavily] Found {len(jobs)} jobs.")
                return jobs

        except Exception as e:
            logger.error(f"[Tavily] Error during search: {e}", exc_info=True)
            return []


class DanishPortalsProvider(BaseJobProvider):
    """Danish Portals Bun CLI Job Provider."""

    @property
    def name(self) -> str:
        return "danish_portals"

    def is_configured(self) -> bool:
        # Checked dynamically in-flight to see if Bun CLI scripts exist
        from pathlib import Path
        for p in ["jobbank", "jobdanmark", "jobindex", "jobnet"]:
            if Path(f".agents/skills/{p}-search/cli/src/cli.ts").exists():
                return True
        return False

    async def search(self, query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
        from noray.career_agent.job_search import search_danish_portals
        # search_danish_portals is synchronous, run in threadpool
        loop = asyncio.get_running_loop()
        try:
            jobs = await loop.run_in_executor(
                None,
                search_danish_portals,
                [query],
                location
            )
            return jobs[:limit]
        except Exception as e:
            logger.error(f"[DanishPortals] Error calling legacy search: {e}", exc_info=True)
            return []


class JobProviderRegistry:
    """Registry managing active job search providers."""

    def __init__(self):
        self._providers: dict[str, BaseJobProvider] = {}
        # Pre-register initial providers in order
        self.register(RemoteOkProvider())
        self.register(AdzunaProvider())
        self.register(SerpapiProvider())
        self.register(TavilyProvider())
        self.register(DanishPortalsProvider())

    def register(self, provider: BaseJobProvider) -> None:
        """Register a new job provider."""
        self._providers[provider.name] = provider
        logger.info(f"Registered job search provider: '{provider.name}'")

    def get_provider(self, name: str) -> BaseJobProvider | None:
        """Retrieve a specific provider by name."""
        return self._providers.get(name)

    def get_active_providers(self) -> list[BaseJobProvider]:
        """Return a list of all currently configured and active providers."""
        active = []
        for name, provider in self._providers.items():
            if provider.is_configured():
                active.append(provider)
            else:
                logger.info(f"Job provider '{name}' skipped: not fully configured (missing API keys/files).")
        return active

# Global provider registry instance
provider_registry = JobProviderRegistry()
