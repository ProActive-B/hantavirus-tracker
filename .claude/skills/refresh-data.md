---
description: Run the ingest pipeline locally, diff the resulting data files against what's committed, and ask before committing. Use when you want to refresh data on demand instead of waiting for the daily cron.
---

# /refresh-data

Run the ingest pipeline locally and review the diff before committing.

## Steps

1. Confirm working tree is clean for `data/`:
   ```bash
   git status -- data/
   ```
   If `data/` has uncommitted changes, stop and ask the user whether to
   stash, commit, or discard them.

2. Run ingest (uv handles the venv):
   ```bash
   uv run python -m ingest.cli run
   ```
   Capture stderr — if any source fetcher raises (vs returning empty),
   surface which one and stop.

3. Check the live-parse status of the cruise-outbreak source:
   ```bash
   jq '.current.parsed_from_live_source, .current.as_of' data/cruise_analysis.json
   ```
   If `parsed_from_live_source` is `false`, note it in the user-facing
   summary — the cruise figures came from the frozen-fallback snapshot,
   not from today's HAN parse. This is fine (data is still
   primary-sourced) but worth flagging.

4. Diff the result:
   ```bash
   git diff --stat data/
   ./scripts/diff-data.sh
   ```
   Show a feature-level summary (added / removed / changed records by id)
   plus per-file line-stat for the JSON files.

5. Show the summary to the user. Ask:
   - Commit these changes? (`yes` / `no` / `partial`)
   - If `partial`: which files?

6. On `yes`, commit only `data/` files, message of the form:
   ```
   data: refresh ingest YYYY-MM-DD

   <one-line summary of what changed>
   ```

## What you must verify before committing

Run validation:
```bash
uv run python -m ingest.cli validate
```
This re-checks every record in `data/hantavirus.geojson` against
`ingest/schemas.py`. If it exits non-zero, fix the source — do not commit.

## Don't

- Don't push without asking.
- Don't `git add -A` — only stage `data/`.
- Don't bypass the schema check; if `ingest.cli validate` exits non-zero,
  treat it as a hard fail.
- Don't commit a `parsed_from_live_source: false` cruise refresh and then
  describe it to the user as "today's live data" — be precise.
