"""ECDC weekly Communicable Disease Threats Report (CDTR) — RSS taxonomy feed.

Endpoint (verified 2026-05-14):
    https://www.ecdc.europa.eu/en/taxonomy/term/1505/feed

This feed publishes one entry per weekly CDTR. Each entry is a CDTR digest
covering multiple pathogens; we match on hantavirus keywords in the title
and summary, and emit a single Incident per matching weekly report. CDTR is
the canonical source of confirmed European outbreak status.
"""
from __future__ import annotations

import re

import feedparser
from dateutil import parser as dateparser

from ..normalize import stable_id
from ..schemas import Incident
from ._common import now_utc

ECDC_CDTR_RSS = "https://www.ecdc.europa.eu/en/taxonomy/term/1505/feed"
KEYWORDS = re.compile(r"hantavir|andes virus|puumala|seoul virus|HPS|HFRS", re.I)


def fetch() -> list[Incident]:
    out: list[Incident] = []
    try:
        feed = feedparser.parse(ECDC_CDTR_RSS)
        if feed.get("status") not in (200, None):
            return []
    except Exception:
        return []

    for entry in feed.entries:
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        if not KEYWORDS.search(title + " " + summary):
            continue
        link = entry.get("link", "")
        try:
            reported = dateparser.parse(entry.get("published", "")).date()
        except Exception:
            continue
        out.append(Incident(
            id=stable_id("ecdc-cdtr", link),
            title=f"ECDC — {title}",
            location="European Union / EEA — weekly threats summary",
            lon=18.063240, lat=59.334591,  # ECDC HQ; record is feed-only
            virus="hantavirus (unspecified)",
            cases=None, deaths=None,
            confidence="confirmed",
            reported=reported,
            ingested_at=now_utc(),
            source_name="ECDC Communicable Disease Threats Report",
            source_url=link,
            summary=summary[:500] or title,
            # Weekly CDTR is a meta-summary that mentions hantavirus alongside
            # other pathogens — not a localized incident worth a map marker.
            show_on_map=False,
        ))
    return out
