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

# Run the agent
docker compose --profile "$PROFILE" run --rm \
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
