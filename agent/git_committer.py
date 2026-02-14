"""Git operations for committing generated apps."""

import logging
import subprocess
from pathlib import Path

from agent.config import GitConfig

logger = logging.getLogger(__name__)


def _run_git(args: list[str], cwd: str) -> subprocess.CompletedProcess:
    """Run a git command and return the result."""
    cmd = ["git"] + args
    logger.debug("Running: %s", " ".join(cmd))
    return subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, timeout=30,
    )


def init_repo(config: GitConfig) -> None:
    """Initialize git repo if it doesn't exist."""
    repo = Path(config.repo_path)
    repo.mkdir(parents=True, exist_ok=True)

    if not (repo / ".git").exists():
        _run_git(["init"], cwd=config.repo_path)
        _run_git(
            ["config", "user.name", config.author_name],
            cwd=config.repo_path,
        )
        _run_git(
            ["config", "user.email", config.author_email],
            cwd=config.repo_path,
        )
        logger.info("Initialized git repo at %s", config.repo_path)
    else:
        logger.debug("Git repo already exists at %s", config.repo_path)


def commit_app(config: GitConfig, app_dir_name: str, app_title: str) -> bool:
    """Stage and commit a new app directory and updated index."""
    repo = config.repo_path

    # Stage the app directory and index
    result = _run_git(["add", app_dir_name, "index.html", "benchmark.html"], cwd=repo)
    if result.returncode != 0:
        logger.error("git add failed: %s", result.stderr)
        return False

    # Commit
    message = f"Add {app_title} ({app_dir_name})"
    result = _run_git(
        ["commit", "-m", message, "--author",
         f"{config.author_name} <{config.author_email}>"],
        cwd=repo,
    )
    if result.returncode != 0:
        logger.error("git commit failed: %s", result.stderr)
        return False

    logger.info("Committed: %s", message)

    # Optional push
    if config.auto_push:
        result = _run_git(["push"], cwd=repo)
        if result.returncode != 0:
            logger.error("git push failed: %s", result.stderr)
            return False
        logger.info("Pushed to remote")

    return True
