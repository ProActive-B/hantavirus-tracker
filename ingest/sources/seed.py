"""Verified, primary-source seed records.

Every record here must trace to a primary public-health authority page (CDC HAN,
WHO DON, ECDC, PAHO, national/state ministry of health) — not to a news rehash
or a secondary aggregator — and every numeric value must be quotable from that
page. If a source page rots or changes its numbers, fix it here before the next
build.

Provenance audit, last verified 2026-05-14:
- NM DOH HPS page (nmhealth.org/about/erd/ideb/zdp/hps/): NM 2025 & 2026 figures.

Records here have ``show_on_map=False`` because the same state-year cells are
now covered by the federal CDC NNDSS feed (``ingest.sources.nndss``), which is
the consistent system-wide aggregator and serves the map markers for every
state. State-DOH records remain in feeds for citation — they sometimes diverge
from NNDSS (different case definitions, different update cadence) and that
divergence is itself useful for researchers. As of 2026-05-14:

- NM 2025: NM DOH reports 7 confirmed; NNDSS reports 2 (NM DOH higher).
- NM 2026: NM DOH reports 1 confirmed; NNDSS reports 2 (NNDSS higher).

The 2026 South Atlantic cruise cluster is produced by
``ingest.sources.cruise_outbreak``, which scrapes CDC HAN 528 and consults the
latest WHO DON each ingest run.

Records dropped during the 2026-05-12 audit (no primary URL); now covered by
NNDSS: Arizona 2025, California 2025.
"""
from __future__ import annotations

from datetime import date

from ..normalize import stable_id
from ..schemas import Incident
from ._common import US_STATE_CENTROIDS, now_utc


def fetch() -> list[Incident]:
    n = now_utc()
    records: list[Incident] = []

    # --- New Mexico 2025 annual total ---
    nm = US_STATE_CENTROIDS["NM"]
    records.append(Incident(
        id=stable_id("nmdoh", "hps-2025"),
        title="New Mexico — 2025 HPS, 7 confirmed (NM DOH)",
        location="New Mexico, USA (Santa Fe, Taos, McKinley, Bernalillo counties)",
        lon=nm[0], lat=nm[1],
        virus="Sin Nombre virus",
        cases=7, deaths=1,
        confidence="confirmed",
        reported=date(2025, 12, 31),
        ingested_at=n,
        source_name="New Mexico DOH — HPS",
        source_url="https://www.nmhealth.org/about/erd/ideb/zdp/hps/",
        summary=(
            "Seven confirmed HPS cases across Santa Fe, Taos, McKinley, and "
            "Bernalillo counties (the Bernalillo case was travel-associated). "
            "One reported death (Santa Fe County, 2025-03-07). State-DOH "
            "figure; the federal NNDSS aggregate currently shows 2 for the "
            "same state-year (state DOH and NNDSS use different update cadences "
            "and case definitions)."
        ),
        show_on_map=False,
    ))

    # --- New Mexico 2026 first case ---
    records.append(Incident(
        id=stable_id("nmdoh", "hps-2026-01"),
        title="New Mexico — 2026 HPS, 1 confirmed (NM DOH)",
        location="New Mexico, USA",
        lon=nm[0], lat=nm[1],
        virus="Sin Nombre virus",
        cases=1, deaths=None,
        confidence="confirmed",
        reported=date(2026, 3, 15),
        ingested_at=n,
        source_name="New Mexico DOH — HPS",
        source_url="https://www.nmhealth.org/about/erd/ideb/zdp/hps/",
        summary=(
            "First confirmed New Mexico HPS case of 2026, per the New Mexico "
            "DOH HPS page. NNDSS currently shows 2 for NM 2026 (NNDSS leads "
            "in this direction). Exact onset date not stated on source page."
        ),
        show_on_map=False,
    ))

    return records
