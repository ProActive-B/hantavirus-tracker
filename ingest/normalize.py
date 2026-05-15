"""Aggregate, dedupe, and write the four frontend contract files."""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path

from .schemas import FeedItem, Incident

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


def stable_id(*parts: str) -> str:
    h = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()
    return h[:12]


def dedupe(records: list[Incident]) -> list[Incident]:
    seen: dict[str, Incident] = {}
    for r in records:
        key = r.id
        prev = seen.get(key)
        if prev is None or r.ingested_at > prev.ingested_at:
            seen[key] = r
    return sorted(seen.values(), key=lambda r: r.reported, reverse=True)


def write_geojson(records: list[Incident]) -> None:
    visible = [r for r in records if r.show_on_map]
    fc = {
        "type": "FeatureCollection",
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "count": len(visible),
            "total_records": len(records),
        },
        "features": [r.to_feature() for r in visible],
    }
    (DATA_DIR / "hantavirus.geojson").write_text(json.dumps(fc, indent=2) + "\n")


def write_feed(records: list[Incident]) -> None:
    # Suppress a feed-only (show_on_map=False) record only if a canonical
    # (show_on_map=True) record already cites the same source_url. This
    # collapses the "WHO DON601 snapshot" against the "MV Hondius cluster
    # Incident currently sourced to DON601" but leaves unrelated records
    # alone — e.g., NM 2025 and NM 2026 both cite the NM DOH HPS page and
    # must both survive.
    canonical_urls = {str(r.source_url) for r in records if r.show_on_map}
    kept = [r for r in records if r.show_on_map or str(r.source_url) not in canonical_urls]
    deduped = sorted(kept, key=lambda r: r.reported, reverse=True)

    items = []
    for r in deduped[:200]:
        cite = (
            f"{r.source_name}. ({r.reported.year}). {r.title}. "
            f"Retrieved {r.ingested_at.date()} from {r.source_url}."
        )
        items.append(
            FeedItem(
                id=r.id,
                title=r.title,
                source=r.source_name,
                source_url=r.source_url,
                published=r.reported,
                summary=r.summary,
                tier=r.confidence,
                citation=cite,
            ).to_dict()
        )
    (DATA_DIR / "feed.json").write_text(
        json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(), "items": items}, indent=2)
        + "\n"
    )


def write_overview(records: list[Incident]) -> None:
    today = date.today()
    # Only count canonical map records when summing — otherwise sequential WHO
    # DON snapshots of the same cluster triple-count the same cases/deaths.
    visible = [r for r in records if r.show_on_map]
    cases_90d = sum(
        (r.cases or 0) for r in visible if (today - r.reported).days <= 90
    )
    deaths_90d = sum(
        (r.deaths or 0) for r in visible if (today - r.reported).days <= 90
    )
    active = sum(1 for r in visible if (today - r.reported).days <= 180)
    lead = next(
        (r for r in visible if r.confidence == "confirmed" and (r.cases or 0) >= 5),
        visible[0] if visible else None,
    )
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "active": active,
        "cases_90d": cases_90d,
        "deaths_90d": deaths_90d,
        "lead_outbreak": {
            "id": lead.id if lead else "",
            "title": lead.title if lead else "—",
            "source_url": str(lead.source_url) if lead else "",
        } if lead else {"id": "", "title": "—", "source_url": ""},
    }
    (DATA_DIR / "overview.json").write_text(json.dumps(payload, indent=2) + "\n")
