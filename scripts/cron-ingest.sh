#!/usr/bin/env bash
# Local daily ingest. Use this when the repo isn't on GitHub yet, or as a
# belt-and-suspenders backup to the GH Actions workflow.
#
# Install with cron:   crontab -e
#   17 6 * * * /home/<user>/hantavirus/scripts/cron-ingest.sh >> /var/log/hanta-ingest.log 2>&1
#
# Install with systemd timer: see scripts/hanta-ingest.{service,timer} below.

set -euo pipefail
cd "$(dirname "$0")/.."

# Ensure uv is on PATH for non-login shells.
export PATH="$HOME/.local/bin:$PATH"

ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }

echo "[$(ts)] hanta ingest starting"
uv sync --quiet
uv run python -m ingest.cli run
uv run python -m ingest.cli validate

# If we're in a git repo and there are data/ changes, commit locally.
# Push only if a remote is configured AND the user opts in via the env var.
if [[ -d .git ]] && [[ -n "$(git status --porcelain data/)" ]]; then
  git -c user.name=hanta-cron -c user.email=cron@local add data/
  git -c user.name=hanta-cron -c user.email=cron@local \
    commit -m "data: refresh ingest $(date -u +%Y-%m-%d) [cron]"
  if [[ "${HANTA_CRON_PUSH:-0}" == "1" ]] && git remote get-url origin >/dev/null 2>&1; then
    git push
  fi
fi

echo "[$(ts)] hanta ingest done"
