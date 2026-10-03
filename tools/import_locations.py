#!/usr/bin/env python3
"""Načte polohy prostorů z database/venue_locations.csv do tabulky venue_locations."""
from __future__ import annotations

import csv
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "theatrodb.sqlite"
SCHEMA_PATH = ROOT / "database" / "schema.sql"
CSV_PATH = ROOT / "database" / "venue_locations.csv"

PRECISIONS = {"exact", "approx", "city"}


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    venue_ids = dict(conn.execute("SELECT slug, id FROM venues"))

    imported = 0
    with CSV_PATH.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            slug = row["slug"].strip()
            venue_id = venue_ids.get(slug)
            if venue_id is None:
                print(f"Přeskočeno, neznámý prostor: {slug}")
                continue
            precision = row["precision"].strip() or "city"
            if precision not in PRECISIONS:
                raise SystemExit(f"{slug}: neplatná přesnost '{precision}' (povoleno: {', '.join(sorted(PRECISIONS))})")
            conn.execute(
                """
                INSERT INTO venue_locations (venue_id, latitude, longitude, precision, address, source, note)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(venue_id) DO UPDATE SET
                    latitude = excluded.latitude,
                    longitude = excluded.longitude,
                    precision = excluded.precision,
                    address = excluded.address,
                    source = excluded.source,
                    note = excluded.note,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    venue_id,
                    float(row["latitude"]),
                    float(row["longitude"]),
                    precision,
                    row["address"].strip() or None,
                    row["source"].strip() or None,
                    row["note"].strip() or None,
                ),
            )
            imported += 1

    conn.commit()
    missing = conn.execute(
        "SELECT city, name FROM venues WHERE id NOT IN (SELECT venue_id FROM venue_locations) ORDER BY city"
    ).fetchall()
    print(f"Importováno {imported} poloh do {DB_PATH}")
    for city, name in missing:
        print(f"Bez polohy: {city} · {name}")


if __name__ == "__main__":
    main()
