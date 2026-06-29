// test_backend_api.test.js — integration tests for the Express API
// against a temporary, throwaway SQLite database (never the real
// traffic.db). Uses supertest so no real port needs to be bound.
//
// Run from backend/ after `npm install`:
//   DATABASE_PATH=:memory: npx jest ../testing/software_tests/test_backend_api.test.js
//
// NOTE ON THIS REPO'S TEST STATUS: these were written and syntax-checked
// (`node --check`) in a sandboxed environment without registry access to
// `npm install` jest/supertest/better-sqlite3, so they have **not** been
// executed end-to-end in this revision. Run them yourself after
// `npm install` before relying on them — see testing/software_tests/README.md.

const path = require("path");
const fs = require("fs");
const os = require("os");

let app;
let request;
let tmpDbPath;

beforeAll(() => {
  // Point at a throwaway DB file *before* requiring any backend module,
  // since database/db.js opens its connection at require-time.
  tmpDbPath = path.join(os.tmpdir(), `traffic-test-${Date.now()}.db`);
  process.env.DATABASE_PATH = tmpDbPath;
  process.env.JWT_SECRET = "test-secret";

  // eslint-disable-next-line global-require
  request = require("supertest");
  // eslint-disable-next-line global-require
  const { createApp } = require(path.join(__dirname, "../../backend/api/app.js"));
  app = createApp({ publishOverride: jest.fn() });
});

afterAll(() => {
  if (tmpDbPath && fs.existsSync(tmpDbPath)) fs.unlinkSync(tmpDbPath);
});

describe("GET /api/health", () => {
  it("reports ok status with an uptime counter", async () => {
    const res = await request(app).get("/api/health");
    expect(res.status).toBe(200);
    expect(res.body.status).toBe("ok");
    expect(typeof res.body.uptime_s).toBe("number");
  });
});

describe("GET /api/events", () => {
  it("returns an empty list on a fresh database", async () => {
    const res = await request(app).get("/api/events?hours=24");
    expect(res.status).toBe(200);
    expect(res.body.count).toBe(0);
    expect(res.body.events).toEqual([]);
  });

  it("returns 404 for a non-existent event id", async () => {
    const res = await request(app).get("/api/events/999999");
    expect(res.status).toBe(404);
  });
});

describe("POST /api/override", () => {
  it("rejects requests with no auth token", async () => {
    const res = await request(app).post("/api/override").send({ action: "force_red" });
    expect(res.status).toBe(401);
  });

  it("rejects an invalid action even with a (fake) bearer token shape", async () => {
    const res = await request(app)
      .post("/api/override")
      .set("Authorization", "Bearer not-a-real-token")
      .send({ action: "do_something_unsafe" });
    // Auth check happens first, so an invalid token is still a 401 here —
    // this test documents that ordering rather than asserting 400.
    expect(res.status).toBe(401);
  });
});
