// db.js — thin data-access layer over better-sqlite3.
//
// Every query used elsewhere in the backend lives here, not scattered
// across route handlers, so the SQLite/Postgres swap discussed in
// diagrams/Database_Design.md only ever touches this one file.

const path = require("path");
const fs = require("fs");
const Database = require("better-sqlite3");

const DB_PATH = process.env.DATABASE_PATH || path.join(__dirname, "traffic.db");
const SCHEMA_PATH = path.join(__dirname, "schema.sql");

function init() {
  const db = new Database(DB_PATH);
  db.pragma("journal_mode = WAL");
  db.pragma("foreign_keys = ON");
  const schema = fs.readFileSync(SCHEMA_PATH, "utf8");
  db.exec(schema);
  return db;
}

const db = init();

// ---------------------------------------------------------------------------
// emergency_events
// ---------------------------------------------------------------------------
const insertEmergencyEvent = db.prepare(`
  INSERT INTO emergency_events (detected_at, lane, confidence, evidence_path)
  VALUES (@detected_at, @lane, @confidence, @evidence_path)
`);

const clearEmergencyEvent = db.prepare(`
  UPDATE emergency_events
  SET cleared = 1, cleared_at = @cleared_at, duration_ms = @duration_ms
  WHERE id = @id
`);

const getRecentEvents = db.prepare(`
  SELECT * FROM emergency_events
  WHERE detected_at >= @since
  ORDER BY detected_at DESC
  LIMIT @limit
`);

const getEventById = db.prepare(`SELECT * FROM emergency_events WHERE id = ?`);

// ---------------------------------------------------------------------------
// detection_log
// ---------------------------------------------------------------------------
const insertDetectionLog = db.prepare(`
  INSERT INTO detection_log (ts, confidence, passed_validation, failure_reason, frame_path, emergency_event_id)
  VALUES (@ts, @confidence, @passed_validation, @failure_reason, @frame_path, @emergency_event_id)
`);

// ---------------------------------------------------------------------------
// signal_cycles
// ---------------------------------------------------------------------------
const insertSignalCycle = db.prepare(`
  INSERT INTO signal_cycles (started_at, lane, phase, planned_duration_ms, actual_duration_ms, extended_by_ir)
  VALUES (@started_at, @lane, @phase, @planned_duration_ms, @actual_duration_ms, @extended_by_ir)
`);

const getCyclesSince = db.prepare(`
  SELECT * FROM signal_cycles WHERE started_at >= @since ORDER BY started_at ASC
`);

// ---------------------------------------------------------------------------
// system_health
// ---------------------------------------------------------------------------
const insertHealth = db.prepare(`
  INSERT INTO system_health (ts, node, uptime_s, cpu_pct, mem_pct, wifi_status, mqtt_status)
  VALUES (@ts, @node, @uptime_s, @cpu_pct, @mem_pct, @wifi_status, @mqtt_status)
`);

const getLatestHealthPerNode = db.prepare(`
  SELECT node, MAX(ts) as ts, uptime_s, wifi_status, mqtt_status
  FROM system_health
  GROUP BY node
`);

// ---------------------------------------------------------------------------
// audit_trail
// ---------------------------------------------------------------------------
const insertAudit = db.prepare(`
  INSERT INTO audit_trail (ts, user_id, action, details)
  VALUES (@ts, @user_id, @action, @details)
`);

module.exports = {
  db,
  emergencyEvents: {
    insert: (row) => insertEmergencyEvent.run(row),
    clear: (row) => clearEmergencyEvent.run(row),
    recentSince: (since, limit = 100) => getRecentEvents.all({ since, limit }),
    byId: (id) => getEventById.get(id),
  },
  detectionLog: {
    insert: (row) => insertDetectionLog.run(row),
  },
  signalCycles: {
    insert: (row) => insertSignalCycle.run(row),
    since: (since) => getCyclesSince.all({ since }),
  },
  systemHealth: {
    insert: (row) => insertHealth.run(row),
    latestPerNode: () => getLatestHealthPerNode.all(),
  },
  auditTrail: {
    insert: (row) => insertAudit.run(row),
  },
};
