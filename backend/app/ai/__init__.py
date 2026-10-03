"""Pluggable AI architecture.

The whole image-to-nutrition pipeline is described by a small set of Protocols
in `app.ai.base`. Two implementations ship out of the box:

* `MockMealAnalyzer` (default) — deterministic, no network, returns realistic
  Indian-meal data so the rest of the app works without any model setup.
* `GitHubModelsMealAnalyzer` — real vision via GitHub Models (gpt-4o,
  Llama-3.2-Vision, Phi-3.5-vision, etc.) using your GitHub PAT. Nutrition is
  resolved through `NutritionLookup` (local Indian table → USDA fallback).

Add new providers by implementing the protocols and adding a branch below.
"""
from __future__ import annotations

import logging
from functools import lru_cache

from app.ai.base import MealAnalyzer
from app.ai.mock_provider import MockMealAnalyzer
from app.config import get_settings

log = logging.getLogger(__name__)


@lru_cache
def get_meal_analyzer() -> MealAnalyzer:
    settings = get_settings()
    provider = settings.ai_provider.lower()

    if provider in ("github", "github-models", "githubmodels", "gh"):
        if not settings.github_token:
            log.warning("AI_PROVIDER=%s but GITHUB_TOKEN is empty — falling back to mock provider.", provider)
            return MockMealAnalyzer()
        from app.ai.providers.github_models import GitHubModelsMealAnalyzer

        log.info("AI provider: GitHub Models (%s @ %s)", settings.ai_vision_model, settings.ai_vision_endpoint)
        return GitHubModelsMealAnalyzer(
            token=settings.github_token,
            model=settings.ai_vision_model,
            endpoint=settings.ai_vision_endpoint,
        )

    # Future providers, kept as stubs so swapping is a one-line change.
    # if provider == "qwen25vl":
    #     from app.ai.providers.qwen25vl import Qwen25VLMealAnalyzer
    #     return Qwen25VLMealAnalyzer()
    # if provider in ("yolov8", "florence2", "smolvlm"):
    #     ...

    log.info("AI provider: mock (set AI_PROVIDER=github to use real vision)")
    return MockMealAnalyzer()


__all__ = ["get_meal_analyzer", "MealAnalyzer"]
