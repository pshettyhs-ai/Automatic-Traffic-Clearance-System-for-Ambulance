# Deployment Guide

## Local development (everything on one machine)

```bash
git clone <this-repo>
cd Traffic-Clearance-System-For-Emergency-Vehicles
cp backend/.env.example backend/.env
cp dashboard/.env.example dashboard/.env
docker compose up --build
```

This brings up Mosquitto, the backend, and the dashboard. Then, separately (these run on real
hardware, not in Docker):

```bash
# Pico WH — see firmware/pico_firmware/README.md for flashing instructions
# ESP8266 — see firmware/esp8266_firmware/README.md
# Pi 4B detection script:
cd ai_model/inference
pip install -r ../requirements.txt
python detect.py --mqtt-host <your-server-ip> --lane 1 --weights ../model_weights/ambulance_yolov8n.pt
```

Create your first operator login:
```bash
docker compose exec backend node database/seed.js admin "a-strong-password"
```

## Single-intersection pilot deployment

Same as local development, but:

1. Run `docker-compose.yml`'s services on a small always-on machine (a mini-PC or a cloud VM works —
   doesn't need to be physically at the intersection, just network-reachable from it).
2. Point the Pi 4B and Pico WH's MQTT broker address (`config.py` / `detect.py --mqtt-host`) at that
   machine's address instead of `localhost`.
3. Before exposing the broker beyond your own LAN/VPN:
   - Disable anonymous MQTT access (`simulations/mosquitto.conf` -> `allow_anonymous false`) and create
     credentials with `mosquitto_passwd`.
   - Enable TLS on the broker (port 8883) and update `MQTT_BROKER_URL` / firmware configs to `mqtts://`.
   - Set a long, random `JWT_SECRET` in `backend/.env` (not the placeholder from `.env.example`).
   - Put the dashboard behind HTTPS (a reverse proxy like Caddy or Traefik in front of the `dashboard`
     container is the easiest path) and update `CORS_ORIGINS` accordingly.
4. Back up the `backend-data` volume (contains `traffic.db`) on whatever schedule matches your data
   retention needs.

## Multi-intersection / city-scale deployment

This repository's architecture is designed so this is mostly a matter of repeating the edge-hardware
deployment, not redesigning the server side:

1. **Swap SQLite for PostgreSQL.** Change `backend/database/db.js` to use `pg` instead of
   `better-sqlite3` (the schema in `schema.sql` is plain SQL and should need minimal changes), and point
   the connection config at a Postgres connection string.
2. **Swap Mosquitto for a managed broker** (AWS IoT Core, HiveMQ Cloud, etc.) if you need built-in
   per-device certificate management at scale — the application code only depends on standard MQTT
   pub/sub, not anything Mosquitto-specific.
3. **Tag every MQTT topic and DB row with an intersection id.** This repository's schema and topics
   (`traffic/emergency`, etc.) are written for a single intersection; add an `intersection_id` field
   throughout before connecting a second one, so events from different junctions don't collide.
4. **Consider a per-intersection edge gateway** if connectivity to each site is unreliable, so detection
   events can be queued locally and forwarded once the link is back — not implemented in this revision.

## Updating firmware in the field

- **Pico WH:** no over-the-air update mechanism is implemented — re-flashing requires physical USB
  access in this revision. If frequent field updates are a requirement, this is the first thing to add
  (MicroPython supports OTA patterns, but none is wired up here).
- **ESP8266:** same — physical/serial reflash only.
- **Pi 4B:** standard `git pull` + restart of the `detect.py` process (e.g., via systemd) works fine
  since it's a full Linux machine; consider a systemd unit file with `Restart=on-failure` for resilience.

## Rollback

Both `backend` and `dashboard` are stateless containers (state lives in the `backend-data` volume) — a
bad deploy can be rolled back by redeploying the previous image tag. `docker-compose.yml` as written
doesn't pin image tags or version the build; add proper image tagging and a registry push before
treating this as a real CI/CD pipeline rather than a `docker compose up --build` convenience script.
