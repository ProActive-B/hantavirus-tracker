# hantavirus tracker

Public-awareness tracker for hantavirus incidents and spread dynamics, with a
side-by-side comparison against COVID-19 and a daily-refreshing analysis of the
2026 South Atlantic Andes-virus cruise cluster. Static site (Astro + MapLibre),
daily data ingest via GitHub Actions, deployed to Hetzner.

## Stack

- **Frontend**: Astro 5 (static output), Tailwind 3, MapLibre GL JS 4, Chart.js
- **Ingest**: Python 3.12 + `uv`; commits normalized JSON / GeoJSON nightly
- **CI/CD**: GitHub Actions (`daily-ingest.yml`, `deploy.yml`, `ci.yml`)
- **Hosting**: nginx static on Hetzner (CX22 class is sufficient)

## Data sources (tiered)

- **Confirmed**: CDC NNDSS API, CDC HAN, WHO DONs, ECDC CDTR, Argentina BEN,
  state ministries of health (NM DOH).
- **Probable**: outbreak investigations with lab-pending cases.
- **Signal**: PubMed (academic literature via NCBI E-utilities). ProMED and
  HealthMap retired their public feeds; documented stubs only.

Every record carries a `confidence` field; styling differs by tier. See
`/about` for full methodology and the full active-sources list.

## Live cruise-outbreak analysis

The cluster's canonical figures come from **whichever of CDC HAN 528 or the
latest linked WHO Disease Outbreak News is fresher**. The pipeline:

1. `ingest/sources/cruise_outbreak.py::get_figures()` consults both
   - CDC HAN 528 (`han00528.html`) via tolerant regex of the published prose.
   - The WHO event page `2026-E000227`, following each linked DON
     (DON599 / DON600 / DON601 / …) via `ingest/sources/who_event.py`.
2. Both candidates must pass monotonicity (no regression below the verified
   2026-05-08 baseline).
3. `max(as_of)` wins; the Incident's `source_name` / `source_url` reflects
   the winning authority.
4. On total failure of both, the pipeline serves the verified 2026-05-08
   HAN snapshot — still primary-cited, just stale — and surfaces
   `parsed_from_live_source: false` on `/compare`.

`ingest/cruise_analysis.py` then recomputes attack rate, CFR, days-since-
departure, and days-since-source-update each run and compares against
Diamond Princess (CDC MMWR 69/12, frozen historical).

## Local development

```bash
pnpm install
uv sync                # python ingest deps
uv run python -m ingest.cli run          # writes all 5 data files
pnpm dev               # http://localhost:4321
pnpm build && pnpm preview               # static-output check
```

## The five data contracts

The frontend imports these; the ingest writes them. Schema in `ingest/schemas.py`.

| File | Purpose |
|---|---|
| `data/hantavirus.geojson` | Map points (one Feature per incident). |
| `data/overview.json` | Headline stats on the map page. |
| `data/feed.json` | Reverse-chronological reports for `/feeds` + RSS. |
| `data/comparison.json` | Top-of-page comparison table rows. |
| `data/cruise_analysis.json` | Live cruise cluster figures + Diamond Princess. |

## Repo layout

```
src/             astro pages, components, layouts, styles
public/          static assets; public/data is a symlink to ../data
data/            normalized json + geojson (committed)
data/raw/        scratch (gitignored)
ingest/          python ingest pipeline
ingest/sources/  one fetcher module per upstream source
.github/         workflows
.claude/         agents, skills, hooks for Claude Code
scripts/         deploy + dev helpers
```

## Claude Code

This repo ships with specialist agents (`data-curator`, `spread-analyst`,
`epi-writer`, `frontend-engineer`) and slash-skills (`/refresh-data`,
`/add-incident`, `/deploy`). See `.claude/` and `CLAUDE.md`.
