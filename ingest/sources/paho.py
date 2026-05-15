"""PAHO regional bulletins. PAHO does not expose a clean RSS for hantavirus; the
PLISA platform is the structured source but requires per-country queries. For
now this fetcher is a placeholder — returns []. Replace with a real fetcher
when adding Argentina / Chile / Panama detail (the regional Andes-virus zone)."""
from __future__ import annotations

from ..schemas import Incident


def fetch() -> list[Incident]:
    return []
