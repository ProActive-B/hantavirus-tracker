"""Normalized record schemas. Bump SCHEMA_VERSION when changing these."""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator

Confidence = Literal["confirmed", "probable", "signal"]

VIRUSES = {
    "Sin Nombre virus",
    "Andes virus",
    "Seoul virus",
    "Puumala virus",
    "Hantaan virus",
    "Dobrava-Belgrade virus",
    "Bayou virus",
    "Black Creek Canal virus",
    "Choclo virus",
    "hantavirus (unspecified)",
}


class Incident(BaseModel):
    """One hantavirus incident — confirmed case, cluster, or outbreak signal.

    ``show_on_map`` lets a record appear in feeds + RSS for citation while being
    suppressed from the map. Useful when several authoritative reports describe
    the same cluster (e.g., CDC HAN + multiple WHO DONs about MV Hondius) and we
    want one map marker but every report in the feed.
    """

    id: str
    title: str
    location: str
    lon: float = Field(..., ge=-180, le=180)
    lat: float = Field(..., ge=-90, le=90)
    virus: str
    cases: int | None = None
    deaths: int | None = None
    confidence: Confidence
    reported: date
    ingested_at: datetime
    source_name: str
    source_url: HttpUrl
    summary: str
    show_on_map: bool = True

    @field_validator("virus")
    @classmethod
    def virus_known(cls, v: str) -> str:
        if v not in VIRUSES:
            # don't crash, just normalize to unspecified so downstream renders
            return "hantavirus (unspecified)"
        return v

    @field_validator("cases", "deaths")
    @classmethod
    def non_negative(cls, v: int | None) -> int | None:
        if v is None:
            return None
        if v < 0:
            raise ValueError("negative count")
        return v

    def to_feature(self) -> dict:
        return {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [self.lon, self.lat]},
            "properties": {
                "id": self.id,
                "title": self.title,
                "location": self.location,
                "virus": self.virus,
                "cases": self.cases,
                "deaths": self.deaths,
                "confidence": self.confidence,
                "reported": self.reported.isoformat(),
                "ingested_at": self.ingested_at.isoformat(),
                "source_name": self.source_name,
                "source_url": str(self.source_url),
                "summary": self.summary,
            },
        }


class FeedItem(BaseModel):
    id: str
    title: str
    source: str
    source_url: HttpUrl
    published: date
    summary: str
    tier: Confidence
    citation: str

    def to_dict(self) -> dict:
        d = self.model_dump()
        d["source_url"] = str(self.source_url)
        d["published"] = self.published.isoformat()
        return d
