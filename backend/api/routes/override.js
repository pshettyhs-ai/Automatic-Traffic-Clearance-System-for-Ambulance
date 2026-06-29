// routes/override.js — manual control endpoints for traffic operators.
// Requires auth (see middleware/auth.js) and writes to audit_trail,
// since the original report specified manual override as a feature but
// never specified any accountability trail for who issued one.

const express = require("express");
const db = require("../../database/db");
const { requireAuth } = require("../middleware/auth");

const router = express.Router();

const ALLOWED_ACTIONS = new Set(["force_red", "clear_emergency"]);

// POST /api/override   { "action": "force_red" | "clear_emergency", "lane": 2 }
router.post("/", requireAuth, (req, res, next) => {
  const { action, lane } = req.body || {};

  if (!ALLOWED_ACTIONS.has(action)) {
    const err = new Error(`action must be one of: ${[...ALLOWED_ACTIONS].join(", ")}`);
    err.status = 400;
    err.expose = true;
    return next(err);
  }

  const publishOverride = req.app.get("publishOverride");
  if (!publishOverride) {
    const err = new Error("MQTT bridge is not connected; override cannot be delivered");
    err.status = 503;
    err.expose = true;
    return next(err);
  }

  publishOverride(action, lane ? { lane } : {});

  db.auditTrail.insert({
    ts: Date.now() / 1000,
    user_id: req.user.id,
    action: `override:${action}`,
    details: JSON.stringify({ lane }),
  });

  res.json({ status: "sent", action, lane: lane || null });
});

module.exports = router;
