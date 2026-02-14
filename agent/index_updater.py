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
    """Regenerate the gallery index.html and benchmark.html from all app metadata."""
    apps = scan_apps(repo_path)

    env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)

    # Gallery page
    gallery_template = env.get_template("gallery_template.html")
    categories = sorted({app.get("category", "other") for app in apps})
    gallery_html = gallery_template.render(apps=apps, categories=categories)

    index_path = Path(repo_path) / "index.html"
    with open(index_path, "w") as f:
        f.write(gallery_html)

    logger.info("Updated gallery index with %d apps", len(apps))

    # Benchmark page
    benchmark_template = env.get_template("benchmark_template.html")
    benchmark_html = benchmark_template.render(apps=apps)

    benchmark_path = Path(repo_path) / "benchmark.html"
    with open(benchmark_path, "w") as f:
        f.write(benchmark_html)

    logger.info("Updated benchmark page")
