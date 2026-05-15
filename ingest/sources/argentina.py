"""Argentina — Boletín Epidemiológico Nacional (BEN), Ministerio de Salud.

Hantavirus is endemic in Argentina (Andes virus in Patagonia, Sin Nombre-like
strains farther north). The BEN publishes weekly updates as both a PDF and a
news article. PDFs aren't easily machine-parseable in this pipeline, so we
target the HTML news articles at:

    https://www.argentina.gob.ar/noticias/actualizacion-del-boletin-epidemiologico-nacional-de-la-semana-ndeg-<W>
    https://www.argentina.gob.ar/noticias/actualizacion-del-boletin-epidemiologico-nacional-de-la-se-ndeg-<W>

Strategy on each ingest:
1. Fetch the current year's BEN listing page, extract the news-article URLs.
2. Walk newest first; for each, fetch and regex-search for the season-total
   sentence ("El total de casos de toda la temporada YYYY-YYYY asciende a N
   confirmados.").
3. On success, emit one Incident with the cumulative figure.
4. On total failure, fall back to the verified 2025-2026 SE-17 snapshot
   (102 confirmed) — still primary-sourced to BEN SE-17/2026.
"""
from __future__ import annotations

import re
from datetime import date
from dataclasses import dataclass

from bs4 import BeautifulSoup

from ..normalize import stable_id
from ..schemas import Incident
from ._common import http_client, now_utc

# Argentina national centroid — roughly Córdoba, midway between Buenos Aires and the south.
AR_LON, AR_LAT = -63.6167, -38.4161

LISTING_URLS = [
    "https://www.argentina.gob.ar/salud/boletin-epidemiologico-nacional/boletines-2026",
    "https://www.argentina.gob.ar/salud/boletin-epidemiologico-nacional/boletines-2025",
]

# Verified 2026-05-14 from BEN SE-17/2026 news article.
FALLBACK = {
    "season": "2025-2026",
    "se": 17,
    "se_year": 2026,
    "confirmed_total": 102,
    "deaths_in_season_text": "three deaths in the MV Hondius cluster; season-wide deaths not separately stated",
    "regional": "Centro region 54% (Buenos Aires Province 43); NOA 36 cases (Salta 83%)",
    "reported": date(2026, 5, 8),  # SE-17 ends Saturday 2026-04-25 by ISO calc; BEN typical publication ~2 wks after
    "source_url": "https://www.argentina.gob.ar/noticias/actualizacion-del-boletin-epidemiologico-nacional-de-la-semana-ndeg-17",
    "source_name": "Argentina BEN SE-17/2026",
}


@dataclass
class ARFigures:
    confirmed_total: int
    season: str
    se: int
    se_year: int
    reported: date
    source_url: str
    source_name: str
    summary: str
    parsed_from_live: bool


_SEASON_TOTAL_RE = re.compile(
    r"(?:total|asciende(?:n)?)\s+(?:de\s+casos\s+)?(?:de\s+toda\s+la\s+temporada\s+)?(\d{4})-(\d{4})\s+(?:asciende(?:n)?\s+a\s+)?(\d{1,4})\s+confirmad",
    re.I,
)
_SE_RE = re.compile(r"semana\s+(?:epidemiol[oó]gica\s+)?(?:n[°ºo°]\s*)?(\d{1,2})", re.I)


def _list_news_urls() -> list[str]:
    urls: list[str] = []
    for listing in LISTING_URLS:
        try:
            with http_client(timeout=15.0) as c:
                r = c.get(listing)
                if r.status_code != 200:
                    continue
                soup = BeautifulSoup(r.text, "lxml")
        except Exception:
            continue
        for a in soup.select("a[href*='/noticias/']"):
            href = a.get("href", "")
            if "boletin-epidemiologico" not in href:
                continue
            if not href.startswith("http"):
                href = "https://www.argentina.gob.ar" + href
            if href not in urls:
                urls.append(href)
    return urls


def _parse_news_article(url: str) -> ARFigures | None:
    try:
        with http_client(timeout=15.0) as c:
            r = c.get(url)
            if r.status_code != 200:
                return None
            soup = BeautifulSoup(r.text, "lxml")
            text = soup.get_text(" ", strip=True)
    except Exception:
        return None

    m = _SEASON_TOTAL_RE.search(text)
    if not m:
        # try a simpler pattern just in case the season-syntax shifts
        m2 = re.search(r"asciende(?:n)?\s+a\s+(\d{1,4})\s+confirmad", text, re.I)
        if not m2:
            return None
        confirmed = int(m2.group(1))
        season = ""
    else:
        season = f"{m.group(1)}-{m.group(2)}"
        confirmed = int(m.group(3))

    if confirmed < FALLBACK["confirmed_total"]:
        # Monotonic guard against parser regression.
        return None

    se_match = _SE_RE.search(url) or _SE_RE.search(text)
    se = int(se_match.group(1)) if se_match else FALLBACK["se"]

    # Year hint from URL or fallback
    year_match = re.search(r"/(\d{4})/", url) or re.search(r"de\s+(\d{4})", text)
    se_year = int(year_match.group(1)) if year_match else FALLBACK["se_year"]

    return ARFigures(
        confirmed_total=confirmed,
        season=season or FALLBACK["season"],
        se=se,
        se_year=se_year,
        reported=date.today(),
        source_url=url,
        source_name=f"Argentina BEN SE-{se:02d}/{se_year}",
        summary=(
            f"Argentina BEN: {confirmed} confirmed hantavirus cases reported "
            f"for the {season or FALLBACK['season']} season through SE {se} of {se_year}. "
            f"Regional context (most recent BEN with breakdown): "
            f"{FALLBACK['regional']}."
        ),
        parsed_from_live=True,
    )


def get_figures() -> ARFigures:
    for url in _list_news_urls():
        f = _parse_news_article(url)
        if f is not None:
            return f
    return ARFigures(
        confirmed_total=FALLBACK["confirmed_total"],
        season=FALLBACK["season"],
        se=FALLBACK["se"],
        se_year=FALLBACK["se_year"],
        reported=FALLBACK["reported"],
        source_url=FALLBACK["source_url"],
        source_name=FALLBACK["source_name"],
        summary=(
            f"Argentina BEN: {FALLBACK['confirmed_total']} confirmed hantavirus cases "
            f"for the {FALLBACK['season']} season through SE {FALLBACK['se']} of "
            f"{FALLBACK['se_year']} (frozen snapshot — live parse unavailable this run). "
            f"Regional: {FALLBACK['regional']}."
        ),
        parsed_from_live=False,
    )


def fetch() -> list[Incident]:
    f = get_figures()
    return [
        Incident(
            id=stable_id("ar-ben", f"{f.season}"),
            title=f"Argentina — {f.confirmed_total} confirmed HPS cases, {f.season} season (BEN SE-{f.se:02d}/{f.se_year})",
            location="Argentina (Centro and NOA regions concentrate most cases)",
            lon=AR_LON, lat=AR_LAT,
            virus="Andes virus",
            cases=f.confirmed_total, deaths=None,
            confidence="confirmed",
            reported=f.reported,
            ingested_at=now_utc(),
            source_name=f.source_name,
            source_url=f.source_url,
            summary=f.summary,
        )
    ]
