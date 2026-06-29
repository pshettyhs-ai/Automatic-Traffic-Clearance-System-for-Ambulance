// routes/events.js — emergency event history, the main thing the
// dashboard's "Analytics" / "Emergency Timeline" panels read from.

const express = require("express");
const db = require("../../database/db");

const router = express.Router();

// GET /api/events?hours=24&limit=100
router.get("/", (req, res) => {
  const hours = Number(req.query.hours) || 24;
  const limit = Math.min(Number(req.query.limit) || 100, 1000);
  const since = Date.now() / 1000 - hours * 3600;

  const events = db.emergencyEvents.recentSince(since, limit);
  res.json({ count: events.length, since, events });
});

// GET /api/events/:id
router.get("/:id", (req, res, next) => {
  const event = db.emergencyEvents.byId(Number(req.params.id));
  if (!event) {
    const err = new Error("Event not found");
    err.status = 404;
    err.expose = true;
    return next(err);
  }
  res.json(event);
});

module.exports = router;
