#!/usr/bin/env bash
# Human-readable diff for data/ after an ingest run. Counts features added /
# removed / changed in the geojson and any json files, without showing the raw
# JSON diff (which is unreadable).
set -euo pipefail
cd "$(dirname "$0")/.."

if ! git diff --quiet -- data/; then :; else
  echo "data/ unchanged"; exit 0
fi

for f in data/*.geojson data/*.json; do
  [[ -f "$f" ]] || continue
  if ! git diff --quiet -- "$f"; then
    echo "=== $f ==="
    case "$f" in
      *.geojson)
        old_ids=$(git show "HEAD:$f" 2>/dev/null | jq -r '.features[].properties.id' | sort -u)
        new_ids=$(jq -r '.features[].properties.id' "$f" | sort -u)
        added=$(comm -13 <(printf '%s\n' "$old_ids") <(printf '%s\n' "$new_ids") | wc -l)
        removed=$(comm -23 <(printf '%s\n' "$old_ids") <(printf '%s\n' "$new_ids") | wc -l)
        common=$(comm -12 <(printf '%s\n' "$old_ids") <(printf '%s\n' "$new_ids") | wc -l)
        echo "  +$added  -$removed  =$common (records by id)"
        ;;
      *.json)
        echo "  $(git diff --shortstat -- "$f")"
        ;;
    esac
  fi
done
