// routes/lanes.js — signal cycle history + latest known per-lane phase,
// used by the dashboard's live signal-status panel and analytics charts.

const express = require("express");
const db = require("../../database/db");

const router = express.Router();

// GET /api/lanes/cycles?hours=6
router.get("/cycles", (req, res) => {
  const hours = Number(req.query.hours) || 6;
  const since = Date.now() / 1000 - hours * 3600;
  const cycles = db.signalCycles.since(since);
  res.json({ count: cycles.length, since, cycles });
});

// GET /api/lanes/health — latest heartbeat per physical node (Pi4 / Pico / ESP8266)
router.get("/health", (req, res) => {
  res.json(db.systemHealth.latestPerNode());
});

module.exports = router;
