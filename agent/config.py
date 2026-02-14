"""Configuration loader with YAML + environment variable overrides."""

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class OllamaConfig:
    url: str = "http://host.docker.internal:11434"
    model: str = "qwen3-coder:14b-16k"
    timeout: int = 300


@dataclass
class ScheduleConfig:
    time: str = "03:00"
    timezone: str = "UTC"


@dataclass
class GitConfig:
    author_name: str = "SPA Agent"
    author_email: str = "spa-agent@autonomous.dev"
    auto_push: bool = False
    repo_path: str = "/data/daily-spa-apps"


@dataclass
class GenerationConfig:
    max_retries: int = 3
    temperature: float = 0.7
    temperature_increment: float = 0.1


@dataclass
class AppConfig:
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    schedule: ScheduleConfig = field(default_factory=ScheduleConfig)
    git: GitConfig = field(default_factory=GitConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    categories: list[str] = field(default_factory=lambda: [
        "game", "tool", "visualization", "animation", "productivity",
        "educational", "creative", "music", "simulation", "puzzle",
    ])


def load_config(config_path: str = "config/config.yaml") -> AppConfig:
    """Load config from YAML file with environment variable overrides."""
    config = AppConfig()

    path = Path(config_path)
    if path.exists():
        with open(path) as f:
            data = yaml.safe_load(f) or {}

        if "ollama" in data:
            for k, v in data["ollama"].items():
                if hasattr(config.ollama, k):
                    setattr(config.ollama, k, v)

        if "schedule" in data:
            for k, v in data["schedule"].items():
                if hasattr(config.schedule, k):
                    setattr(config.schedule, k, v)

        if "git" in data:
            for k, v in data["git"].items():
                if hasattr(config.git, k):
                    setattr(config.git, k, v)

        if "generation" in data:
            for k, v in data["generation"].items():
                if hasattr(config.generation, k):
                    setattr(config.generation, k, v)

        if "categories" in data:
            config.categories = data["categories"]

    # Environment variable overrides
    if url := os.environ.get("OLLAMA_URL"):
        config.ollama.url = url
    if model := os.environ.get("OLLAMA_MODEL"):
        config.ollama.model = model
    if repo := os.environ.get("REPO_PATH"):
        config.git.repo_path = repo
    if push := os.environ.get("AUTO_PUSH"):
        config.git.auto_push = push.lower() in ("true", "1", "yes")
    if sched_time := os.environ.get("SCHEDULE_TIME"):
        config.schedule.time = sched_time

    return config
