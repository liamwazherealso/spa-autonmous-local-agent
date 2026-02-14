# Autonomous SPA Development Agent

A containerized agent that uses a locally running Ollama instance to generate one vanilla HTML/CSS/JS single-page application per day, commits it to a git repo, and maintains a gallery page.

## Prerequisites

1. **Ollama** running on your host machine
2. **Model pulled**: `ollama pull qwen3-coder:14b-16k`
3. **Docker** and Docker Compose

Verify Ollama is running:
```bash
curl http://localhost:11434/api/tags
```

## Quick Start

```bash
# Build and run a single generation (test mode)
./run.sh --once

# Run as a daily scheduler (default: 03:00 UTC)
./run.sh
```

## Manual Docker Usage

```bash
# Build
docker compose build

# Run once (macOS)
docker compose --profile macos run --rm spa-agent --once

# Run once (Linux)
docker compose --profile linux run --rm spa-agent --once
```

## Configuration

Edit `config/config.yaml` to customize:

| Setting | Default | Description |
|---------|---------|-------------|
| `ollama.url` | `http://host.docker.internal:11434` | Ollama API endpoint |
| `ollama.model` | `qwen3-coder:14b-16k` | Model to use |
| `schedule.time` | `03:00` | Daily generation time (UTC) |
| `git.auto_push` | `false` | Auto-push after commit |
| `generation.max_retries` | `3` | Retry attempts per generation |

Environment variable overrides: `OLLAMA_URL`, `OLLAMA_MODEL`, `REPO_PATH`, `AUTO_PUSH`, `SCHEDULE_TIME`.

## Output

Generated apps are stored in the Docker volume `spa-data` at `/data/daily-spa-apps/`:

```
daily-spa-apps/
├── index.html              # Gallery page
├── color-palette-mixer/
│   ├── index.html          # The app
│   └── metadata.json       # App metadata
├── retro-snake-game/
│   ├── index.html
│   └── metadata.json
└── ...
```

## Accessing Generated Apps

Copy from the Docker volume:
```bash
docker cp spa-agent:/data/daily-spa-apps ./daily-spa-apps
```

Or mount a local directory instead of a volume by editing `docker-compose.yml`.

## Testing

```bash
# Generate one app
./run.sh --once

# Check the output
docker compose --profile macos run --rm spa-agent ls /data/daily-spa-apps/
```
