"""Shared HTTP helpers and US state centroids."""
from __future__ import annotations

from datetime import datetime, timezone

import httpx

USER_AGENT = "hantavirus-tracker/0.1 (+https://github.com/) contact: brandon@newtonstars.org"

# Map from full state name (as it appears in CDC NNDSS rows) to postal abbreviation.
US_STATE_NAME_TO_ABBR: dict[str, str] = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA", "West Virginia": "WV",
    "Wisconsin": "WI", "Wyoming": "WY",
}

# US state centroids (approx, decimal degrees) — used because CDC withholds
# county-level hantavirus data for privacy.
US_STATE_CENTROIDS: dict[str, tuple[float, float]] = {
    "AL": (-86.79113, 32.806671), "AK": (-152.404419, 61.370716),
    "AZ": (-111.431221, 33.729759), "AR": (-92.373123, 34.969704),
    "CA": (-119.681564, 36.116203), "CO": (-105.311104, 39.059811),
    "CT": (-72.755371, 41.597782), "DE": (-75.507141, 39.318523),
    "FL": (-81.686783, 27.766279), "GA": (-83.643074, 33.040619),
    "HI": (-157.498337, 21.094318), "ID": (-114.478828, 44.240459),
    "IL": (-88.986137, 40.349457), "IN": (-86.258278, 39.849426),
    "IA": (-93.210526, 42.011539), "KS": (-96.726486, 38.5266),
    "KY": (-84.670067, 37.66814), "LA": (-91.867805, 31.169546),
    "ME": (-69.381927, 44.693947), "MD": (-76.802101, 39.063946),
    "MA": (-71.530106, 42.230171), "MI": (-84.536095, 43.326618),
    "MN": (-93.900192, 45.694454), "MS": (-89.678696, 32.741646),
    "MO": (-92.288368, 38.456085), "MT": (-110.454353, 46.921925),
    "NE": (-98.268082, 41.12537), "NV": (-117.055374, 38.313515),
    "NH": (-71.563896, 43.452492), "NJ": (-74.521011, 40.298904),
    "NM": (-106.248482, 34.840515), "NY": (-74.948051, 42.165726),
    "NC": (-79.806419, 35.630066), "ND": (-99.784012, 47.528912),
    "OH": (-82.764915, 40.388783), "OK": (-96.928917, 35.565342),
    "OR": (-122.070938, 44.572021), "PA": (-77.209755, 40.590752),
    "RI": (-71.51178, 41.680893), "SC": (-80.945007, 33.856892),
    "SD": (-99.438828, 44.299782), "TN": (-86.692345, 35.747845),
    "TX": (-97.563461, 31.054487), "UT": (-111.862434, 40.150032),
    "VT": (-72.710686, 44.045876), "VA": (-78.169968, 37.769337),
    "WA": (-121.490494, 47.400902), "WV": (-80.954453, 38.491226),
    "WI": (-89.616508, 44.268543), "WY": (-107.30249, 42.755966),
}


def http_client(timeout: float = 20.0) -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
        timeout=timeout,
        follow_redirects=True,
    )


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
