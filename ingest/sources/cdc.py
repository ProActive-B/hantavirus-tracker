"""CDC HAN listing scraper — currently a stub.

The previous endpoint (cdc.gov/han/index.html) returned 404 in May 2026; CDC's
HAN listing URL has moved and a stable replacement isn't yet identified.
Specific HAN advisories are picked up via dedicated fetchers (see
``cruise_outbreak`` for HAN 528). When a fresh listing URL is confirmed,
restore the scraper here.
"""
from __future__ import annotations

from ..schemas import Incident


def fetch() -> list[Incident]:
    return []
