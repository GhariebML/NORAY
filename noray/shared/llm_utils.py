"""
NORAY — LLM Abstraction Layer

Provides a unified interface for calling LLMs.
Supports Claude (via Anthropic SDK), with hooks for GPT and Gemini.
All agents use this module instead of calling LLMs directly.
"""

from __future__ import annotations
from typing import Any, Optional
from dataclasses import dataclass, field

from noray.config import DEFAULT_MODEL, REVIEWER_MODEL, TEMPERATURE, MAX_TOKENS


@dataclass
class LLMConfig:
    """Configuration for an LLM call."""
    model: str = DEFAULT_MODEL
    temperature: float = TEMPERATURE
    max_tokens: int = MAX_TOKENS
    system_prompt: str = ""


@dataclass
class LLMResponse:
    """Structured response from an LLM call."""
    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)  # input_tokens, output_tokens
    finish_reason: str = ""


def call_llm(
    prompt: str,
    config: LLMConfig | None = None,
    *,
    system: str = "",
    model: str | None = None,
    temperature: float | None = None,
) -> LLMResponse:
    """
    Call an LLM with the given prompt.
    Routes queries dynamically via the centralized AI Gateway layer.
    """
    from noray.gateway.facade import AIGateway
    from noray.gateway.base import RouteRequirements

    cfg = config or LLMConfig()
    target_model = model or cfg.model
    system_prompt = system or cfg.system_prompt
    temp = temperature if temperature is not None else cfg.temperature

    # Build routing requirements
    reqs = RouteRequirements()
    
    if target_model:
        if "claude" in target_model:
            reqs.preferred_provider = "anthropic"
        elif "gpt" in target_model:
            reqs.preferred_provider = "openai"
        elif "gemini" in target_model:
            reqs.preferred_provider = "gemini"
        else:
            reqs.preferred_provider = "local"
            
    reqs.min_context_window = cfg.max_tokens

    # Forward call to Central Gateway
    gw = AIGateway()
    gw_res = gw.call_llm(
        prompt=prompt,
        system_prompt=system_prompt,
        temperature=temp,
        max_tokens=cfg.max_tokens,
        requirements=reqs
    )

    return LLMResponse(
        content=gw_res.content,
        model=gw_res.model,
        usage={"input_tokens": gw_res.input_tokens, "output_tokens": gw_res.output_tokens},
        finish_reason="stop"
    )


def create_reviewer_config() -> LLMConfig:
    """Create config for the reviewer agent (fresh context)."""
    return LLMConfig(
        model=REVIEWER_MODEL,
        temperature=0.2,  # Lower temperature for review
        system_prompt=(
            "You are a hiring manager proxy reviewing a job application. "
            "Your job is to make the application as targeted and compelling as possible. "
            "Research the company and critique the drafts rigorously."
        ),
    )


def format_profile_for_prompt(profile_data: dict) -> str:
    """Format a career profile dict into a readable string for LLM prompts."""
    lines = []

    # Identity
    identity = profile_data.get("identity", {})
    lines.append(f"Name: {identity.get('name', 'N/A')}")
    loc = identity.get("location", {})
    lines.append(f"Location: {loc.get('city', '')}, {loc.get('country', '')}")
    lines.append("")

    # Education
    lines.append("## Education")
    for edu in profile_data.get("education", []):
        lines.append(f"- {edu.get('degree', '')} in {edu.get('field', '')} ({edu.get('start_year', '')}-{edu.get('end_year', '')}) — {edu.get('institution', '')}")
        if edu.get("thesis"):
            lines.append(f"  Thesis: {edu['thesis']}")
    lines.append("")

    # Experience
    lines.append("## Experience")
    for exp in profile_data.get("experience", []):
        end = exp.get("end_date", "present")
        lines.append(f"- {exp.get('title', '')} ({exp.get('start_date', '')} - {end}) — {exp.get('company', '')}")
        for r in exp.get("responsibilities", []):
            lines.append(f"  • {r}")
    lines.append("")

    # Skills
    skills = profile_data.get("skills", {})
    lines.append("## Skills")
    lines.append(f"Primary: {', '.join(skills.get('primary', []))}")
    lines.append(f"Secondary: {', '.join(skills.get('secondary', []))}")
    lines.append(f"Domain: {', '.join(skills.get('domain', []))}")
    lines.append(f"Tools: {', '.join(skills.get('tools', []))}")

    return "\n".join(lines)
