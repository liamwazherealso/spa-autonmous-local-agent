"""LLM-based SPA idea generation with deduplication."""

import json
import logging
import random
from pathlib import Path

import requests

from agent.config import AppConfig

logger = logging.getLogger(__name__)


def _get_existing_titles(repo_path: str) -> set[str]:
    """Get titles of all existing apps for dedup."""
    titles = set()
    repo = Path(repo_path)
    for metadata_file in repo.glob("*/metadata.json"):
        try:
            with open(metadata_file) as f:
                data = json.load(f)
            titles.add(data.get("title", "").lower())
        except (json.JSONDecodeError, OSError):
            continue
    return titles


def generate_idea(config: AppConfig) -> dict:
    """Generate a unique SPA idea using Ollama.

    Returns dict with keys: title, description, category, slug
    """
    existing = _get_existing_titles(config.git.repo_path)
    category = random.choice(config.categories)

    existing_list = ", ".join(sorted(existing)) if existing else "none yet"

    prompt = f"""Generate a unique single-page web application idea.

Category: {category}

Requirements:
- Must be a self-contained single HTML file with inline CSS and JS
- No external dependencies (no CDNs, no frameworks)
- Should be interactive and visually appealing
- Must work offline in a browser

Existing apps (avoid duplicates): {existing_list}

Respond with ONLY valid JSON, no other text:
{{"title": "App Title", "description": "One sentence description", "category": "{category}", "slug": "app-title-slug"}}"""

    response = requests.post(
        f"{config.ollama.url}/api/generate",
        json={
            "model": config.ollama.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.9,
                "num_predict": 256,
            },
        },
        timeout=config.ollama.timeout,
    )
    response.raise_for_status()

    raw = response.json()["response"].strip()
    logger.debug("Raw idea response: %s", raw)

    # Extract JSON from response (handle markdown code blocks)
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    idea = json.loads(raw)

    # Validate required fields
    for field in ("title", "description", "category", "slug"):
        if field not in idea:
            raise ValueError(f"Missing field in idea: {field}")

    # Dedup check
    if idea["title"].lower() in existing:
        raise ValueError(f"Duplicate idea: {idea['title']}")

    # Sanitize slug
    idea["slug"] = idea["slug"].lower().replace(" ", "-")
    idea["slug"] = "".join(c for c in idea["slug"] if c.isalnum() or c == "-")

    logger.info("Generated idea: %s (%s)", idea["title"], idea["category"])
    return idea
