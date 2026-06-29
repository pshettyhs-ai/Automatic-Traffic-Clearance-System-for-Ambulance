# User Manual — Traffic Authority Operators

This is the non-developer-facing manual: what to do if you're the person watching the dashboard, not the
person maintaining the code. For setup/installation, see `docs/Deployment_Guide.md` instead.

## Logging in

1. Open the dashboard URL provided by your system administrator (e.g., `http://<server-ip>:8080`).
2. The live signal status, event timeline, and analytics are visible without logging in.
3. To use **Manual Override**, enter the operator username/password your administrator created for you
   (see `backend/database/seed.js` — your admin runs this once per operator account) in the "Manual
   Override" panel.

## Reading the dashboard

- **Connection card** — should read "connected." If it reads "disconnected," the dashboard has lost its
  link to the backend; the physical traffic lights are unaffected (they keep running locally on the
  Pico regardless of dashboard connectivity) but you won't see live updates until it reconnects.
- **Emergency Status card** — "ACTIVE" means an ambulance has been detected and a lane currently has
  priority; "Clear" means normal timed cycling.
- **Intersection Signal Status** — one panel per lane (North/East/South/West), each showing which light
  is lit and the current phase name.
- **Emergency Event Timeline** — every confirmed detection in the last 24 hours, with a confidence score.
- **Emergency Triggers by Hour** — a bar chart to spot patterns (e.g., consistently high-traffic hours).

## When to use Manual Override

- **Force all-red** — use during maintenance, a manual traffic-police-directed situation, or any time
  you need the intersection to default to the safest state regardless of the automatic cycle. The system
  will not auto-resume from this state; press it again only once it's safe and use the dashboard to
  confirm, or restart the Pico to resume the normal cycle.
- **Clear active emergency** — use if the system reports "ACTIVE" but you can visually confirm via the
  camera feed or in person that no emergency vehicle is actually present (a false positive). This ends
  the priority state and returns the intersection to normal cycling immediately, without waiting out the
  minimum hold timer.

Every override you send is logged with your username and a timestamp — this isn't meant as a deterrent,
it's so that if a citizen or a colleague asks "why did the signal do that at 3pm," there's a clear,
honest answer.

## What to do if something looks wrong

- **All lanes stuck on red, no countdown moving:** this is the system's deliberate fail-safe behavior on
  a fault (lost power to the Pico, a crashed control loop, etc.) — it is not a separate "broken" state
  you need to fix manually; it's the safe state the system defaults to. Contact your technical
  administrator.
- **Dashboard shows "ACTIVE" for an unusually long time:** check the Emergency Event Timeline for the
  triggering event's confidence score and evidence — if it looks like a false positive, use "Clear active
  emergency." If it looks genuine but is taking unusually long, this may indicate the ambulance is
  genuinely still in the detection zone, or that the detection pipeline needs a technician's attention.
- **Buzzer not sounding on an emergency:** the buzzer is a separate, independent device (ESP8266) from
  the signal lights — a quiet buzzer does not mean the signal override failed. Report it separately to
  your technical administrator.

## Who to contact

Your organization's deployment-specific contact information goes here — this manual ships generic
because the repository doesn't know your operations team's structure. Fill this section in for your own
deployment before handing the dashboard to operators.
