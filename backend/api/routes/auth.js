// routes/auth.js — operator login. Issues a JWT consumed by
// middleware/auth.js's requireAuth on the override endpoint.
//
// There is intentionally no self-service signup endpoint — operator
// accounts are provisioned out-of-band (see database/seed.js) since this
// is a small-scale traffic-operations tool, not a multi-tenant SaaS.

const express = require("express");
const bcrypt = require("bcryptjs");
const { db } = require("../../database/db");
const { signToken } = require("../middleware/auth");

const router = express.Router();

const getUserByUsername = db.prepare("SELECT * FROM users WHERE username = ?");

router.post("/login", (req, res, next) => {
  const { username, password } = req.body || {};
  if (!username || !password) {
    const err = new Error("username and password are required");
    err.status = 400;
    err.expose = true;
    return next(err);
  }

  const user = getUserByUsername.get(username);
  if (!user || !bcrypt.compareSync(password, user.password_hash)) {
    const err = new Error("Invalid credentials");
    err.status = 401;
    err.expose = true;
    return next(err);
  }

  const token = signToken(user);
  res.json({ token, user: { id: user.id, username: user.username, role: user.role } });
});

module.exports = router;
