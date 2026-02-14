#!/bin/bash
set -e

OLLAMA_URL="${OLLAMA_URL:-http://host.docker.internal:11434}"
OLLAMA_MODEL="${OLLAMA_MODEL:-qwen3-coder:14b-16k}"

echo "=== Autonomous SPA Development Agent ==="
echo "Ollama URL: $OLLAMA_URL"
echo "Model: $OLLAMA_MODEL"

# Health check: wait for Ollama to be reachable
echo "Checking Ollama connectivity..."
MAX_RETRIES=30
for i in $(seq 1 $MAX_RETRIES); do
    if curl -sf "$OLLAMA_URL/api/tags" > /dev/null 2>&1; then
        echo "Ollama is reachable."
        break
    fi
    if [ "$i" -eq "$MAX_RETRIES" ]; then
        echo "ERROR: Cannot reach Ollama at $OLLAMA_URL after $MAX_RETRIES attempts."
        echo "Make sure Ollama is running on the host machine."
        exit 1
    fi
    echo "  Waiting for Ollama... ($i/$MAX_RETRIES)"
    sleep 2
done

# Check if model is available
echo "Checking model availability..."
if ! curl -sf "$OLLAMA_URL/api/tags" | grep -q "$OLLAMA_MODEL"; then
    echo "WARNING: Model '$OLLAMA_MODEL' not found in Ollama."
    echo "Pull it with: ollama pull $OLLAMA_MODEL"
    echo "Attempting to continue anyway (model may be pulled on first use)..."
fi

# Initialize git repo if needed
REPO_PATH="${REPO_PATH:-/data/daily-spa-apps}"
if [ ! -d "$REPO_PATH/.git" ]; then
    echo "Initializing git repo at $REPO_PATH..."
    mkdir -p "$REPO_PATH"
    cd "$REPO_PATH"
    git init
    git config user.name "SPA Agent"
    git config user.email "spa-agent@autonomous.dev"
    cd /app
fi

echo "Starting agent..."
exec python -m agent.main "$@"
