"""ProMED-mail signal layer — currently a stub.

ProMED's free public RSS endpoints were discontinued after the 2023–2024
funding crisis. Every candidate URL audited 2026-05-14 returned 404:
- promedmail.org/promed-posts-rss/
- promedmail.org/feed/
- promedmail.org/rss
- promedmail.org/promed-rss-feed/

Restoring this signal source requires either:
1. A paid ProMED subscription with API access, OR
2. Scraping the public ProMED post listings (HTML; requires care because
   ProMED's content tone varies post-to-post and our normalizer would have
   to be especially conservative — every record produced here is and stays
   ``confidence='signal'``).

Until then this fetcher returns empty and the absence of ProMED signals
is honestly reflected in the data, not papered over.
"""
from __future__ import annotations

from ..schemas import Incident


def fetch() -> list[Incident]:
    return []
