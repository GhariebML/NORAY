"""
NORAY — Entity & Relation Extractor

Extracts structured entities and relationships from unstructured text
using a combination of rule-based NLP patterns and LLM-assisted extraction.

Architecture:
    1. Rule-based extraction (fast, zero-cost) runs first to capture known
       patterns (dates, countries, degree names, technology keywords).
    2. LLM-assisted extraction (optional) runs second for deeper semantic
       understanding when an API key is available.
    3. Results are deduplicated, normalized, and returned as GraphNode/GraphEdge
       domain objects ready for insertion into any BaseGraphStore.

Design Decisions:
    - The extractor is stateless and does not depend on any graph store.
      It produces domain objects that the caller persists.
    - Entity normalization collapses variants (e.g. "ML" → "Machine Learning",
      "UK" → "United Kingdom") using a configurable alias map.
    - The LLM prompt is carefully structured to return JSON, which is parsed
      with fallback error handling.
"""

from __future__ import annotations

import json
import re
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple

from noray.graph.base import GraphNode, GraphEdge, ENTITY_TYPES, RELATIONSHIP_TYPES


# ---------------------------------------------------------------------------
# Entity Alias Normalization Map
# ---------------------------------------------------------------------------

_ENTITY_ALIASES: Dict[str, Tuple[str, str]] = {
    # (normalized_name, entity_type)
    "ml": ("Machine Learning", "Skill"),
    "machine learning": ("Machine Learning", "Skill"),
    "ai": ("Artificial Intelligence", "Skill"),
    "artificial intelligence": ("Artificial Intelligence", "Skill"),
    "dl": ("Deep Learning", "Skill"),
    "deep learning": ("Deep Learning", "Skill"),
    "nlp": ("Natural Language Processing", "Skill"),
    "natural language processing": ("Natural Language Processing", "Skill"),
    "cv": ("Computer Vision", "Skill"),
    "computer vision": ("Computer Vision", "Skill"),
    "python": ("Python", "Technology"),
    "javascript": ("JavaScript", "Technology"),
    "typescript": ("TypeScript", "Technology"),
    "react": ("React", "Technology"),
    "nextjs": ("Next.js", "Technology"),
    "next.js": ("Next.js", "Technology"),
    "fastapi": ("FastAPI", "Technology"),
    "pytorch": ("PyTorch", "Technology"),
    "tensorflow": ("TensorFlow", "Technology"),
    "docker": ("Docker", "Technology"),
    "kubernetes": ("Kubernetes", "Technology"),
    "aws": ("AWS", "Technology"),
    "gcp": ("Google Cloud", "Technology"),
    "azure": ("Microsoft Azure", "Technology"),
    "uk": ("United Kingdom", "Country"),
    "usa": ("United States", "Country"),
    "us": ("United States", "Country"),
    "uae": ("United Arab Emirates", "Country"),
    "germany": ("Germany", "Country"),
    "canada": ("Canada", "Country"),
    "australia": ("Australia", "Country"),
    "france": ("France", "Country"),
    "japan": ("Japan", "Country"),
    "daad": ("DAAD Scholarship", "Scholarship"),
    "chevening": ("Chevening Scholarship", "Scholarship"),
    "fulbright": ("Fulbright Scholarship", "Scholarship"),
    "erasmus": ("Erasmus+ Programme", "Scholarship"),
    "rhodes": ("Rhodes Scholarship", "Scholarship"),
    "commonwealth": ("Commonwealth Scholarship", "Scholarship"),
    "phd": ("PhD", "Role"),
    "msc": ("Master of Science", "Role"),
    "bsc": ("Bachelor of Science", "Role"),
}


# ---------------------------------------------------------------------------
# Rule-Based Extraction Patterns
# ---------------------------------------------------------------------------

_DEGREE_PATTERN = re.compile(
    r"\b(PhD|Ph\.D|Doctorate|Master(?:\'s)?|MSc|M\.Sc|MBA|BSc|B\.Sc|BA|B\.A)\b",
    re.IGNORECASE,
)

_YEAR_PATTERN = re.compile(r"\b(20\d{2})\b")

_URL_PATTERN = re.compile(r"https?://[^\s\)]+")


class EntityRelationExtractor:
    """Extracts Knowledge Graph entities and relations from text.

    Supports two extraction modes:
        1. Rule-based (always active, zero-cost).
        2. LLM-assisted (optional, requires API key).

    Args:
        use_llm: Whether to attempt LLM-assisted extraction.
        alias_map: Optional custom alias normalization map.
    """

    def __init__(
        self,
        use_llm: bool = True,
        alias_map: Optional[Dict[str, Tuple[str, str]]] = None,
    ):
        self.use_llm = use_llm
        self.alias_map = alias_map or _ENTITY_ALIASES

    def extract(
        self,
        text: str,
        *,
        source_document_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[GraphNode], List[GraphEdge]]:
        """Extract entities and relationships from text.

        Args:
            text: Input text to analyze.
            source_document_id: Optional ID of the source document node
                (creates MENTIONS edges from document to extracted entities).
            metadata: Optional additional metadata to attach to entities.

        Returns:
            Tuple of (nodes, edges) ready for persistence.
        """
        nodes: Dict[str, GraphNode] = {}  # keyed by normalized name
        edges: List[GraphEdge] = []

        # --- Phase 1: Rule-based extraction ---
        rule_nodes = self._extract_rules(text)
        for node in rule_nodes:
            nodes[node.name.lower()] = node

        # --- Phase 2: LLM-assisted extraction ---
        if self.use_llm:
            llm_nodes, llm_edges = self._extract_llm(text)
            for node in llm_nodes:
                key = node.name.lower()
                if key not in nodes:
                    nodes[key] = node
                else:
                    # Merge properties from LLM extraction
                    nodes[key].properties.update(node.properties)
            edges.extend(llm_edges)

        # --- Phase 3: Create MENTIONS edges from document ---
        if source_document_id:
            for node in nodes.values():
                edges.append(GraphEdge(
                    source_id=source_document_id,
                    target_id=node.id,
                    type="MENTIONS",
                    weight=0.8,
                ))

        return list(nodes.values()), edges

    def _extract_rules(self, text: str) -> List[GraphNode]:
        """Fast rule-based entity extraction."""
        found: Dict[str, GraphNode] = {}
        text_lower = text.lower()

        # Alias map matching
        for alias, (normalized_name, entity_type) in self.alias_map.items():
            # Word boundary match to avoid partial matches
            pattern = r"\b" + re.escape(alias) + r"\b"
            if re.search(pattern, text_lower):
                key = normalized_name.lower()
                if key not in found:
                    found[key] = GraphNode(
                        name=normalized_name,
                        type=entity_type,
                    )

        # Degree extraction
        for match in _DEGREE_PATTERN.finditer(text):
            degree = match.group(1)
            key = degree.lower()
            if key not in found:
                found[key] = GraphNode(
                    name=degree,
                    type="Role",
                    properties={"subtype": "degree"},
                )

        return list(found.values())

    def _extract_llm(self, text: str) -> Tuple[List[GraphNode], List[GraphEdge]]:
        """LLM-assisted entity and relation extraction."""
        try:
            from noray.shared.llm_utils import call_llm, LLMConfig

            prompt = (
                "Extract structured entities and relationships from the following text.\n\n"
                f"Text:\n\"\"\"\n{text[:3000]}\n\"\"\"\n\n"
                "Return a JSON object with two arrays:\n"
                "1. \"entities\": [{\"name\": str, \"type\": str}]\n"
                f"   Valid types: {', '.join(sorted(ENTITY_TYPES))}\n"
                "2. \"relations\": [{\"source\": str, \"target\": str, \"type\": str}]\n"
                f"   Valid types: {', '.join(sorted(RELATIONSHIP_TYPES))}\n\n"
                "   source and target should be entity names from the entities list.\n"
                "Return ONLY the JSON object, no other text."
            )

            response = call_llm(
                prompt,
                LLMConfig(temperature=0.0, max_tokens=1500),
            )

            return self._parse_llm_response(response.content)

        except Exception:
            return [], []

    def _parse_llm_response(
        self, response_text: str
    ) -> Tuple[List[GraphNode], List[GraphEdge]]:
        """Parse LLM JSON response into domain objects."""
        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []
        name_to_id: Dict[str, str] = {}

        try:
            # Extract JSON from response (handle markdown code blocks)
            json_text = response_text.strip()
            if "```" in json_text:
                # Extract content between code fences
                match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", json_text, re.DOTALL)
                if match:
                    json_text = match.group(1).strip()

            data = json.loads(json_text)

            # Parse entities
            for entity in data.get("entities", []):
                name = entity.get("name", "").strip()
                etype = entity.get("type", "").strip()

                if not name or etype not in ENTITY_TYPES:
                    continue

                node = GraphNode(name=name, type=etype)
                nodes.append(node)
                name_to_id[name.lower()] = node.id

            # Parse relations
            for rel in data.get("relations", []):
                source_name = rel.get("source", "").strip().lower()
                target_name = rel.get("target", "").strip().lower()
                rel_type = rel.get("type", "").strip()

                if rel_type not in RELATIONSHIP_TYPES:
                    rel_type = "RELATED_TO"

                source_id = name_to_id.get(source_name)
                target_id = name_to_id.get(target_name)

                if source_id and target_id:
                    edges.append(GraphEdge(
                        source_id=source_id,
                        target_id=target_id,
                        type=rel_type,
                    ))

        except (json.JSONDecodeError, KeyError, TypeError):
            pass

        return nodes, edges

    def normalize_entity_name(self, name: str) -> str:
        """Normalize an entity name using the alias map."""
        key = name.strip().lower()
        if key in self.alias_map:
            return self.alias_map[key][0]
        return name.strip()
