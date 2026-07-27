"""
NORAY — Automatic Warm-Up Module

Pre-loads the primary local model (Gemma) into memory on NORAY startup
to eliminate first-token latency for the first user request.
Runs as a lightweight background task.
"""

from __future__ import annotations

import asyncio
import logging
import time

import httpx

logger = logging.getLogger("noray.llm.warm_up")

WARM_UP_PROMPTS = ["Hello", "System Ready", "OK"]
WARM_UP_TIMEOUT = 30.0


async def warm_up_ollama_model(
    model_name: str = "gemma3:latest",
    base_url: str = "http://localhost:11434",
) -> bool:
    """
    Send a lightweight warm-up prompt to Ollama to pre-load the model.
    Returns True if warm-up succeeded (model is now in memory).
    """
    logger.info(f"Warm-up: pre-loading model '{model_name}' into memory...")
    start = time.time()

    for attempt, prompt in enumerate(WARM_UP_PROMPTS):
        try:
            async with httpx.AsyncClient(timeout=WARM_UP_TIMEOUT) as client:
                payload = {
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": 1,
                        "temperature": 0.0,
                    },
                }
                res = await client.post(
                    f"{base_url}/api/generate",
                    json=payload,
                )
                if res.status_code == 200:
                    elapsed = time.time() - start
                    logger.info(
                        f"Warm-up: model '{model_name}' loaded in {elapsed:.1f}s "
                        f"(prompt: '{prompt}')"
                    )
                    return True
                else:
                    logger.warning(
                        f"Warm-up attempt {attempt+1} returned {res.status_code}: {res.text[:100]}"
                    )
        except httpx.ConnectError:
            logger.warning(f"Warm-up attempt {attempt+1}: Ollama not reachable at {base_url}")
            await asyncio.sleep(1)
        except asyncio.TimeoutError:
            logger.warning(f"Warm-up attempt {attempt+1}: timeout after {WARM_UP_TIMEOUT}s")
        except Exception as e:
            logger.warning(f"Warm-up attempt {attempt+1}: {e}")

        if attempt < len(WARM_UP_PROMPTS) - 1:
            await asyncio.sleep(0.5)

    elapsed = time.time() - start
    logger.warning(
        f"Warm-up: all attempts failed for '{model_name}' after {elapsed:.1f}s. "
        f"Model will load on first user request."
    )
    return False


async def warm_up_local_models(
    base_url: str = "http://localhost:11434",
) -> dict[str, bool]:
    """
    Attempt to warm up all preferred local models in priority order.
    Stops after the first successful warm-up.
    Returns a dict mapping model names to success status.
    """
    preferred = ["gemma3:latest", "gemma3:7b", "gemma3:2b",
                  "gemma2:latest", "gemma2:9b", "gemma2:2b"]

    results: dict[str, bool] = {}

    for model_name in preferred:
        success = await warm_up_ollama_model(model_name, base_url)
        results[model_name] = success
        if success:
            break

    if not any(results.values()):
        logger.info("Warm-up: no preferred Gemma models found. Trying to discover installed models.")
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{base_url}/api/tags")
                if res.status_code == 200:
                    models = res.json().get("models", [])
                    for model in models:
                        name = model.get("name", "")
                        if name:
                            success = await warm_up_ollama_model(name, base_url)
                            results[name] = success
                            if success:
                                break
        except Exception as e:
            logger.warning(f"Warm-up: failed to discover local models: {e}")

    success_count = sum(1 for v in results.values() if v)
    logger.info(f"Warm-up complete: {success_count}/{len(results)} models loaded successfully")
    return results


async def start_warm_up_background(
    base_url: str = "http://localhost:11434",
    delay: float = 2.0,
) -> asyncio.Task | None:
    """
    Start the warm-up process as a background asyncio task.
    Delays execution by `delay` seconds to let the main app initialize first.
    """
    async def _warm_up_worker():
        await asyncio.sleep(delay)
        logger.info("Background warm-up: starting model pre-load sequence")
        await warm_up_local_models(base_url)

    try:
        task = asyncio.create_task(_warm_up_worker())
        logger.info(f"Background warm-up task scheduled (delay={delay}s)")
        return task
    except RuntimeError:
        logger.warning("No running event loop — warm-up task not scheduled")
        return None
