-- Local Event Finder: SQLite schema (matches the Software Design Document class diagram)
-- Dates are stored as 'YYYY-MM-DD' and times as 'HH:MM', all in US Eastern Time (Q04).

CREATE TABLE IF NOT EXISTS users (
    user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL CHECK (length(trim(name)) > 0),
    email         TEXT NOT NULL UNIQUE COLLATE NOCASE,   -- store trimmed + lowercased
    password_hash TEXT NOT NULL                          -- salted hash only, never plaintext
);

CREATE TABLE IF NOT EXISTS categories (
    category_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name  TEXT NOT NULL UNIQUE,
    category_image TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    event_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT NOT NULL CHECK (length(trim(title)) > 0),
    description  TEXT NOT NULL,
    date         TEXT NOT NULL,                          -- YYYY-MM-DD
    start_time   TEXT NOT NULL,                          -- HH:MM (24h)
    end_time     TEXT NOT NULL,                          -- HH:MM (24h)
    location     TEXT NOT NULL,
    capacity     INTEGER NOT NULL CHECK (capacity > 0),
    event_status TEXT NOT NULL DEFAULT 'active',         -- 'cancelled' only if FR-10.2 is built
    category_id  INTEGER NOT NULL REFERENCES categories(category_id),
    creator_id   INTEGER NOT NULL REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS rsvps (
    rsvp_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(user_id),
    event_id   INTEGER NOT NULL REFERENCES events(event_id),
    rsvp_date  TEXT NOT NULL DEFAULT (datetime('now')),
    status     TEXT NOT NULL DEFAULT 'active',
    UNIQUE (user_id, event_id)                           -- at most one RSVP per user per event
);

CREATE TABLE IF NOT EXISTS favorites (
    favorite_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(user_id),
    event_id    INTEGER NOT NULL REFERENCES events(event_id),
    UNIQUE (user_id, event_id)                           -- no duplicate favorites
);

CREATE INDEX IF NOT EXISTS idx_events_date     ON events(date, start_time);
CREATE INDEX IF NOT EXISTS idx_events_category ON events(category_id);
CREATE INDEX IF NOT EXISTS idx_rsvps_event     ON rsvps(event_id);
