"""WHO Disease Outbreak News — currently a stub.

WHO discontinued the legacy RSS endpoint
``who.int/feeds/entity/csr/don/en/rss.xml`` and the new DON listing page
(``who.int/emergencies/disease-outbreak-news``) is a client-rendered SPA
that returns no machine-readable content on a static fetch.

Until we add a headless-browser scrape or WHO publishes a documented API,
this fetcher returns empty. The cruise cluster is already covered by
``cruise_outbreak`` (CDC HAN 528), and WHO's DON figures for the same
outbreak track that HAN, so the signal layer is not blind today.

When restoring:
- Headless-browser option: Playwright on the DON listing, filter by
  hantavirus keywords, emit Incident records with ``confidence='confirmed'``.
- Alternative: scrape the WHO News listing
  (``who.int/news?healthtopics=...&publishtypes=...``) which is still
  server-rendered.
"""
from __future__ import annotations

from ..schemas import Incident


def fetch() -> list[Incident]:
    return []
