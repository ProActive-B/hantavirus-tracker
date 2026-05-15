"""CDC NNDSS — weekly notifiable-disease counts via data.cdc.gov SODA API.

Dataset: ``x9gk-5huc`` (NNDSS Weekly Data, moved to data.cdc.gov in 2025).
We query the "Hantavirus pulmonary syndrome" label and emit one Incident per
US state per year (current YTD + prior year final week).

NNDSS field semantics (per CDC NNDSS Reader's Guide):
- ``m1`` — current-week count
- ``m2`` — current-year cumulative (YTD) ← what we use
- ``m3`` — previous-year same-week cumulative
- ``m4`` — previous-year final cumulative
- ``*_flag`` — data-quality flags: ``N`` = not notifiable in that state,
  ``NC`` = no cases reported, ``-`` = none (clean).

We use ``m2`` because it's the cumulative YTD figure, which is what the
public typically wants ("how many cases this year").
"""
from __future__ import annotations

from datetime import date, datetime

from ..normalize import stable_id
from ..schemas import Incident
from ._common import US_STATE_CENTROIDS, US_STATE_NAME_TO_ABBR, http_client, now_utc

DATASET_ID = "x9gk-5huc"
SODA_URL = f"https://data.cdc.gov/resource/{DATASET_ID}.json"
DATASET_LANDING = f"https://data.cdc.gov/NNDSS/NNDSS-Weekly-Data/{DATASET_ID}"

LABEL = "Hantavirus pulmonary syndrome"


def _mmwr_week_end(year: int, week: int) -> date:
    """Approximate MMWR week-ending Saturday for the given year/week.

    MMWR weeks differ from ISO weeks: an MMWR year can have 53 weeks where the
    ISO calendar reports only 52, and the first MMWR week of a year is the
    first one ending on a Saturday in January. We approximate by:

    1. trying ISO ``fromisocalendar(year, week, 6)`` (ISO weekday 6 = Saturday),
    2. falling back to ``Dec 31 of <year>`` when ISO rejects the week
       (this only happens for MMWR week 53 in certain years; the exact
       calendar day is unimportant for a year-end annual aggregate).
    """
    try:
        return datetime.fromisocalendar(year, week, 6).date()
    except ValueError:
        return date(year, 12, 31)


def _query_max_week(year: int) -> int | None:
    """Find the highest week number with hantavirus data for the given year."""
    params = {
        "$where": f"label = '{LABEL}' AND year = '{year}'",
        "$select": "max(week) as max_week",
    }
    with http_client(timeout=15.0) as c:
        r = c.get(SODA_URL, params=params)
        r.raise_for_status()
        data = r.json()
    if not data or not data[0].get("max_week"):
        return None
    try:
        return int(data[0]["max_week"])
    except (ValueError, TypeError):
        return None


def _query_state_rows(year: int, week: int) -> list[dict]:
    params = {
        "$where": f"label = '{LABEL}' AND year = '{year}' AND week = '{week}'",
        "$select": "states,m2,m2_flag",
        "$limit": "200",
    }
    with http_client(timeout=15.0) as c:
        r = c.get(SODA_URL, params=params)
        r.raise_for_status()
        return r.json()


def _to_int(s: str | None) -> int | None:
    if not s:
        return None
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return None


def fetch() -> list[Incident]:
    today = date.today()
    out: list[Incident] = []
    n = now_utc()

    for year in (today.year - 1, today.year):
        week = _query_max_week(year)
        if not week:
            continue
        try:
            rows = _query_state_rows(year, week)
        except Exception:
            continue

        reported = _mmwr_week_end(year, week)
        if reported > today:
            # ISO week math can drift past today's date near year boundaries;
            # never claim a future reported-date.
            reported = today

        for row in rows:
            state_name = (row.get("states") or "").strip()
            abbr = US_STATE_NAME_TO_ABBR.get(state_name)
            if not abbr:
                continue  # skip Census-region aggregates, territories, "Total"
            centroid = US_STATE_CENTROIDS.get(abbr)
            if not centroid:
                continue
            cases = _to_int(row.get("m2"))
            if not cases or cases <= 0:
                continue
            lon, lat = centroid

            out.append(Incident(
                id=stable_id("nndss-hps", f"{abbr}-{year}-w{week}"),
                title=f"{state_name} — {cases} HPS case{'s' if cases != 1 else ''} (CDC NNDSS, {year} through wk {week})",
                location=f"{state_name}, USA (state aggregate)",
                lon=lon, lat=lat,
                virus="Sin Nombre virus",  # dominant US HPS species; surveillance label doesn't subspeciate
                cases=cases, deaths=None,
                confidence="confirmed",
                reported=reported,
                ingested_at=n,
                source_name=f"CDC NNDSS Weekly Data ({year} wk {week})",
                source_url=DATASET_LANDING,
                summary=(
                    f"{cases} hantavirus pulmonary syndrome case"
                    f"{'s' if cases != 1 else ''} reported by {state_name} to CDC NNDSS, "
                    f"year-to-date through MMWR week {week} of {year}. "
                    f"State-centroid placement; CDC withholds sub-state hantavirus "
                    f"data for patient privacy."
                ),
            ))

    return out
