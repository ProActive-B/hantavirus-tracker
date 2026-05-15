---
description: Add a single hantavirus incident to the tracker by hand, with full provenance. Use when a source is too one-off to write a fetcher for (a single WHO DON, a single state-MoH bulletin).
---

# /add-incident

Interactively add one record to `data/hantavirus.geojson`.

## Required fields (ask if missing)

- **title** — short, factual ("Andes-virus cluster — South Atlantic cruise")
- **location** — readable place name; do not include county-level US detail
- **coordinates** — `[lon, lat]`. For US, use state centroid from
  `ingest/sources/_common.py::US_STATE_CENTROIDS`. For sea / ship outbreaks,
  use the last verified vessel position named in the source.
- **virus** — "Sin Nombre virus" | "Andes virus" | "Seoul virus" |
  "Puumala virus" | other (verify against `ingest/schemas.py::VIRUSES`)
- **cases** — integer; verbatim from source
- **deaths** — integer; verbatim
- **confidence** — `confirmed` | `probable` | `signal`. Hard rule:
  only health authorities → confirmed; ProMED / news → signal.
- **reported** — ISO date the source published
- **source_name** — e.g. "CDC HAN 528"
- **source_url** — direct link to the bulletin (not a news rehash; not
  a search-result snippet URL — you must be able to open the page and
  see the number).
- **summary** — 1–2 sentences, public-readable

## Primary-source verification (mandatory)

Before writing the record, **open the `source_url` in WebFetch** and confirm
each numeric value appears on the page. Quote the exact phrase in the chat
back to the user. If you cannot quote it, do not add the record.

The provenance audit on 2026-05-12 dropped two records (AZ 2025 and CA 2025
aggregates) because no primary URL could be cited — don't recreate that
failure mode.

## Steps

1. Read `data/hantavirus.geojson` and check for duplicates by
   `(title, source_url)` and by coords proximity (<50km, same virus).
   Surface possible dupes to the user.
2. Generate a stable `id` from a hash of `(source_url, reported)`.
3. Append the feature, write back with pretty-print, and run
   `uv run python -m ingest.cli validate` to confirm schema.
4. Stage `data/hantavirus.geojson` only. Commit message:
   `data: add incident — <title>`.

## Don't

- Don't allow `confidence: confirmed` for a non-authority source.
- Don't accept coordinates with >2 decimal places for US records.
- Don't add a record whose number you can't quote verbatim from the
  `source_url` page.
- Don't push without asking.
