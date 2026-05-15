"""PubMed — NCBI E-utilities. Recent peer-reviewed papers indexed under the
``hantavirus`` MeSH term. This is the academic signal layer — what used to be
ProMED's job before they took the free RSS down.

Pipeline (per E-utilities best practice):
1. ``esearch``  — find PMIDs for hantavirus[MeSH] published in the current
   and previous calendar year, sorted newest first.
2. ``esummary`` — pull title / pubdate / journal / first-author for each.

Records emitted have ``confidence='signal'`` and ``show_on_map=False`` —
PubMed records aren't localized outbreaks, they're citations. They appear in
the feed (and RSS) for researchers and journalists.

API rate limits: 3 req/sec without API key, 10 req/sec with one. We make two
calls per ingest run, well under any limit.

Documentation: https://www.ncbi.nlm.nih.gov/books/NBK25500/
"""
from __future__ import annotations

from datetime import date, datetime

from dateutil import parser as dateparser

from ..normalize import stable_id
from ..schemas import Incident
from ._common import http_client, now_utc

ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

# NCBI National Library of Medicine, Bethesda MD — coords unused (show_on_map=False).
NLM_LON, NLM_LAT = -77.099722, 38.998333

MAX_RESULTS = 25


def _esearch(term: str, retmax: int) -> list[str]:
    params = {
        "db": "pubmed",
        "term": term,
        "retmode": "json",
        "retmax": str(retmax),
        "sort": "date",
    }
    with http_client(timeout=15.0) as c:
        r = c.get(ESEARCH, params=params)
        r.raise_for_status()
        return r.json().get("esearchresult", {}).get("idlist", []) or []


def _esummary(pmids: list[str]) -> dict:
    if not pmids:
        return {}
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "json",
    }
    with http_client(timeout=15.0) as c:
        r = c.get(ESUMMARY, params=params)
        r.raise_for_status()
        return r.json().get("result", {})


def _parse_pubdate(raw: str | None) -> date | None:
    if not raw:
        return None
    try:
        return dateparser.parse(raw, default=datetime(date.today().year, 1, 1)).date()
    except Exception:
        return None


def fetch() -> list[Incident]:
    this_year = date.today().year
    last_year = this_year - 1
    term = f"hantavirus[MeSH] AND (\"{last_year}\"[DP] OR \"{this_year}\"[DP])"

    try:
        pmids = _esearch(term, MAX_RESULTS)
        result = _esummary(pmids)
    except Exception:
        return []

    out: list[Incident] = []
    n = now_utc()
    for pmid in pmids:
        item = result.get(pmid)
        if not item:
            continue
        title = (item.get("title") or "").strip()
        if not title:
            continue
        pubdate = _parse_pubdate(item.get("pubdate"))
        if not pubdate:
            continue
        journal = (item.get("source") or "").strip()
        authors = [a.get("name") for a in (item.get("authors") or []) if a.get("authtype") == "Author"]
        first_authors = ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else "")
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        summary = (
            f"{title} — {first_authors or 'authors not listed'}. "
            f"{journal}. PMID {pmid}."
        )
        out.append(Incident(
            id=stable_id("pubmed", pmid),
            title=f"PubMed — {title}",
            location=f"Peer-reviewed literature ({journal or 'journal not stated'})",
            lon=NLM_LON, lat=NLM_LAT,
            virus="hantavirus (unspecified)",
            cases=None, deaths=None,
            confidence="signal",
            reported=pubdate,
            ingested_at=n,
            source_name=f"PubMed (PMID {pmid}, {journal})" if journal else f"PubMed (PMID {pmid})",
            source_url=url,
            summary=summary[:500],
            show_on_map=False,
        ))
    return out
