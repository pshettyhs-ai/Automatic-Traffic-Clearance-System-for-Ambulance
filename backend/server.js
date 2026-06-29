// server.js — entry point. Wires together the HTTP server, Socket.IO,
// the MQTT bridge, and the Express app (see diagrams/System_Architecture.svg
// for how these three pieces relate).

require("dotenv").config();

const http = require("http");
const { Server: SocketIOServer } = require("socket.io");

const { createApp } = require("./api/app");
const { attachMqttBridge } = require("./mqtt/mqttBridge");

const PORT = process.env.PORT || 4000;
const corsOrigins = (process.env.CORS_ORIGINS || "*").split(",").map((s) => s.trim());

function main() {
  // Socket.IO needs an http server up front (it upgrades HTTP connections to
  // WebSocket), so we create that before the Express app's routes need to
  // reference the MQTT bridge's publish function.
  const httpServer = http.createServer();
  const io = new SocketIOServer(httpServer, { cors: { origin: corsOrigins } });

  const { publishOverride } = attachMqttBridge(io, {
    brokerUrl: process.env.MQTT_BROKER_URL,
    username: process.env.MQTT_USERNAME,
    password: process.env.MQTT_PASSWORD,
  });

  const app = createApp({ publishOverride });
  httpServer.on("request", app);

  io.on("connection", (socket) => {
    console.log("[socket.io] dashboard client connected:", socket.id);
    socket.on("disconnect", () => console.log("[socket.io] client disconnected:", socket.id));
  });

  httpServer.listen(PORT, () => {
    console.log(`Traffic Clearance backend listening on :${PORT}`);
  });

  // Fail-safe: don't let an unhandled rejection silently kill Node without
  // at least logging what happened — operationally, this backend going
  // down should be loud, not silent.
  process.on("unhandledRejection", (reason) => {
    console.error("[unhandledRejection]", reason);
  });
}

main();
