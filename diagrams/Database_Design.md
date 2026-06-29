```mermaid
erDiagram
    EMERGENCY_EVENTS {
        integer id PK
        datetime detected_at
        integer lane
        real confidence
        string evidence_path
        integer cleared
        datetime cleared_at
        integer duration_ms
    }

    SIGNAL_CYCLES {
        integer id PK
        datetime started_at
        integer lane
        string phase
        integer planned_duration_ms
        integer actual_duration_ms
        integer extended_by_ir
    }

    SYSTEM_HEALTH {
        integer id PK
        datetime ts
        string node
        integer uptime_s
        real cpu_pct
        real mem_pct
        string wifi_status
        string mqtt_status
    }

    DETECTION_LOG {
        integer id PK
        datetime ts
        real confidence
        integer passed_validation
        string failure_reason
        string frame_path
        integer emergency_event_id FK
    }

    USERS {
        integer id PK
        string username
        string password_hash
        string role
        datetime created_at
    }

    AUDIT_TRAIL {
        integer id PK
        datetime ts
        integer user_id FK
        string action
        string details
    }

    EMERGENCY_EVENTS ||--o{ DETECTION_LOG : "validated by"
    USERS ||--o{ AUDIT_TRAIL : "performs"
```

### Notes

- **SQLite** is used for the single-intersection pilot deployment described in this repository (zero
  config, file-based, trivially backed up). The schema is written in plain SQL
  (`backend/database/schema.sql`) with no SQLite-specific syntax, so migrating to **PostgreSQL** for a
  multi-intersection, city-scale deployment is a connection-string change, not a redesign.
- `DETECTION_LOG` intentionally records **every** inference pass, not just the ones that triggered an
  emergency — this is what makes it possible to compute false-positive/false-negative rates after the
  fact instead of only ever seeing confirmed detections.
- `AUDIT_TRAIL` exists because the original report flagged manual override as a feature but didn't
  specify any accountability trail for who issued it — added here to close that gap.
