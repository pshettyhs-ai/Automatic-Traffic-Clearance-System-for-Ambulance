// app.js — assembles the Express app: middleware, routes, error handling.
// Kept separate from server.js so it can be imported directly in tests
// (supertest) without binding a real port or connecting to MQTT.

const express = require("express");
const cors = require("cors");
const helmet = require("helmet");
const rateLimit = require("express-rate-limit");

const authRoutes = require("./routes/auth");
const eventsRoutes = require("./routes/events");
const lanesRoutes = require("./routes/lanes");
const overrideRoutes = require("./routes/override");
const healthRoutes = require("./routes/health");
const { notFoundHandler, errorHandler } = require("./middleware/errorHandler");

function createApp({ publishOverride } = {}) {
  const app = express();

  const corsOrigins = (process.env.CORS_ORIGINS || "*").split(",").map((s) => s.trim());

  app.use(helmet());
  app.use(cors({ origin: corsOrigins }));
  app.use(express.json({ limit: "256kb" }));

  // Generous limit on read endpoints, tighter on the state-changing one.
  app.use("/api/", rateLimit({ windowMs: 60_000, max: 120 }));
  app.use("/api/override", rateLimit({ windowMs: 60_000, max: 20 }));

  if (publishOverride) {
    app.set("publishOverride", publishOverride);
  }

  app.get("/", (req, res) => res.json({ name: "traffic-clearance-backend", status: "running" }));

  app.use("/api/auth", authRoutes);
  app.use("/api/events", eventsRoutes);
  app.use("/api/lanes", lanesRoutes);
  app.use("/api/override", overrideRoutes);
  app.use("/api/health", healthRoutes);

  app.use(notFoundHandler);
  app.use(errorHandler);

  return app;
}

module.exports = { createApp };
