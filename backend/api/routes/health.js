// routes/health.js — backend liveness + a quick rollup used by ops/monitoring.

const express = require("express");
const db = require("../../database/db");

const router = express.Router();

router.get("/", (req, res) => {
  res.json({
    status: "ok",
    uptime_s: Math.floor(process.uptime()),
    nodes: db.systemHealth.latestPerNode(),
    timestamp: Date.now() / 1000,
  });
});

module.exports = router;
