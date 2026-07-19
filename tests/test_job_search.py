import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from noray.career_agent.job_search import JobPosting, SearchResult, search_jobs
from noray.career_agent.providers import (
    provider_registry,
    RemoteOkProvider,
    AdzunaProvider,
    SerpapiProvider,
    TavilyProvider,
    BaseJobProvider,
)
from noray.config import settings

@pytest.fixture
def mock_profile():
    return {
        "identity": {
            "name": "Test Candidate",
            "email": "test@candidate.com",
            "location": {"city": "New York", "country": "US"}
        },
        "skills": {
            "primary": ["Python", "Machine Learning", "FastAPI"],
            "secondary": ["Docker", "Git"],
            "domain": [],
            "tools": []
        },
        "goals": {
            "target_roles": ["Software Engineer", "ML Engineer"]
        }
    }


def test_provider_registry_registration():
    """Verify registry properly registers and exposes providers."""
    class CustomProvider(BaseJobProvider):
        @property
        def name(self) -> str:
            return "custom_test"
        
        def is_configured(self) -> bool:
            return True
            
        async def search(self, query: str, location: str = "", limit: int = 20):
            return []

    registry = provider_registry
    custom = CustomProvider()
    registry.register(custom)
    
    assert registry.get_provider("custom_test") == custom
    assert custom in registry.get_active_providers()


@pytest.mark.asyncio
async def test_remoteok_provider_parsing():
    """Verify RemoteOkProvider parses remoteok payload correctly."""
    mock_payload = [
        {"legal": "This is legal advice"},
        {
            "position": "Senior ML Engineer",
            "company": "AI Labs",
            "url": "https://remoteok.com/jobs/1",
            "description": "<p>We require Python and Machine Learning.</p>",
            "location": "Worldwide",
            "date": "2026-07-15T12:00:00Z"
        }
    ]

    provider = RemoteOkProvider()
    
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_payload
        mock_get.return_value = mock_response
        
        jobs = await provider.search("ML")
        
        assert len(jobs) == 1
        job = jobs[0]
        assert job.title == "Senior ML Engineer"
        assert job.company == "AI Labs"
        assert job.url == "https://remoteok.com/jobs/1"
        assert "We require Python" in job.description
        assert job.location == "Worldwide"
        assert job.posted_date == "2026-07-15"
        assert job.source == "remoteok"


@pytest.mark.asyncio
async def test_adzuna_provider_configuration_and_search():
    """Verify AdzunaProvider is only active when keys are provided and handles results."""
    provider = AdzunaProvider()
    
    # Test unconfigured
    with patch.object(settings, "ADZUNA_APP_ID", None), patch.object(settings, "ADZUNA_APP_KEY", None):
        assert not provider.is_configured()
        assert await provider.search("Python") == []

    # Test configured & mock search
    with patch.object(settings, "ADZUNA_APP_ID", "app_id"), \
         patch.object(settings, "ADZUNA_APP_KEY", "app_key"), \
         patch("httpx.AsyncClient.get") as mock_get:
        
        assert provider.is_configured()
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "title": "Python Developer",
                    "company": {"display_name": "Tech Corp"},
                    "location": {"display_name": "New York, NY"},
                    "redirect_url": "https://adzuna.com/redirect/1",
                    "description": "Write FastAPI backend code.",
                    "created": "2026-07-16T10:00:00Z"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        jobs = await provider.search("Python", location="New York")
        assert len(jobs) == 1
        assert jobs[0].title == "Python Developer"
        assert jobs[0].company == "Tech Corp"
        assert jobs[0].source == "adzuna"


@pytest.mark.asyncio
async def test_tavily_provider_jobs_search():
    """Verify TavilyProvider wraps web results into JobPostings."""
    provider = TavilyProvider()
    
    with patch.object(settings, "TAVILY_API_KEY", "tavily_key"), \
         patch("httpx.AsyncClient.post") as mock_post:
         
         assert provider.is_configured()
         
         mock_response = MagicMock()
         mock_response.status_code = 200
         mock_response.json.return_value = {
             "results": [
                 {
                     "title": "Senior Python Developer - Lever",
                     "url": "https://jobs.lever.co/techco/123",
                     "content": "Looking for a Python and Docker expert."
                 }
             ]
         }
         mock_post.return_value = mock_response
         
         jobs = await provider.search("Python")
         assert len(jobs) == 1
         assert jobs[0].company == "Techco"
         assert "lever" in jobs[0].url.lower()
         assert jobs[0].source == "tavily"


@pytest.mark.asyncio
async def test_search_jobs_orchestrator(mock_profile):
    """Verify search_jobs coordinates providers, deduplicates, and scores fit."""
    # We will mock the registry to return our custom mock provider
    class MockProvider(BaseJobProvider):
        @property
        def name(self) -> str:
            return "mock"
        
        def is_configured(self) -> bool:
            return True
            
        async def search(self, query: str, location: str = "", limit: int = 20):
            return [
                JobPosting(
                    title="Software Engineer",
                    company="Google",
                    location="New York",
                    url="https://jobs.google.com/1",
                    description="We require Python, FastAPI, and Git.",
                    source="mock"
                ),
                JobPosting(
                    title="Chef",
                    company="Pasta Place",
                    location="New York",
                    url="https://jobs.chef.com/1",
                    description="Looking for an experienced chef.",
                    source="mock"
                )
            ]

    mock_provider = MockProvider()
    
    with patch("noray.career_agent.providers.provider_registry.get_active_providers", return_value=[mock_provider]):
        res = await search_jobs(mock_profile, focus_area="Python")
        
        assert isinstance(res, SearchResult)
        assert len(res.jobs) == 2
        # Google Software Engineer should have higher fit score than Chef
        assert res.jobs[0].title == "Software Engineer"
        assert res.jobs[0].fit_score > res.jobs[1].fit_score
        assert "python" in res.jobs[0].match_reasons[0].lower()
