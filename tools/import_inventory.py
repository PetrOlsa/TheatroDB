#!/usr/bin/env python3
from __future__ import annotations

import re
import sqlite3
import unicodedata
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "theatrodb.sqlite"
SCHEMA_PATH = ROOT / "database" / "schema.sql"
INCOMING_DIR = ROOT / "incoming" / "new_venues"

SK_HINTS = {
    "bratislava",
    "liskova",
    "senica",
    "trnava",
    "poprad",
    "kulturny",
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic"}
DOCUMENT_EXTENSIONS = {".docx", ".pdf", ".pages", ".rtf"}


def normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch)).lower()


def slugify(value: str) -> str:
    normalized = normalize(value)
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return normalized or "venue"


def classify_type(folder_name: str) -> str:
    text = normalize(folder_name)
    if "lesni divadlo" in text:
        return "outdoor_theatre"
    if "kino" in text:
        return "cinema"
    if "filharmonie" in text:
        return "concert_hall"
    if "sokolovna" in text:
        return "sokol_hall"
    if (
        "kulturni dum" in text
        or "dum kultury" in text
        or "dom kultury" in text
        or "kulturny dom" in text
        or "spolecensky dum" in text
        or text.startswith("dk ")
        or " msks" in text
        or text.endswith(" msks")
    ):
        return "cultural_house"
    if "divadlo" in text:
        return "theatre"
    return "unknown"


def classify_country(folder_name: str) -> str:
    text = normalize(folder_name)
    return "SK" if any(hint in text for hint in SK_HINTS) else "CZ"


def split_city_and_name(folder_name: str) -> tuple[str | None, str]:
    clean = folder_name.replace("!BLACKLIST!", "").strip(" ,-")
    if "," in clean:
        city, name = clean.split(",", 1)
        city = city.strip()
        if normalize(city).endswith(" sk"):
            city = city[:-3].strip()
        return city, name.strip()
    if " - " in clean:
        city, name = clean.split(" - ", 1)
        return city.strip(), name.strip()
    if clean.startswith("DK "):
        return clean[3:].strip(), clean
    return clean, clean


def file_kind(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in IMAGE_EXTENSIONS:
        return "photo"
    if ext in DOCUMENT_EXTENSIONS:
        return "document"
    return "other"


def iso_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    return conn


def upsert_venue(conn: sqlite3.Connection, folder: Path) -> int:
    city, name = split_city_and_name(folder.name)
    slug = slugify(folder.name)
    status = "blacklisted" if "blacklist" in normalize(folder.name) else "active"
    conn.execute(
        """
        INSERT INTO venues (slug, name, city, country, venue_type, status, source_folder, original_source_folder)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_folder) DO UPDATE SET
            slug = excluded.slug,
            name = excluded.name,
            city = excluded.city,
            country = excluded.country,
            venue_type = excluded.venue_type,
            status = excluded.status,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            slug,
            name,
            city,
            classify_country(folder.name),
            classify_type(folder.name),
            status,
            str(folder.relative_to(ROOT)),
            str(folder.relative_to(ROOT)),
        ),
    )
    venue_id = conn.execute(
        "SELECT id FROM venues WHERE source_folder = ?", (str(folder.relative_to(ROOT)),)
    ).fetchone()[0]
    conn.execute(
        """
        INSERT OR IGNORE INTO performance_spaces (venue_id, name, space_type)
        VALUES (?, 'Main space', ?)
        """,
        (venue_id, "outdoor_stage" if classify_type(folder.name) == "outdoor_theatre" else "main_hall"),
    )
    for task_type, priority in (
        ("extract_technical_data", 1),
        ("extract_contacts", 2),
        ("extract_access_notes", 2),
        ("verify_web_data", 3),
    ):
        conn.execute(
            """
            INSERT OR IGNORE INTO extraction_tasks (venue_id, task_type, priority)
            VALUES (?, ?, ?)
            """,
            (venue_id, task_type, priority),
        )
    return venue_id


def import_files(conn: sqlite3.Connection, venue_id: int, folder: Path) -> None:
    for path in sorted(folder.iterdir(), key=lambda item: item.name.lower()):
        if not path.is_file() or path.name == ".DS_Store":
            continue
        stat = path.stat()
        conn.execute(
            """
            INSERT INTO source_files (
                venue_id, path, filename, extension, file_kind, size_bytes, modified_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                venue_id = excluded.venue_id,
                filename = excluded.filename,
                extension = excluded.extension,
                file_kind = excluded.file_kind,
                size_bytes = excluded.size_bytes,
                modified_at = excluded.modified_at,
                imported_at = CURRENT_TIMESTAMP
            """,
            (
                venue_id,
                str(path.relative_to(ROOT)),
                path.name,
                path.suffix.lower().lstrip("."),
                file_kind(path),
                stat.st_size,
                iso_mtime(path),
            ),
        )


def main() -> None:
    INCOMING_DIR.mkdir(parents=True, exist_ok=True)
    conn = connect()
    with conn:
        for folder in sorted((p for p in INCOMING_DIR.iterdir() if p.is_dir()), key=lambda item: item.name.lower()):
            if folder.name.startswith("."):
                continue
            venue_id = upsert_venue(conn, folder)
            import_files(conn, venue_id, folder)

    venues = conn.execute("SELECT COUNT(*) FROM venues").fetchone()[0]
    files = conn.execute("SELECT COUNT(*) FROM source_files").fetchone()[0]
    print(f"Imported {venues} venues and {files} source files into {DB_PATH}")


if __name__ == "__main__":
    main()
