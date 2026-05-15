"""Hantavirus-vs-COVID comparison table. Static, vetted; updated by `spread-analyst`."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


COMPARISON_ROWS = [
    {
        "metric": "Pathogen",
        "hantavirus": "Bunyavirales: Hantaviridae (Sin Nombre, Andes, others)",
        "covid19": "Coronaviridae: SARS-CoV-2",
    },
    {
        "metric": "Primary reservoir",
        "hantavirus": "Rodents (deer mice, rats, voles)",
        "covid19": "Bats (with intermediate-host hypothesis)",
    },
    {
        "metric": "Human-to-human spread",
        "hantavirus": "Rare; documented only for Andes virus",
        "covid19": "Sustained, airborne, primary route",
        "note": "Most hantaviruses do not transmit between people.",
    },
    {
        "metric": "Incubation period",
        "hantavirus": "4–42 days (median ~14)",
        "covid19": "2–14 days (median ~5)",
    },
    {
        "metric": "Case fatality rate",
        "hantavirus": "~38% for HPS (CDC); 1–15% for HFRS depending on virus species",
        "covid19": "Variable by variant and demographics; pandemic-era IFR ~0.5–1%",
        "note": "Hantavirus CFR is among the highest of any common viral respiratory disease.",
    },
    {
        "metric": "Reported case scale",
        "hantavirus": "United States: 890 cumulative HPS cases 1993–2023 (CDC). Global: HFRS dominates totals, concentrated in East Asia.",
        "covid19": "WHO has recorded hundreds of millions of confirmed cases globally since 2020.",
        "note": "Hantavirus and COVID-19 are not comparable at outbreak scale — listed here for context.",
    },
    {
        "metric": "Vaccine",
        "hantavirus": "None licensed in US or EU",
        "covid19": "Multiple licensed (mRNA, viral-vector, protein-subunit)",
    },
    {
        "metric": "Antiviral treatment",
        "hantavirus": "Supportive care only; ribavirin investigational for HFRS",
        "covid19": "Nirmatrelvir/ritonavir, remdesivir, molnupiravir (licensed)",
    },
    {
        "metric": "Geographic distribution",
        "hantavirus": "Americas (HPS), Europe & Asia (HFRS); reservoir-bound",
        "covid19": "Global; established human circulation",
    },
    {
        "metric": "Public-health response level",
        "hantavirus": "Surveillance + exposure prevention (rodent control)",
        "covid19": "Routine respiratory-virus seasonal management",
    },
]


def write_comparison() -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rows": COMPARISON_ROWS,
    }
    (DATA_DIR / "comparison.json").write_text(json.dumps(payload, indent=2) + "\n")
