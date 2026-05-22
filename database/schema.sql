PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS venues (
    id INTEGER PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    city TEXT,
    country TEXT,
    venue_type TEXT NOT NULL DEFAULT 'unknown',
    status TEXT NOT NULL DEFAULT 'active',
    source_folder TEXT NOT NULL UNIQUE,
    original_source_folder TEXT,
    web_url TEXT,
    latitude REAL,
    longitude REAL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS performance_spaces (
    id INTEGER PRIMARY KEY,
    venue_id INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    name TEXT NOT NULL DEFAULT 'Main space',
    space_type TEXT NOT NULL DEFAULT 'unknown',
    capacity INTEGER,
    stage_width_m REAL,
    stage_depth_m REAL,
    stage_height_m REAL,
    portal_width_m REAL,
    portal_height_m REAL,
    fly_system TEXT,
    orchestra_pit TEXT,
    floor_type TEXT,
    notes TEXT,
    UNIQUE (venue_id, name)
);

CREATE TABLE IF NOT EXISTS technical_systems (
    id INTEGER PRIMARY KEY,
    venue_id INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    space_id INTEGER REFERENCES performance_spaces(id) ON DELETE SET NULL,
    system_type TEXT NOT NULL,
    summary TEXT,
    source_file_id INTEGER REFERENCES source_files(id) ON DELETE SET NULL,
    confidence TEXT NOT NULL DEFAULT 'manual'
);

CREATE TABLE IF NOT EXISTS equipment_items (
    id INTEGER PRIMARY KEY,
    venue_id INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    space_id INTEGER REFERENCES performance_spaces(id) ON DELETE SET NULL,
    category TEXT NOT NULL,
    manufacturer TEXT,
    model TEXT,
    quantity INTEGER,
    location TEXT,
    purpose TEXT,
    condition_note TEXT,
    source_file_id INTEGER REFERENCES source_files(id) ON DELETE SET NULL,
    confidence TEXT NOT NULL DEFAULT 'manual'
);

CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY,
    venue_id INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    name TEXT,
    role TEXT,
    organization TEXT,
    phone TEXT,
    email TEXT,
    web TEXT,
    note TEXT,
    source TEXT,
    source_file_id INTEGER REFERENCES source_files(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS access_notes (
    id INTEGER PRIMARY KEY,
    venue_id INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    loading_note TEXT,
    parking_note TEXT,
    arrival_note TEXT,
    restrictions TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_notes (
    id INTEGER PRIMARY KEY,
    venue_id INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    space_id INTEGER REFERENCES performance_spaces(id) ON DELETE SET NULL,
    note_type TEXT NOT NULL DEFAULT 'general',
    note TEXT NOT NULL,
    author TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS source_files (
    id INTEGER PRIMARY KEY,
    venue_id INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    path TEXT NOT NULL UNIQUE,
    filename TEXT NOT NULL,
    extension TEXT NOT NULL,
    file_kind TEXT NOT NULL,
    size_bytes INTEGER,
    modified_at TEXT,
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS web_sources (
    id INTEGER PRIMARY KEY,
    venue_id INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    title TEXT,
    source_type TEXT NOT NULL DEFAULT 'official',
    checked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    note TEXT,
    UNIQUE (venue_id, url)
);

CREATE TABLE IF NOT EXISTS extraction_tasks (
    id INTEGER PRIMARY KEY,
    venue_id INTEGER NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    task_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'todo',
    priority INTEGER NOT NULL DEFAULT 3,
    note TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (venue_id, task_type)
);

CREATE INDEX IF NOT EXISTS idx_venues_city ON venues(city);
CREATE INDEX IF NOT EXISTS idx_venues_type ON venues(venue_type);
CREATE INDEX IF NOT EXISTS idx_source_files_venue ON source_files(venue_id);
CREATE INDEX IF NOT EXISTS idx_equipment_venue_category ON equipment_items(venue_id, category);
CREATE INDEX IF NOT EXISTS idx_notes_venue ON user_notes(venue_id);

CREATE VIEW IF NOT EXISTS venue_overview AS
SELECT
    v.id,
    v.city,
    v.name,
    v.country,
    v.venue_type,
    v.status,
    v.source_folder,
    v.original_source_folder,
    COUNT(sf.id) AS source_file_count,
    SUM(CASE WHEN sf.file_kind = 'document' THEN 1 ELSE 0 END) AS document_count,
    SUM(CASE WHEN sf.file_kind = 'photo' THEN 1 ELSE 0 END) AS photo_count
FROM venues v
LEFT JOIN source_files sf ON sf.venue_id = v.id
GROUP BY v.id;

CREATE VIEW IF NOT EXISTS venues_needing_identification AS
SELECT
    id,
    city,
    name,
    country,
    source_folder,
    source_file_count,
    document_count,
    photo_count
FROM venue_overview
WHERE venue_type = 'unknown'
ORDER BY city, name;
