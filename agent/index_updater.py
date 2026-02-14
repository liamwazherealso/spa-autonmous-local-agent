"""Gallery index page generator using Jinja2."""

import json
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)


def scan_apps(repo_path: str) -> list[dict]:
    """Scan app directories for metadata.json files."""
    apps = []
    repo = Path(repo_path)

    for metadata_file in sorted(repo.glob("*/metadata.json")):
        try:
            with open(metadata_file) as f:
                metadata = json.load(f)
            metadata["dir_name"] = metadata_file.parent.name
            apps.append(metadata)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to read %s: %s", metadata_file, e)

    # Sort by date descending (newest first)
    apps.sort(key=lambda a: a.get("date", ""), reverse=True)
    logger.info("Found %d apps", len(apps))
    return apps


def update_index(repo_path: str, template_dir: str = "templates") -> None:
    """Regenerate the gallery index.html from all app metadata."""
    apps = scan_apps(repo_path)

    env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
    template = env.get_template("gallery_template.html")

    categories = sorted({app.get("category", "other") for app in apps})

    html = template.render(apps=apps, categories=categories)

    index_path = Path(repo_path) / "index.html"
    with open(index_path, "w") as f:
        f.write(html)

    logger.info("Updated gallery index with %d apps", len(apps))
