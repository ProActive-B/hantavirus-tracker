"""Chile — MINSAL Departamento de Epidemiología hantavirus bulletins.

Currently a stub. As of 2026-05-14, ``epi.minsal.cl`` is behind Cloudflare's
WAF and returns 403 to every non-browser request — including those bearing
realistic Mozilla user-agent strings. Restoring live data from this source
requires either:

1. A headless-browser ingest path (Playwright with stealth), OR
2. Routing through a residential proxy (operational cost + complexity).

The PDF URL pattern is predictable —
    https://epi.minsal.cl/wp-content/uploads/<YYYY>/<MM>/Boletin_Epidemiologico_Hantavirus_SE_<WW>_<YYYY>.pdf
— but every direct fetch also 403s, so this isn't an HTML-vs-PDF issue.

Until that path is built, Chile data is absent. The cruise outbreak's genetic
sequencing (per Argentina's BEN) confirmed Andes virus 'present in southern
Argentina and Chile' — but we don't fabricate a Chile case count.
"""
from __future__ import annotations

from ..schemas import Incident


def fetch() -> list[Incident]:
    return []
