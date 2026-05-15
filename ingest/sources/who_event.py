"""WHO Emergency Event page + linked Disease Outbreak News for the 2026
hantavirus cluster.

Anchor URL (provided by site operator, verified 2026-05-14):
    https://www.who.int/emergencies/emergency-events/item/2026-e000227

This event page links to one or more WHO DON articles (e.g. DON599, DON600,
DON601). Each DON is a snapshot of the outbreak at a specific date with
verbatim case/death/exposure counts. We pull each linked DON, parse its
figures with regexes tuned to WHO's actual phrasing, and emit one Incident
per DON. All emitted Incidents have ``show_on_map=False`` because the cruise
cluster already has a single map marker produced by ``cruise_outbreak``
(which itself now consults this module to pick the freshest authority).

Pattern matches:
- "As of <Month> <day>(, <year>)?"
- "total of <N> cases" or "<N> cases"
- "<N> confirmed"
- "<N> probable" or "<N> suspected"
- "<N> deaths"
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime

from bs4 import BeautifulSoup

from ..normalize import stable_id
from ..schemas import Incident
from ._common import http_client, now_utc

EVENT_URL = "https://www.who.int/emergencies/emergency-events/item/2026-e000227"
EVENT_ID = "2026-E000227"

# Las Palmas, Canary Islands — same canonical map location used by cruise_outbreak.
# Incidents here have show_on_map=False so coordinates are present but unused;
# they're kept for symmetry with the rest of the schema.
MET_LON = -15.4365
MET_LAT = 28.1235

_NUM = r"(\d{1,4}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)"
_WORD_NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
}


def _wordnum(t: str) -> int | None:
    t = t.strip().lower()
    if t.isdigit():
        return int(t)
    return _WORD_NUM.get(t)


@dataclass
class DONFigures:
    url: str
    as_of: date
    confirmed: int
    suspected: int   # probable + inconclusive — anything-not-confirmed
    deaths: int
    raw_text: str    # short excerpt for the feed summary


def _parse_don(url: str) -> DONFigures | None:
    try:
        with http_client(timeout=15.0) as c:
            r = c.get(url)
            if r.status_code != 200:
                return None
            soup = BeautifulSoup(r.text, "lxml")
            text = soup.get_text(" ", strip=True)
    except Exception:
        return None

    # "As of <Month> <day>, <year>"  (year optional — WHO sometimes omits it)
    m = re.search(
        r"as of\s+(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)(?:\s+(\d{4}))?",
        text, re.I,
    )
    if not m:
        m = re.search(
            r"as of\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?:,\s+(\d{4}))?",
            text, re.I,
        )
        if not m:
            return None
        month, day, year = m.group(1), m.group(2), m.group(3) or "2026"
    else:
        day, month, year = m.group(1), m.group(2), m.group(3) or "2026"
    try:
        as_of = datetime.strptime(f"{month} {day} {year}", "%B %d %Y").date()
    except ValueError:
        return None

    # "total of N cases"  (preferred)  OR  "N cases" (fallback)
    m = re.search(rf"total of\s+{_NUM}\s+cases?", text, re.I)
    if not m:
        m = re.search(rf"{_NUM}\s+cases?", text, re.I)
    total = _wordnum(m.group(1)) if m else None

    # "N confirmed"  (this is what we want; ignore "lab-confirmed" superset)
    m = re.search(rf"{_NUM}\s+(?:laboratory[- ])?confirmed", text, re.I)
    confirmed = _wordnum(m.group(1)) if m else None

    # "N deaths" — only the first match (the rest may be sub-clauses)
    m = re.search(rf"{_NUM}\s+deaths?", text, re.I)
    deaths = _wordnum(m.group(1)) if m else None

    if None in (total, confirmed, deaths) or total < confirmed:
        return None

    suspected = total - confirmed

    # Short excerpt around the "as of" sentence for the feed summary
    idx = text.lower().find("as of")
    excerpt = text[idx : idx + 360] if idx >= 0 else text[:360]

    return DONFigures(
        url=url,
        as_of=as_of,
        confirmed=confirmed,
        suspected=suspected,
        deaths=deaths,
        raw_text=excerpt,
    )


def _collect_don_urls() -> list[str]:
    try:
        with http_client(timeout=15.0) as c:
            r = c.get(EVENT_URL)
            if r.status_code != 200:
                return []
            soup = BeautifulSoup(r.text, "lxml")
    except Exception:
        return []

    urls: list[str] = []
    for a in soup.select("a[href*='/disease-outbreak-news/item/']"):
        href = a.get("href", "")
        if not href.startswith("http"):
            href = "https://www.who.int" + href
        if href not in urls:
            urls.append(href)
    return urls


def get_dons() -> list[DONFigures]:
    """All parsed DONs linked from the event page, sorted newest first."""
    parsed: list[DONFigures] = []
    for url in _collect_don_urls():
        f = _parse_don(url)
        if f is not None:
            parsed.append(f)
    return sorted(parsed, key=lambda d: d.as_of, reverse=True)


def fetch() -> list[Incident]:
    out: list[Incident] = []
    n = now_utc()
    for d in get_dons():
        don_slug = d.url.rstrip("/").rsplit("/", 1)[-1]  # e.g., "2026-DON601"
        total = d.confirmed + d.suspected
        out.append(Incident(
            id=stable_id("who-don", d.url),
            title=f"WHO DON — Hantavirus cluster, cruise ship ({don_slug})",
            location=(
                "MV Hondius (Dutch-flagged cruise ship); passengers under monitoring "
                "in United Kingdom, France, Spain, United States, Argentina, Chile"
            ),
            lon=MET_LON, lat=MET_LAT,
            virus="Andes virus",
            cases=total, deaths=d.deaths,
            confidence="confirmed",
            reported=d.as_of,
            ingested_at=n,
            source_name=f"WHO Disease Outbreak News ({don_slug})",
            source_url=d.url,
            summary=d.raw_text,
            show_on_map=False,
        ))
    return out
