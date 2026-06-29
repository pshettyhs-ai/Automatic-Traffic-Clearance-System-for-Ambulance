-- schema.sql — plain ANSI-ish SQL, intentionally avoiding SQLite-only syntax
-- where possible so migrating to PostgreSQL is a connection-string change,
-- not a rewrite (see diagrams/Database_Design.md).

CREATE TABLE IF NOT EXISTS emergency_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    detected_at     REAL    NOT NULL,
    lane            INTEGER NOT NULL,
    confidence      REAL    NOT NULL,
    evidence_path   TEXT,
    cleared         INTEGER NOT NULL DEFAULT 0,
    cleared_at      REAL,
    duration_ms     INTEGER
);

CREATE TABLE IF NOT EXISTS signal_cycles (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at           REAL    NOT NULL,
    lane                 INTEGER NOT NULL,
    phase                TEXT    NOT NULL,
    planned_duration_ms  INTEGER,
    actual_duration_ms   INTEGER,
    extended_by_ir       INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS system_health (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ts            REAL    NOT NULL,
    node          TEXT    NOT NULL,
    uptime_s      INTEGER,
    cpu_pct       REAL,
    mem_pct       REAL,
    wifi_status   TEXT,
    mqtt_status   TEXT
);

CREATE TABLE IF NOT EXISTS detection_log (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    ts                    REAL    NOT NULL,
    confidence            REAL    NOT NULL,
    passed_validation     INTEGER NOT NULL DEFAULT 0,
    failure_reason        TEXT,
    frame_path            TEXT,
    emergency_event_id    INTEGER,
    FOREIGN KEY (emergency_event_id) REFERENCES emergency_events(id)
);

CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT    NOT NULL UNIQUE,
    password_hash   TEXT    NOT NULL,
    role            TEXT    NOT NULL DEFAULT 'operator',
    created_at      REAL    NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_trail (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          REAL    NOT NULL,
    user_id     INTEGER,
    action      TEXT    NOT NULL,
    details     TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_emergency_events_detected_at ON emergency_events(detected_at);
CREATE INDEX IF NOT EXISTS idx_detection_log_ts ON detection_log(ts);
CREATE INDEX IF NOT EXISTS idx_signal_cycles_started_at ON signal_cycles(started_at);
CREATE INDEX IF NOT EXISTS idx_system_health_ts ON system_health(ts);
