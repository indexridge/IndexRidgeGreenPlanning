#!/usr/bin/env python3
"""Fetch a low-risk UK green planning sample from official open data.

This script intentionally uses only the official Planning Data API and emits
attribution/licence metadata alongside the generated sample. It does not scrape
news, copy third-party editorial material, or contact prospects.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

API_URL = "https://www.planning.data.gov.uk/entity.json"
DATASET_META_URL = "https://www.planning.data.gov.uk/dataset/planning-application.json"
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "outputs"

KEYWORDS = {
    "solar": [r"\bsolar\b", r"\bphotovoltaic\b", r"\bPV\b", r"solar panel", r"solar farm"],
    "battery_storage": [r"\bbattery\b", r"\bBESS\b", r"energy storage", r"storage system"],
    "ev_charging": [r"EV charging", r"electric vehicle", r"charging point", r"charge point"],
    "heat_pump_retrofit": [r"heat pump", r"air source", r"ground source", r"retrofit"],
    "grid_energy": [r"substation", r"grid connection", r"renewable energy", r"energy centre"],
}

DISCLAIMER = (
    "Informational public-data monitoring only; not planning, legal, investment, "
    "engineering, environmental, or regulatory advice. Verify against official sources."
)


@dataclass
class GreenPlanningRecord:
    reference: str
    decision_date: str
    entry_date: str
    organisation_entity: str
    categories: str
    matched_terms: str
    description: str
    source_entity_url: str
    source_dataset: str = "planning-application"
    licence: str = "Open Government Licence v3.0"
    attribution: str = "© Crown copyright and database right 2026"


def fetch_json(url: str, params: dict[str, str | int] | None = None) -> dict:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": "IndexRidgeGreenPlanningMVP/0.1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def classify(description: str) -> tuple[list[str], list[str]]:
    cats: list[str] = []
    terms: list[str] = []
    for category, patterns in KEYWORDS.items():
        for pattern in patterns:
            if re.search(pattern, description, flags=re.IGNORECASE):
                cats.append(category)
                terms.append(pattern.replace(r"\b", ""))
                break
    return cats, terms


def iter_entities(limit: int, max_pages: int) -> Iterable[dict]:
    offset = 0
    for _ in range(max_pages):
        payload = fetch_json(API_URL, {"dataset": "planning-application", "limit": limit, "offset": offset})
        entities = payload.get("entities") or []
        if not entities:
            break
        yield from entities
        offset += limit


def make_records(limit: int, max_pages: int) -> list[GreenPlanningRecord]:
    records: list[GreenPlanningRecord] = []
    for entity in iter_entities(limit, max_pages):
        description = (entity.get("description") or "").strip()
        categories, terms = classify(description)
        if not categories:
            continue
        entity_id = entity.get("entity", "")
        source_entity_url = f"https://www.planning.data.gov.uk/entity/{entity_id}" if entity_id else ""
        records.append(
            GreenPlanningRecord(
                reference=str(entity.get("reference") or ""),
                decision_date=str(entity.get("decision-date") or ""),
                entry_date=str(entity.get("entry-date") or ""),
                organisation_entity=str(entity.get("organisation-entity") or ""),
                categories=";".join(categories),
                matched_terms=";".join(terms),
                description=description,
                source_entity_url=source_entity_url,
            )
        )
    return records


def write_outputs(records: list[GreenPlanningRecord], metadata: dict) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    csv_path = OUTPUT_DIR / "green_planning_sample.csv"
    json_path = OUTPUT_DIR / "green_planning_sample.json"
    md_path = OUTPUT_DIR / "green_planning_sample.md"
    licence_path = OUTPUT_DIR / "source_licences.json"

    rows = [asdict(record) for record in records]

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(GreenPlanningRecord.__annotations__.keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(
        json.dumps(
            {
                "generated_at_utc": generated_at,
                "record_count": len(records),
                "disclaimer": DISCLAIMER,
                "records": rows,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    licence_payload = {
        "generated_at_utc": generated_at,
        "source": "Planning Data platform planning-application dataset",
        "metadata_url": DATASET_META_URL,
        "licence": metadata.get("licence-text") or "Open Government Licence v3.0",
        "attribution": metadata.get("attribution-text") or "© Crown copyright and database right 2026",
        "dataset_entity_count": metadata.get("entity-count"),
        "disclaimer": DISCLAIMER,
    }
    licence_path.write_text(json.dumps(licence_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Green Planning Sample Digest",
        "",
        f"Generated: {generated_at}",
        "",
        f"Records found: {len(records)}",
        "",
        f"> {DISCLAIMER}",
        "",
        "Source: Planning Data platform `planning-application` dataset.",
        f"Attribution: {licence_payload['attribution']}",
        "",
    ]
    for record in records[:25]:
        lines.extend(
            [
                f"## {record.reference or 'No reference'} — {record.categories}",
                "",
                f"- Decision date: {record.decision_date or 'not supplied'}",
                f"- Organisation entity: {record.organisation_entity or 'not supplied'}",
                f"- Matched terms: {record.matched_terms}",
                f"- Source: {record.source_entity_url}",
                f"- Description: {record.description}",
                "",
            ]
        )
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch green-planning public-data sample")
    parser.add_argument("--limit", type=int, default=500, help="API page size")
    parser.add_argument("--max-pages", type=int, default=3, help="Maximum API pages to fetch")
    args = parser.parse_args()

    if args.limit < 1 or args.limit > 5000:
        parser.error("--limit must be between 1 and 5000")
    if args.max_pages < 1 or args.max_pages > 50:
        parser.error("--max-pages must be between 1 and 50")

    metadata = fetch_json(DATASET_META_URL)
    records = make_records(args.limit, args.max_pages)
    write_outputs(records, metadata)
    print(f"OK fetched_pages={args.max_pages} page_size={args.limit} matching_records={len(records)} output_dir={OUTPUT_DIR}")
    if not records:
        print("WARNING: no keyword matches in fetched sample; increase --max-pages or add sources", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
