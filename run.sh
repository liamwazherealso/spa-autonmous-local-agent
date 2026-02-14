#!/bin/bash
set -e

PAGES_REPO="${PAGES_REPO:-/Users/lpieri/code/spa-app-daily-bot}"

# Detect OS and launch with the correct profile
case "$(uname -s)" in
    Darwin)
        PROFILE="macos"
        ;;
    Linux)
        PROFILE="linux"
        ;;
    *)
        echo "Unsupported OS: $(uname -s)"
        exit 1
        ;;
esac

echo "Detected OS: $(uname -s) → using profile: $PROFILE"

# Detect host hardware for benchmarking
COMPUTE_INFO=""
case "$PROFILE" in
    macos)
        CHIP=$(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo "Unknown")
        RAM_BYTES=$(sysctl -n hw.memsize 2>/dev/null || echo "0")
        RAM_GB=$((RAM_BYTES / 1073741824))
        COMPUTE_INFO="${CHIP} / ${RAM_GB}GB RAM"
        # Check for GPU cores
        GPU_CORES=$(system_profiler SPDisplaysDataType 2>/dev/null | grep "Total Number of Cores" | awk -F': ' '{print $2}' | head -1)
        if [ -n "$GPU_CORES" ]; then
            COMPUTE_INFO="${COMPUTE_INFO} / ${GPU_CORES} GPU cores"
        fi
        ;;
    linux)
        if command -v nvidia-smi &>/dev/null; then
            GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
            GPU_MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader 2>/dev/null | head -1)
            COMPUTE_INFO="${GPU_NAME} / ${GPU_MEM}"
        fi
        CPU=$(grep -m1 "model name" /proc/cpuinfo 2>/dev/null | cut -d: -f2 | xargs || echo "Unknown CPU")
        RAM_KB=$(grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}')
        RAM_GB=$((RAM_KB / 1048576))
        if [ -n "$COMPUTE_INFO" ]; then
            COMPUTE_INFO="${COMPUTE_INFO} / ${CPU} / ${RAM_GB}GB RAM"
        else
            COMPUTE_INFO="${CPU} / ${RAM_GB}GB RAM"
        fi
        ;;
esac

echo "Compute: $COMPUTE_INFO"

# Run the agent
docker compose --profile "$PROFILE" run --rm \
    -e COMPUTE_INFO="$COMPUTE_INFO" \
    "agent-${PROFILE}" "$@"

# Copy generated apps from Docker volume to GitHub Pages repo
echo "Copying generated apps to $PAGES_REPO..."

TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

# Extract from Docker volume via a temporary container
docker create --name spa-copy -v autonomous-dev-agent_spa-data:/data alpine true > /dev/null 2>&1
docker cp "spa-copy:/data/daily-spa-apps/." "$TMPDIR/"
docker rm spa-copy > /dev/null 2>&1

# Copy everything except .git to the Pages repo
rsync -a --exclude='.git' "$TMPDIR/" "$PAGES_REPO/"

echo "Apps copied to $PAGES_REPO"

# Commit and push to GitHub Pages repo
cd "$PAGES_REPO"
if [ -n "$(git status --porcelain)" ]; then
    git add -A
    git commit -m "Add daily generated SPA app

Co-Authored-By: SPA Agent <spa-agent@autonomous.dev>"
    git push
    echo "Pushed to GitHub Pages repo"
else
    echo "No new changes to push"
fi
