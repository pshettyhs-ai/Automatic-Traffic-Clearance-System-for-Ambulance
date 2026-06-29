```mermaid
flowchart LR
    subgraph Intersection["Intersection Site"]
        Pi4["Raspberry Pi 4B\n(Detection)"]
        Pico["Pico WH\n(Control)"]
        ESP["ESP8266\n(Alert)"]
    end

    subgraph Server["Server (on-prem mini-PC or cloud VM)"]
        direction TB
        subgraph Compose["docker-compose.yml"]
            Mosq["mosquitto:2\nMQTT Broker"]
            API["traffic-backend\nNode.js + Express + Socket.IO"]
            PG["postgres:16\n(or bind-mounted SQLite file)"]
            NGINX["nginx\nstatic React build + reverse proxy"]
        end
    end

    Ops["Traffic Authority\n(browser)"]

    Pi4 -- "MQTT (TLS, port 8883)" --> Mosq
    Pico -- "MQTT (TLS, port 8883)" --> Mosq
    ESP -- "MQTT (TLS, port 8883)" --> Mosq
    Mosq --> API
    API --> PG
    API --> NGINX
    NGINX -- "HTTPS" --> Ops

    style Intersection fill:#eff6ff,stroke:#1d4ed8
    style Server fill:#f0fdf4,stroke:#16a34a
    style Compose fill:#ffffff,stroke:#94a3b8,stroke-dasharray: 4 3
```

### Deployment notes

- A single `docker-compose.yml` (see `/docker-compose.yml`) brings up the broker, backend, database, and
  dashboard together for local development or a single-server pilot.
- Each intersection only needs outbound MQTT (TLS, port 8883) to the server — no inbound ports are
  opened on the edge hardware, reducing attack surface versus exposing a REST endpoint on each Pi.
- For a city-scale rollout, `Mosquitto` can be swapped for a managed broker (AWS IoT Core, HiveMQ Cloud)
  and Postgres for a managed instance (RDS/Cloud SQL) without changing the backend code — only
  connection configuration changes.
- See `docs/Deployment_Guide.md` for step-by-step setup, environment variables, and TLS certificate
  provisioning.
