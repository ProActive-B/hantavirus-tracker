"""HealthMap signals. HealthMap is reduced from its peak and the public API is
unreliable; this fetcher is a placeholder. When the official API key flow is
re-established, populate with a real implementation."""
from __future__ import annotations

from ..schemas import Incident


def fetch() -> list[Incident]:
    return []
