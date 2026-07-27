"""
NORAY — LLM Abstraction Layer

Provides a unified interface for calling LLMs through the SmartRouter,
with automatic failover, circuit breaker, retry policy, and seamless
fallback between cloud providers and local Ollama models.
All agents use this module instead of calling LLMs directly.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from noray.config import DEFAULT_MODEL, MAX_TOKENS, REVIEWER_MODEL, TEMPERATURE
from noray.llm.providers.base_provider import LLMMessage as SmartLLMMessage

logger = logging.getLogger("noray.shared.llm_utils")


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
    usage: dict[str, int] = field(default_factory=dict)
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
    Routes queries dynamically through the SmartRouter with automatic
    failover between cloud providers and local Ollama.
    """
    from noray.llm.smart_router import smart_router

    cfg = config or LLMConfig()
    target_model = model or cfg.model
    system_prompt = system or cfg.system_prompt
    temp = temperature if temperature is not None else cfg.temperature

    # Build messages in SmartRouter format
    messages = []
    if system_prompt:
        messages.append(SmartLLMMessage(role="system", content=system_prompt))
    messages.append(SmartLLMMessage(role="user", content=prompt))

    # Use SmartRouter for routing and generation with fallback
    smart_config = type(
        "Config",
        (),
        {
            "model": target_model,
            "temperature": temp,
            "max_tokens": cfg.max_tokens,
            "system_prompt": system_prompt,
            "json_mode": False,
            "tools": None,
        },
    )()

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                smart_router.generate_with_fallback(
                    messages=messages,
                    config=smart_config,
                )
            )
        finally:
            loop.close()

        return LLMResponse(
            content=result.content,
            model=result.model,
            usage={
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
            },
            finish_reason=result.finish_reason,
        )
    except Exception as e:
        logger.error(f"SmartRouter call_llm failed: {e}")
        # Ultimate fallback
        from noray.gateway.facade import AIGateway
        from noray.gateway.base import RouteRequirements

        reqs = RouteRequirements()
        gw = AIGateway()
        gw_res = gw.call_llm(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temp,
            max_tokens=cfg.max_tokens,
            requirements=reqs,
        )

        return LLMResponse(
            content=gw_res.content,
            model=gw_res.model,
            usage={"input_tokens": gw_res.input_tokens, "output_tokens": gw_res.output_tokens},
            finish_reason="stop",
        )


def create_reviewer_config() -> LLMConfig:
    """Create config for the reviewer agent (fresh context)."""
    return LLMConfig(
        model=REVIEWER_MODEL,
        temperature=0.2,
        system_prompt=(
            "You are a hiring manager proxy reviewing a job application. "
            "Your job is to make the application as targeted and compelling as possible. "
            "Research the company and critique the drafts rigorously."
        ),
    )


def format_profile_for_prompt(profile_data: dict) -> str:
    """Format a career profile dict into a readable string for LLM prompts."""
    lines = []

    identity = profile_data.get("identity", {})
    lines.append(f"Name: {identity.get('name', 'N/A')}")
    loc = identity.get("location", {})
    lines.append(f"Location: {loc.get('city', '')}, {loc.get('country', '')}")
    lines.append("")

    lines.append("## Education")
    for edu in profile_data.get("education", []):
        lines.append(f"- {edu.get('degree', '')} in {edu.get('field', '')} ({edu.get('start_year', '')}-{edu.get('end_year', '')}) \u2014 {edu.get('institution', '')}")
        if edu.get("thesis"):
            lines.append(f"  Thesis: {edu['thesis']}")
    lines.append("")

    lines.append("## Experience")
    for exp in profile_data.get("experience", []):
        end = exp.get("end_date", "present")
        lines.append(f"- {exp.get('title', '')} ({exp.get('start_date', '')} - {end}) \u2014 {exp.get('company', '')}")
        for r in exp.get("responsibilities", []):
            lines.append(f"  \u2022 {r}")
    lines.append("")

    skills = profile_data.get("skills", {})
    lines.append("## Skills")
    lines.append(f"Primary: {', '.join(skills.get('primary', []))}")
    lines.append(f"Secondary: {', '.join(skills.get('secondary', []))}")
    lines.append(f"Domain: {', '.join(skills.get('domain', []))}")
    lines.append(f"Tools: {', '.join(skills.get('tools', []))}")

    return "\n".join(lines)
