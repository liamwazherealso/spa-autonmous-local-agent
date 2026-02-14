"""Validates generated HTML for structural correctness."""

import logging
import re

logger = logging.getLogger(__name__)

REQUIRED_ELEMENTS = ["<!doctype html>", "<html", "<head", "<title", "<body"]
MAX_FILE_SIZE = 500_000  # 500KB
MIN_FILE_SIZE = 200  # bytes

# External domains that indicate network dependencies
EXTERNAL_PATTERNS = [
    r'src=["\']https?://',
    r'href=["\']https?://[^"\']*\.css',
    r'@import\s+url\(["\']?https?://',
]


def validate_html(html: str) -> tuple[bool, list[str]]:
    """Validate generated HTML. Returns (is_valid, list_of_errors)."""
    errors = []
    html_lower = html.lower()

    # Size checks
    size = len(html.encode("utf-8"))
    if size < MIN_FILE_SIZE:
        errors.append(f"File too small ({size} bytes, min {MIN_FILE_SIZE})")
    if size > MAX_FILE_SIZE:
        errors.append(f"File too large ({size} bytes, max {MAX_FILE_SIZE})")

    # Required elements
    for element in REQUIRED_ELEMENTS:
        if element not in html_lower:
            errors.append(f"Missing required element: {element}")

    # Check for closing tags
    for tag in ["</html>", "</head>", "</body>"]:
        if tag not in html_lower:
            errors.append(f"Missing closing tag: {tag}")

    # Check title is not empty
    title_match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if title_match:
        if not title_match.group(1).strip():
            errors.append("Empty <title> element")
    else:
        errors.append("No <title> element found")

    # Check for external dependencies (warn but don't fail)
    for pattern in EXTERNAL_PATTERNS:
        if re.search(pattern, html, re.IGNORECASE):
            logger.warning("External dependency detected: %s", pattern)

    # Basic well-formedness: script and style tags should be closed
    for tag in ["script", "style"]:
        open_count = len(re.findall(rf"<{tag}[\s>]", html_lower))
        close_count = len(re.findall(rf"</{tag}>", html_lower))
        if open_count != close_count:
            errors.append(f"Mismatched <{tag}> tags: {open_count} opened, {close_count} closed")

    if errors:
        logger.warning("Validation failed: %s", "; ".join(errors))
    else:
        logger.info("Validation passed (size: %d bytes)", size)

    return len(errors) == 0, errors
