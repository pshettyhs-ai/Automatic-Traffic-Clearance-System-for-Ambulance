// auth.js — minimal JWT auth middleware for the operator-facing endpoints
// (manual override, audit-sensitive routes). Read-only status/history
// endpoints are left open to keep the dashboard's "live view" usable
// without requiring a login — only state-changing actions require a
// token. Tighten this (e.g. require auth for GET too) if you deploy
// somewhere the live feed itself is sensitive.

const jwt = require("jsonwebtoken");

function requireAuth(req, res, next) {
  const header = req.headers.authorization || "";
  const token = header.startsWith("Bearer ") ? header.slice(7) : null;

  if (!token) {
    return res.status(401).json({ error: "Missing bearer token" });
  }

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = decoded;
    next();
  } catch (err) {
    return res.status(401).json({ error: "Invalid or expired token" });
  }
}

function signToken(user) {
  return jwt.sign(
    { id: user.id, username: user.username, role: user.role },
    process.env.JWT_SECRET,
    { expiresIn: process.env.JWT_EXPIRES_IN || "12h" }
  );
}

module.exports = { requireAuth, signToken };
