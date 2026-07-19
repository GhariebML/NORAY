"""
NORAY — Versioned Artifact Registry
Tracks, versions, and manages generated CVs, SOPs, Cover Letters, and reports.
"""

from __future__ import annotations
import time
import logging
from typing import Dict, Any, List, Optional

from noray.cache.redis_cache import RedisCache

logger = logging.getLogger("noray.services.artifacts")


class Artifact:
    """Represents a versioned file or report output generated during a session."""
    
    def __init__(self, artifact_id: str, name: str, category: str, content: str, session_id: str, version: int = 1):
        self.artifact_id = artifact_id
        self.name = name
        self.category = category
        self.content = content
        self.session_id = session_id
        self.version = version
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "name": self.name,
            "category": self.category,
            "content": self.content,
            "session_id": self.session_id,
            "version": self.version,
            "timestamp": self.timestamp
        }


class ArtifactManager:
    """Manages CRUD and versioning for session artifacts using Redis storage."""
    
    def __init__(self, cache: Optional[RedisCache] = None):
        self.cache = cache or RedisCache(namespace="noray_artifacts")

    def create_artifact(self, session_id: str, name: str, category: str, content: str) -> Artifact:
        """Saves a new artifact, incrementing the version index if one already exists."""
        artifact_id = f"{session_id}:{category}"
        
        # Check current version
        current = self.cache.get(artifact_id)
        version = 1
        if current:
            version = current.get("version", 0) + 1
            
        artifact = Artifact(artifact_id, name, category, content, session_id, version)
        self.cache.set(artifact_id, artifact.to_dict(), ttl=604800)
        
        # Save historical version key for retrieval later
        history_key = f"{artifact_id}:v{version}"
        self.cache.set(history_key, artifact.to_dict(), ttl=604800)
        
        logger.info(f"Created versioned artifact: name={name} category={category} version={version}")
        return artifact

    def get_artifact(self, session_id: str, category: str) -> Optional[Dict[str, Any]]:
        """Returns the latest version of the target artifact category for the session."""
        artifact_id = f"{session_id}:{category}"
        return self.cache.get(artifact_id)

    def get_artifact_version(self, session_id: str, category: str, version: int) -> Optional[Dict[str, Any]]:
        """Returns the specific version content of the target artifact."""
        history_key = f"{session_id}:{category}:v{version}"
        return self.cache.get(history_key)
