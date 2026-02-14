"""Main orchestrator: daily cycle of idea → code → validate → commit."""

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import schedule

from agent.code_generator import generate_code
from agent.config import AppConfig, load_config
from agent.git_committer import commit_app, init_repo
from agent.idea_generator import generate_idea
from agent.index_updater import update_index
from agent.validator import validate_html

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_daily_cycle(config: AppConfig) -> bool:
    """Execute one full generation cycle. Returns True on success."""
    logger.info("=== Starting daily generation cycle ===")

    # Generate idea
    try:
        idea = generate_idea(config)
    except Exception as e:
        logger.error("Idea generation failed: %s", e)
        return False

    # Generate and validate code with retries
    html = None
    for attempt in range(1, config.generation.max_retries + 1):
        temp = config.generation.temperature + (attempt - 1) * config.generation.temperature_increment
        logger.info("Generation attempt %d/%d (temperature=%.2f)",
                     attempt, config.generation.max_retries, temp)

        try:
            html = generate_code(config, idea, temperature=temp)
        except Exception as e:
            logger.error("Code generation failed: %s", e)
            continue

        is_valid, errors = validate_html(html)
        if is_valid:
            logger.info("Validation passed on attempt %d", attempt)
            break
        else:
            logger.warning("Validation failed: %s", "; ".join(errors))
            html = None

    if html is None:
        logger.error("All %d attempts failed for '%s'", config.generation.max_retries, idea["title"])
        return False

    # Write files
    app_dir = Path(config.git.repo_path) / idea["slug"]
    app_dir.mkdir(parents=True, exist_ok=True)

    # Write HTML
    with open(app_dir / "index.html", "w") as f:
        f.write(html)

    # Write metadata
    metadata = {
        "title": idea["title"],
        "description": idea["description"],
        "category": idea["category"],
        "slug": idea["slug"],
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }
    with open(app_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info("Wrote app to %s", app_dir)

    # Update gallery index
    try:
        update_index(config.git.repo_path)
    except Exception as e:
        logger.error("Gallery update failed: %s", e)
        return False

    # Git commit
    try:
        success = commit_app(config.git, idea["slug"], idea["title"])
        if not success:
            logger.error("Git commit failed")
            return False
    except Exception as e:
        logger.error("Git commit error: %s", e)
        return False

    logger.info("=== Successfully generated: %s ===", idea["title"])
    return True


def main():
    parser = argparse.ArgumentParser(description="Autonomous SPA Development Agent")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--config", default="config/config.yaml", help="Config file path")
    args = parser.parse_args()

    config = load_config(args.config)
    logger.info("Loaded config: model=%s, url=%s", config.ollama.model, config.ollama.url)

    # Initialize git repo
    init_repo(config.git)

    if args.once:
        logger.info("Running single generation cycle")
        success = run_daily_cycle(config)
        sys.exit(0 if success else 1)

    # Schedule daily run
    schedule.every().day.at(config.schedule.time).do(run_daily_cycle, config)
    logger.info("Scheduled daily generation at %s %s", config.schedule.time, config.schedule.timezone)

    # Also run immediately on first start
    logger.info("Running initial generation cycle")
    run_daily_cycle(config)

    # Scheduler loop
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
