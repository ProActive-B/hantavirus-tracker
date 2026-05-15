# Hantavirus Tracker — Claude Code project guide

Public-awareness tracker for hantavirus, with a side-by-side comparison vs COVID-19
and a daily-refreshing analysis of the 2026 South Atlantic Andes-virus cruise cluster.
Static site (Astro + MapLibre), daily ingest via GitHub Actions, deployed to Hetzner.

## Hard rules

- **Primary-source-only.** Every record must trace to a recognized public-health
  authority page (CDC, WHO DON, ECDC, PAHO, national/state ministry). Numbers
  are taken **verbatim** from that page. Search-result snippets, news rehashes,
  and Wikipedia are *not* sources of record — at best they point you to the
  primary URL, which is what we cite.
- **Confidence tier is mandatory** on every map point and feed item:
  `confirmed | probable | signal`. Definitions live in `src/pages/about.astro`.
- **No PHI.** US data is state-centroid only — never include county, address, or
  patient-identifying detail, even if a news outlet published it.
- **No invented numbers.** If you can't quote it from the cited URL, don't put
  it in `data/`. If you can't verify a previously-committed number, drop the
  record rather than weaken its confidence tier.
- **Live scrapers need a frozen-but-cited fallback.** If a primary-source page
  is unreachable or its structure changes, the fetcher must fall back to the
  last-verified snapshot of that same source (not to fabricated data) and
  surface `parsed_from_live_source: false` to the UI. See
  `ingest/sources/cruise_outbreak.py` for the canonical pattern.
- **Don't break the daily ingest.** If you change `ingest/schemas.py`, bump
  `SCHEMA_VERSION` and update all consumers in the same change. The site reads
  the five files below — keep those contracts stable.

## The five data contracts

Frontend pages import these directly; the ingest pipeline writes them. Don't
rename or restructure without updating both sides.

| File | Producer | Consumer |
|---|---|---|
| `data/hantavirus.geojson` | `ingest/normalize.py::write_geojson` | map page (runtime fetch) |
| `data/overview.json` | `ingest/normalize.py::write_overview` | map page (build-time import) |
| `data/feed.json` | `ingest/normalize.py::write_feed` | feeds page + RSS |
| `data/comparison.json` | `ingest/comparison.py::write_comparison` | compare page (table) |
| `data/cruise_analysis.json` | `ingest/cruise_analysis.py::write_cruise_analysis` | compare page (cruise section) |

## Where things live

- `src/pages/{index,compare,feeds,about}.astro` — the four primary tabs.
- `src/components/MapApp.astro` — MapLibre map + side panel; loads
  `/data/hantavirus.geojson` at runtime.
- `data/*.json{,geojson}` — committed, normalized data. Don't hand-edit;
  regenerate via `pnpm ingest` or `/refresh-data`.
- `ingest/sources/*.py` — one fetcher per source. Each returns
  `list[Incident]`. Active sources:
  - `nndss.py` — **CDC NNDSS SODA API** (`data.cdc.gov` dataset `x9gk-5huc`).
    Per-state weekly hantavirus counts for current and previous year. Single
    biggest source by record count; produces the US state markers on the map.
  - `cruise_outbreak.py` — canonical MV Hondius cluster Incident;
    `get_figures()` consults CDC HAN 528 **and** the latest linked WHO DON,
    returns the fresher of the two (falls back to verified 2026-05-08
    snapshot if both fail).
  - `who_event.py` — scrapes WHO emergency-event page `2026-E000227`,
    follows DON links (DON599 / DON600 / DON601 / future), emits one
    feed-only Incident per DON (`show_on_map=False`).
  - `argentina.py` — Argentina Boletín Epidemiológico Nacional. Live-parse
    of news-article HTML with regex; fallback to verified BEN SE-17/2026
    snapshot. Single Incident per season.
  - `ecdc.py` — weekly CDTR feed; emits feed-only meta-summaries.
  - `pubmed.py` — NCBI E-utilities (esearch + esummary). Up to 25 most-recent
    hantavirus papers; signal-tier, feed-only.
  - `seed.py` — locally-curated NM state-DOH records (kept as feed-only;
    NNDSS covers state aggregates on the map).
- Documented stubs (return `[]`): `chile.py` (Cloudflare WAF blocks
  scripted access), `who.py` (legacy DON RSS gone), `promed.py` (free RSS
  discontinued 2024), `cdc.py` (HAN listing URL moved), `paho.py`,
  `healthmap.py` (public API dead).
- `ingest/cruise_analysis.py` — combines live cruise figures + Diamond Princess
  reference + methodology prose; writes `data/cruise_analysis.json`.
- `.github/workflows/daily-ingest.yml` — cron at 06:17 UTC.
- `.github/workflows/deploy.yml` — Astro build + rsync to Hetzner.

## The `show_on_map` flag

`Incident.show_on_map: bool = True` lets a record appear in feeds + RSS for
citation while being suppressed from the map. Used when multiple authoritative
reports describe the same cluster (CDC HAN + each WHO DON about MV Hondius) or
when a record is a meta-summary rather than a localized incident (ECDC weekly
CDTR mentioning hantavirus among other pathogens).

Consequences enforced in `normalize.py`:
- `write_geojson` only includes `show_on_map=True` records.
- `write_overview` counts cases/deaths only from `show_on_map=True` (otherwise
  sequential DON snapshots would triple-count the same cluster).
- `write_feed` suppresses a `show_on_map=False` record whose `source_url`
  duplicates one already covered by a `show_on_map=True` record (collapses
  the "WHO DON601 snapshot" against the "cluster Incident currently sourced
  to DON601"). Unrelated records sharing a URL — e.g., NM 2025 and NM 2026
  both citing the NM DOH page — both survive.

## Agents (in `.claude/agents/`)

- `data-curator` — owns ingest pipeline + source fetchers + provenance audit.
- `spread-analyst` — analytical writing on R₀, CFR, attack rate; owns
  `comparison.json`, `overview.json`, the methodology prose inside
  `cruise_analysis.py`, and the prose blocks on `index.astro` / `compare.astro`.
- `epi-writer` — public-facing copy. Plain language, careful risk framing.
- `frontend-engineer` — Astro / MapLibre / Tailwind changes; doesn't touch data.

## Skills (slash commands)

- `/refresh-data` — runs ingest locally, diffs the resulting data files,
  asks before commit.
- `/add-incident` — guided form to add a one-off incident with required
  primary-source URL.
- `/deploy` — preview build + rsync to Hetzner; requires explicit confirmation.

## Style

- Terse copy. Public-health register, not clinical, not tabloid.
- Tailwind utility classes; no CSS files beyond `src/styles/global.css`.
- TypeScript strict mode.

## Don't

- Don't add tracking pixels or analytics that need consent.
- Don't paraphrase a source's numbers, even to "round nicely."
- Don't use the news scraper or ProMED to populate `confirmed` — those are
  `signal` until ratified by a health authority.
- Don't re-introduce records that were dropped during a provenance audit
  (currently: AZ 2025, CA 2025) unless you have a citable state-MoH URL.
