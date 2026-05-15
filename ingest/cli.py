"""Ingest CLI — fetch all sources, normalize, write the four contract files."""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .comparison import write_comparison
from .cruise_analysis import write_cruise_analysis
from .normalize import dedupe, write_feed, write_geojson, write_overview
from .schemas import Incident
from .sources import argentina, cdc, chile, cruise_outbreak, ecdc, healthmap, nndss, paho, promed, pubmed, seed, who, who_event

app = typer.Typer(help="hantavirus tracker — ingest pipeline")
console = Console()


SOURCES = {
    "seed": seed.fetch,                         # locally-curated state-level aggregates
    "cruise_outbreak": cruise_outbreak.fetch,   # canonical cluster: CDC HAN ⊕ latest WHO DON
    "who_event": who_event.fetch,               # all WHO DON snapshots linked from 2026-E000227
    "nndss": nndss.fetch,                       # CDC NNDSS weekly per-state counts (data.cdc.gov)
    "argentina": argentina.fetch,               # MinSalud Argentina BEN (Andes-virus endemic zone)
    "chile": chile.fetch,                       # stub; Cloudflare WAF blocks scripted access
    "cdc": cdc.fetch,
    "who": who.fetch,                           # stub; legacy DON RSS gone
    "ecdc": ecdc.fetch,                         # CDTR weekly reports
    "paho": paho.fetch,
    "promed": promed.fetch,                     # stub; free RSS discontinued
    "pubmed": pubmed.fetch,                     # NCBI E-utilities — academic signal layer
    "healthmap": healthmap.fetch,
}


@app.command()
def run(
    sources: list[str] = typer.Option(None, "--source", "-s", help="Subset of sources; default = all"),
    fail_fast: bool = typer.Option(False, "--fail-fast", help="Exit non-zero on any source failure"),
    no_network: bool = typer.Option(False, "--no-network", help="Skip network sources, use seed only"),
) -> None:
    """Run ingest. Writes data/hantavirus.geojson, feed.json, overview.json, comparison.json."""
    selected = sources or list(SOURCES.keys())
    if no_network:
        selected = ["seed"]

    all_records: list[Incident] = []
    table = Table(title="Ingest results")
    table.add_column("source")
    table.add_column("records", justify="right")
    table.add_column("status")

    started = time.time()
    source_status: list[dict] = []
    had_failure = False
    for name in selected:
        fn = SOURCES.get(name)
        if fn is None:
            table.add_row(name, "-", "[yellow]unknown source[/]")
            source_status.append({"name": name, "ok": False, "records": 0, "error": "unknown source"})
            continue
        t0 = time.time()
        try:
            recs = fn()
            all_records.extend(recs)
            table.add_row(name, str(len(recs)), "[green]ok[/]")
            source_status.append({
                "name": name,
                "ok": True,
                "records": len(recs),
                "duration_s": round(time.time() - t0, 2),
                "error": None,
            })
        except Exception as e:
            had_failure = True
            table.add_row(name, "0", f"[red]fail: {e}[/]")
            source_status.append({
                "name": name,
                "ok": False,
                "records": 0,
                "duration_s": round(time.time() - t0, 2),
                "error": str(e)[:200],
            })
            if fail_fast:
                console.print(table)
                console.print(f"[red]Aborting on first failure[/]")
                sys.exit(1)

    deduped = dedupe(all_records)
    write_geojson(deduped)
    write_feed(deduped)
    write_overview(deduped)
    write_comparison()
    write_cruise_analysis()
    _write_status(source_status, len(deduped), time.time() - started)

    table.add_row("[bold]total[/]", f"[bold]{len(deduped)}[/]", "deduped")
    console.print(table)
    console.print(f"Wrote {len(deduped)} records at {datetime.now(timezone.utc).isoformat()}")

    if had_failure and fail_fast:
        sys.exit(1)


def _write_status(sources: list[dict], total_records: int, duration_s: float) -> None:
    """Always-written status file. Drives the 'last data refresh' footer and the
    source-health panel on /about. Keep small and stable in schema so the UI
    can rely on it.
    """
    data_dir = Path(__file__).resolve().parent.parent / "data"
    status = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_records": total_records,
        "duration_s": round(duration_s, 2),
        "sources": sources,
        "summary": {
            "ok": sum(1 for s in sources if s["ok"]),
            "failed": sum(1 for s in sources if not s["ok"]),
            "records_total": sum(s["records"] for s in sources),
        },
    }
    (data_dir / "_status.json").write_text(json.dumps(status, indent=2) + "\n")


@app.command(name="validate")
def validate() -> None:
    """Re-validate the committed data files against the current schema."""
    import json
    from pathlib import Path

    from .schemas import Incident as I

    data_dir = Path(__file__).resolve().parent.parent / "data"
    geo = json.loads((data_dir / "hantavirus.geojson").read_text())
    errors = 0
    for f in geo.get("features", []):
        try:
            p = f["properties"]
            I(
                id=p["id"], title=p["title"], location=p["location"],
                lon=f["geometry"]["coordinates"][0],
                lat=f["geometry"]["coordinates"][1],
                virus=p["virus"], cases=p.get("cases"), deaths=p.get("deaths"),
                confidence=p["confidence"], reported=p["reported"],
                ingested_at=p["ingested_at"],
                source_name=p["source_name"], source_url=p["source_url"],
                summary=p["summary"],
            )
        except Exception as e:
            console.print(f"[red]invalid record {p.get('id','?')}: {e}[/]")
            errors += 1
    if errors:
        console.print(f"[red]{errors} invalid records[/]")
        sys.exit(1)
    console.print(f"[green]{len(geo.get('features', []))} records valid[/]")


if __name__ == "__main__":
    app()
