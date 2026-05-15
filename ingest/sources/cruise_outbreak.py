"""Live fetcher for the 2026 South Atlantic Andes-virus cruise cluster.

Primary source: CDC HAN 528 (https://www.cdc.gov/han/php/notices/han00528.html).
Pulls the latest case / death numbers via tolerant regex scraping of the HAN
page. On any parse failure the fetcher returns a frozen snapshot whose values
are themselves taken verbatim from the HAN as of 2026-05-08 — so a stale fetch
still surfaces a primary-cited figure, never an invented one.

Output: a single Incident plus an ``extras`` dict (case breakdown, exposed
population, port-of-call list) used downstream by cruise_analysis.py.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime

from bs4 import BeautifulSoup

from ..normalize import stable_id
from ..schemas import Incident
from ._common import http_client, now_utc

HAN_URL = "https://www.cdc.gov/han/php/notices/han00528.html"

# Frozen 2026-05-08 snapshot. Used as the fallback if HAN parsing fails.
# Numbers below are taken verbatim from CDC HAN 528 as of that date.
FALLBACK = {
    "confirmed": 6,
    "suspected": 2,
    "deaths": 3,
    "exposed": 147,
    "passengers": 86,
    "crew": 61,
    "as_of": date(2026, 5, 8),
    "departure_date": date(2026, 4, 1),
    "departure_port": "Ushuaia, Argentina",
    "ports_of_call": [
        "Antarctica",
        "South Georgia Island",
        "Tristan da Cunha",
        "Saint Helena",
        "Ascension Island",
    ],
    "met_at": "Las Palmas, Canary Islands",
    "met_lon": -15.4365,
    "met_lat": 28.1235,
    "met_date": date(2026, 5, 7),
}


@dataclass
class CruiseFigures:
    confirmed: int
    suspected: int
    deaths: int
    exposed: int
    as_of: date
    parsed_from_live: bool
    source_name: str
    source_url: str


_WORD_NUM = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
}


def _wordnum_or_digits(token: str) -> int | None:
    token = token.strip().lower()
    if token.isdigit():
        return int(token)
    return _WORD_NUM.get(token)


_NUM = r"(\d{1,4}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty)"


def _try_parse_han() -> CruiseFigures | None:
    """Parse CDC HAN 528 with patterns matched to its actual phrasing.

    Target sentences (as of 2026-05-08 HAN):
      "As of May 8, 2026, WHO has reported eight cases
       (six confirmed and two suspected), including three deaths."
      "It carried 147 people (86 passengers and 61 crew) from 23 different
       countries."

    Tolerates word-form or digit-form numerals.
    """
    try:
        with http_client(timeout=15.0) as c:
            r = c.get(HAN_URL)
            if r.status_code != 200:
                return None
            soup = BeautifulSoup(r.text, "lxml")
            text = soup.get_text(" ", strip=True)
    except Exception:
        return None

    # "(six confirmed and two suspected)"
    m = re.search(
        rf"\(\s*{_NUM}\s+confirmed\s+and\s+{_NUM}\s+suspected\s*\)",
        text, re.I,
    )
    confirmed = _wordnum_or_digits(m.group(1)) if m else None
    suspected = _wordnum_or_digits(m.group(2)) if m else None

    # "including three deaths"  or  "X deaths"
    m = re.search(rf"including\s+{_NUM}\s+deaths?", text, re.I)
    if not m:
        m = re.search(rf"{_NUM}\s+deaths?", text, re.I)
    deaths = _wordnum_or_digits(m.group(1)) if m else None

    # "carried 147 people"  or  "147 people"
    m = re.search(rf"(?:carried\s+)?{_NUM}\s+people", text, re.I)
    exposed = _wordnum_or_digits(m.group(1)) if m else None

    # "As of <Month> <day>, <year>"
    m = re.search(
        r"as of\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),\s+(\d{4})",
        text, re.I,
    )
    as_of: date | None = None
    if m:
        try:
            as_of = datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}", "%B %d %Y").date()
        except ValueError:
            as_of = None

    if None in (confirmed, suspected, deaths, exposed) or as_of is None:
        return None

    # Monotonicity check: outbreak figures should never go backwards versus the
    # 2026-05-08 baseline. If they do, treat as a parse error and fall back.
    if (
        confirmed < FALLBACK["confirmed"]
        or confirmed + suspected < FALLBACK["confirmed"] + FALLBACK["suspected"]
        or deaths < FALLBACK["deaths"]
        or exposed != FALLBACK["exposed"]  # exposed pop is fixed; mismatch = parse error
    ):
        return None

    return CruiseFigures(
        confirmed=confirmed,
        suspected=suspected,
        deaths=deaths,
        exposed=exposed,
        as_of=as_of,
        parsed_from_live=True,
        source_name=f"CDC HAN 528 ({as_of.isoformat()})",
        source_url=HAN_URL,
    )


def _who_latest_figures() -> CruiseFigures | None:
    """Consult the WHO event page; return the freshest DON's figures as CruiseFigures."""
    # Imported lazily to avoid a cycle when who_event is loaded first.
    from .who_event import get_dons

    dons = get_dons()
    if not dons:
        return None
    d = dons[0]  # newest first
    don_slug = d.url.rstrip("/").rsplit("/", 1)[-1]
    # Monotonicity: WHO must not regress versus the verified 2026-05-08 snapshot.
    if d.confirmed < FALLBACK["confirmed"]:
        return None
    if d.confirmed + d.suspected < FALLBACK["confirmed"] + FALLBACK["suspected"]:
        return None
    if d.deaths < FALLBACK["deaths"]:
        return None
    return CruiseFigures(
        confirmed=d.confirmed,
        suspected=d.suspected,
        deaths=d.deaths,
        exposed=FALLBACK["exposed"],  # WHO doesn't always restate; exposed cohort is fixed at 147
        as_of=d.as_of,
        parsed_from_live=True,
        source_name=f"WHO Disease Outbreak News ({don_slug})",
        source_url=d.url,
    )


def get_figures() -> CruiseFigures:
    """Return the freshest authoritative figures for the cruise cluster.

    Consults both CDC HAN 528 and the WHO emergency-event page (which links to
    dated DON articles). Whichever has the most recent ``as_of`` wins. On total
    failure of both, falls back to the verified 2026-05-08 snapshot — still
    primary-cited, just stale.
    """
    candidates: list[CruiseFigures] = []
    cdc = _try_parse_han()
    if cdc is not None:
        candidates.append(cdc)
    who = _who_latest_figures()
    if who is not None:
        candidates.append(who)
    if candidates:
        return max(candidates, key=lambda c: c.as_of)
    return CruiseFigures(
        confirmed=FALLBACK["confirmed"],
        suspected=FALLBACK["suspected"],
        deaths=FALLBACK["deaths"],
        exposed=FALLBACK["exposed"],
        as_of=FALLBACK["as_of"],
        parsed_from_live=False,
        source_name=f"CDC HAN 528 ({FALLBACK['as_of'].isoformat()}, frozen snapshot)",
        source_url=HAN_URL,
    )


def fetch() -> list[Incident]:
    f = get_figures()
    total_cases = f.confirmed + f.suspected
    return [
        Incident(
            # ID stable across source-of-record changes — this is one cluster,
            # one map point, even if the freshest authority shifts CDC ↔ WHO.
            id=stable_id("cluster", "mv-hondius-2026"),
            title="Andes-virus cluster — MV Hondius cruise (South Atlantic), multi-country",
            location=(
                f"MV Hondius; met by CDC at {FALLBACK['met_at']} "
                f"({FALLBACK['met_date'].isoformat()}); passengers under monitoring across "
                f"United Kingdom, France, Spain, United States, Argentina, Chile"
            ),
            lon=FALLBACK["met_lon"],
            lat=FALLBACK["met_lat"],
            virus="Andes virus",
            cases=total_cases,
            deaths=f.deaths,
            confidence="confirmed",
            reported=f.as_of,
            ingested_at=now_utc(),
            source_name=f.source_name,
            source_url=f.source_url,
            summary=(
                f"{f.confirmed} confirmed and {f.suspected} probable/inconclusive "
                f"Andes-virus cases on the MV Hondius, departed {FALLBACK['departure_port']} on "
                f"{FALLBACK['departure_date'].isoformat()} with stops in "
                f"{', '.join(FALLBACK['ports_of_call'])}. "
                f"CDC met the ship at {FALLBACK['met_at']} on "
                f"{FALLBACK['met_date'].isoformat()}. "
                f"{f.deaths} deaths reported. Andes virus is the only hantavirus with "
                f"documented person-to-person transmission."
            ),
        )
    ]
