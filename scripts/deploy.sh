#!/usr/bin/env bash
# Manual deploy. CI handles the regular path; this is for emergencies or first-time setup.
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -f .env ]]; then
  set -a; . .env; set +a
fi

: "${HETZNER_HOST:?set HETZNER_HOST in .env or env}"
: "${HETZNER_USER:?set HETZNER_USER}"
: "${HETZNER_PATH:?set HETZNER_PATH}"

if [[ "$HETZNER_PATH" == "/" || -z "$HETZNER_PATH" ]]; then
  echo "refusing to rsync --delete to root path"
  exit 1
fi

pnpm install --frozen-lockfile
pnpm build

sha=$(git rev-parse --short HEAD 2>/dev/null || echo "no-git")
echo "Deploying $sha to $HETZNER_USER@$HETZNER_HOST:$HETZNER_PATH"
read -r -p "Proceed? [yes/NO] " yn
[[ "$yn" == "yes" ]] || { echo "aborted"; exit 1; }

rsync -avz --delete dist/ "$HETZNER_USER@$HETZNER_HOST:$HETZNER_PATH/"
code=$(curl -sS -o /dev/null -w "%{http_code}" "https://$HETZNER_HOST/" || echo "fetch-failed")
echo "GET / => $code"
