#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import re
import unicodedata
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "theatrodb.sqlite"
MANIFEST_DIR = ROOT / "database" / "manifests"

FILE_KIND_DIRS = {
    "document": "documents",
    "photo": "photos",
    "other": "other",
}


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_columns(conn: sqlite3.Connection) -> None:
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(venues)")}
    if "original_source_folder" not in columns:
        conn.execute("ALTER TABLE venues ADD COLUMN original_source_folder TEXT")


def slugify(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    normalized = "".join(ch for ch in decomposed if not unicodedata.combining(ch)).lower()
    return re.sub(r"[^a-z0-9]+", "-", normalized).strip("-") or "city"


def venue_target(venue: sqlite3.Row) -> Path:
    city_slug = slugify(venue["city"] or venue["slug"])
    if venue["status"] == "blacklisted":
        return ROOT / "venues" / "_blacklisted" / venue["country"] / city_slug / venue["slug"]
    return ROOT / "venues" / venue["country"] / city_slug / venue["slug"]


def folder_files(conn: sqlite3.Connection, venue_id: int) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            """
            SELECT id, path, filename, file_kind
            FROM source_files
            WHERE venue_id = ?
            ORDER BY file_kind, filename
            """,
            (venue_id,),
        )
    )


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def write_venue_readme(venue: sqlite3.Row, target: Path) -> None:
    readme = target / "README.md"
    content = f"""# {venue['city']} - {venue['name']}

- ID: {venue['id']}
- Země: {venue['country']}
- Typ: {venue['venue_type']}
- Stav: {venue['status']}
- Aktuální složka: {relative(target)}
- Původní složka: {venue['original_source_folder'] or venue['source_folder']}

## Struktura

- `source/documents` - původní technické dokumenty, PDF, DOCX, Pages, RTF.
- `source/photos` - původní fotografie a obrázky.
- `source/other` - ostatní zdrojové soubory.
- `notes` - ručně doplňované poznámky k prostoru.
- `exports` - budoucí výstupy, reporty a přehledy.
"""
    readme.write_text(content, encoding="utf-8")


def build_plan(conn: sqlite3.Connection) -> list[dict]:
    venues = list(
        conn.execute(
            """
            SELECT id, slug, city, name, country, venue_type, status, source_folder, original_source_folder
            FROM venues
            ORDER BY country, venue_type, city, name
            """
        )
    )
    plan: list[dict] = []
    for venue in venues:
        source_root = ROOT / venue["source_folder"]
        target_root = venue_target(venue)
        if source_root == target_root:
            continue
        files = folder_files(conn, venue["id"])
        plan.append(
            {
                "venue_id": venue["id"],
                "city": venue["city"],
                "name": venue["name"],
                "status": venue["status"],
                "from": relative(source_root),
                "to": relative(target_root),
                "files": [
                    {
                        "id": file["id"],
                        "from": file["path"],
                        "to": relative(
                            target_root
                            / "source"
                            / FILE_KIND_DIRS.get(file["file_kind"], "other")
                            / file["filename"]
                        ),
                    }
                    for file in files
                ],
            }
        )
    return plan


def apply_plan(conn: sqlite3.Connection, plan: list[dict]) -> None:
    with conn:
        ensure_columns(conn)
        for item in plan:
            target_root = ROOT / item["to"]
            source_root = ROOT / item["from"]
            if source_root.exists():
                if target_root.exists():
                    raise FileExistsError(f"Target already exists: {target_root}")
                target_root.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source_root), str(target_root))
            else:
                target_root.mkdir(parents=True, exist_ok=True)

            for subdir in ("source/documents", "source/photos", "source/other", "notes", "exports"):
                (target_root / subdir).mkdir(parents=True, exist_ok=True)

            for file_move in item["files"]:
                conn.execute(
                    "UPDATE source_files SET path = ? WHERE id = ?",
                    (file_move["to"], file_move["id"]),
                )

            conn.execute(
                """
                UPDATE venues
                SET original_source_folder = COALESCE(original_source_folder, source_folder),
                    source_folder = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (item["to"], item["venue_id"]),
            )

            venue = conn.execute("SELECT * FROM venues WHERE id = ?", (item["venue_id"],)).fetchone()
            write_venue_readme(venue, target_root)


def main() -> None:
    parser = argparse.ArgumentParser(description="Organize venue source folders.")
    parser.add_argument("--apply", action="store_true", help="Move files and update the database.")
    args = parser.parse_args()

    conn = connect()
    ensure_columns(conn)
    plan = build_plan(conn)

    print(f"Planned venue moves: {len(plan)}")
    for item in plan:
        print(f"- {item['from']} -> {item['to']} ({len(item['files'])} files)")

    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = MANIFEST_DIR / f"organize-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    manifest_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Manifest: {manifest_path}")

    if args.apply:
        apply_plan(conn, plan)
        print("Archive organized and database paths updated.")
    else:
        print("Dry run only. Re-run with --apply to move files.")


if __name__ == "__main__":
    main()
