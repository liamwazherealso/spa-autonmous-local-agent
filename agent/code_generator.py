"""Two-phase LLM code generation for SPA apps."""

import logging
import re

import requests

from agent.config import AppConfig

logger = logging.getLogger(__name__)


def _query_ollama(config: AppConfig, prompt: str, temperature: float) -> str:
    """Send a prompt to Ollama and return the response text."""
    response = requests.post(
        f"{config.ollama.url}/api/generate",
        json={
            "model": config.ollama.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 8192,
            },
        },
        timeout=config.ollama.timeout,
    )
    if not response.ok:
        error_body = response.text[:500]
        raise RuntimeError(f"Ollama {response.status_code}: {error_body}")
    return response.json()["response"]


def _extract_html(raw: str) -> str:
    """Extract HTML from LLM response, handling code blocks."""
    # Try to find HTML in code blocks first
    code_block = re.search(r"```html?\s*\n(.*?)```", raw, re.DOTALL)
    if code_block:
        return code_block.group(1).strip()

    # Try to find a complete HTML document
    html_match = re.search(r"(<!DOCTYPE html>.*</html>)", raw, re.DOTALL | re.IGNORECASE)
    if html_match:
        return html_match.group(1).strip()

    # Last resort: return everything after stripping obvious non-HTML prefix
    lines = raw.strip().split("\n")
    start = 0
    for i, line in enumerate(lines):
        if line.strip().lower().startswith("<!doctype") or line.strip().lower().startswith("<html"):
            start = i
            break
    return "\n".join(lines[start:]).strip()


def generate_code(config: AppConfig, idea: dict, temperature: float) -> str:
    """Generate a complete SPA using two-phase prompting.

    Phase 1: Architecture plan (with thinking enabled)
    Phase 2: Full HTML generation (with thinking enabled)

    Returns the generated HTML string.
    """
    title = idea["title"]
    description = idea["description"]
    category = idea["category"]

    # Phase 1: Architecture plan
    plan_prompt = f"""You are an expert web developer. Plan the architecture for this single-page web application:

Title: {title}
Description: {description}
Category: {category}

Requirements:
- Single HTML file with ALL CSS and JS inline (no external files or CDNs)
- Must work completely offline
- Interactive and visually polished
- Responsive design
- Clean, modern UI

Outline:
1. Key UI components and layout
2. Core JavaScript logic and state management
3. CSS styling approach
4. User interactions and animations

Be specific and detailed. This plan will guide the code generation."""

    logger.info("Phase 1: Generating architecture plan for '%s'...", title)
    plan = _query_ollama(config, plan_prompt, temperature=temperature)
    logger.debug("Architecture plan:\n%s", plan[:500])

    # Phase 2: Full code generation
    code_prompt = f"""You are an expert web developer. Generate a COMPLETE single-page web application.

Title: {title}
Description: {description}
Category: {category}

Architecture Plan:
{plan}

CRITICAL REQUIREMENTS:
- Output a COMPLETE, valid HTML5 document
- ALL CSS must be in a <style> tag inside <head>
- ALL JavaScript must be in a <script> tag before </body>
- NO external dependencies (no CDNs, no imports, no fetch to external URLs)
- Must work completely offline when opened in a browser
- Include a proper <title> tag
- Make it visually appealing with modern CSS (gradients, shadows, animations)
- Make it fully interactive and functional
- Responsive design that works on mobile and desktop

Output ONLY the complete HTML code inside a ```html code block. No explanations before or after."""

    logger.info("Phase 2: Generating full code for '%s'...", title)
    raw = _query_ollama(config, code_prompt, temperature=temperature)

    html = _extract_html(raw)
    logger.info("Generated %d bytes of HTML", len(html))
    return html
