# Dashboard — Operator Web Interface

React 18 + Vite + Redux Toolkit + Tailwind dashboard for live monitoring and manual override. Connects
to the backend over both REST (history, login, override) and WebSocket (live signal/emergency updates) —
see `diagrams/Communication_Architecture.md`.

## Quick start

```bash
npm install
cp .env.example .env   # set VITE_API_BASE_URL if the backend isn't on localhost:4000
npm run dev             # http://localhost:5173
```

## Structure

```
src/
├── App.jsx                       top-level layout, owns the socket lifecycle
├── store.js / store/trafficSlice.js   Redux Toolkit state: lanes, events, health, socket status
├── services/
│   ├── api.js                     REST calls (events, lanes, auth, override)
│   └── socket.js                  Socket.IO client, dispatches straight into Redux
└── components/
    ├── StatusCards.jsx             connection / emergency status / clock
    ├── LaneSignalBoard.jsx         4-lane live signal head visualization
    ├── EmergencyTimeline.jsx       merges live + historical emergency events
    ├── AnalyticsCharts.jsx          Chart.js bar chart, triggers per hour
    └── ManualOverridePanel.jsx     operator login + force_red / clear_emergency
```

## What's real vs. illustrative here

- The Redux store shape and Socket.IO event names match exactly what `backend/mqtt/mqttBridge.js`
  actually emits (`emergencyEvent`, `laneStatus`, `emergencyCleared`, `systemHealth`) — this isn't a
  mockup with invented data shapes.
- `LaneSignalBoard` renders whatever phase the backend last reported; with no backend running it will
  correctly show all four lanes as `UNKNOWN` rather than faking a green light.
- All JS/JSX in this folder was syntax-validated with `esbuild` in the environment this repo was
  generated in (no JS package registry access there to run a real `npm install` + build) — run
  `npm install && npm run build` yourself before deploying; see the root README's "Honest Status"
  section.

## Building for production

```bash
npm run build      # outputs to dist/
npm run preview    # serve the production build locally
```

Or via the provided multi-stage `Dockerfile` (built automatically by the root `docker-compose.yml`).
