#!/usr/bin/env bash
# PostToolUse hook: when an Edit/Write touches data/*.geojson or data/*.json,
# validate it parses cleanly. Silent-fail on any environmental problem so the
# editor never gets blocked by a broken hook.
set -u

# read tool event from stdin (Claude Code passes JSON via stdin)
input=$(cat 2>/dev/null || true)
[[ -z "$input" ]] && exit 0

# extract file path; if jq unavailable, no-op
command -v jq >/dev/null 2>&1 || exit 0
path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null)

case "$path" in
  */data/*.geojson|*/data/*.json) ;;
  *) exit 0 ;;
esac

[[ -f "$path" ]] || exit 0

# validate JSON parses
if ! python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$path" 2>/dev/null; then
  echo "{\"decision\":\"block\",\"reason\":\"$path is not valid JSON\"}"
  exit 0
fi

# for geojson, lightweight feature-collection shape check
case "$path" in
  *.geojson)
    python3 - <<PY 2>/dev/null || {
      echo "{\"decision\":\"block\",\"reason\":\"$path is not a valid FeatureCollection or has malformed features\"}"
      exit 0
    }
import json, sys
d = json.load(open("$path"))
assert d.get("type") == "FeatureCollection", "type must be FeatureCollection"
for f in d.get("features", []):
    assert f["type"] == "Feature"
    assert f["geometry"]["type"] == "Point"
    p = f["properties"]
    for k in ("id","title","confidence","virus","source_name","source_url"):
        assert k in p, f"missing {k}"
    assert p["confidence"] in ("confirmed","probable","signal"), f"bad confidence {p['confidence']}"
PY
    ;;
esac

exit 0
