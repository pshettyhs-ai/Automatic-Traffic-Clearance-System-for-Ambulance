```mermaid
stateDiagram-v2
    [*] --> INIT
    INIT --> NORTH_GREEN

    NORTH_GREEN --> NORTH_YELLOW: timer expired (15s base, +10s if IR occupied)
    NORTH_YELLOW --> EAST_GREEN: 3s
    EAST_GREEN --> EAST_YELLOW: timer expired
    EAST_YELLOW --> SOUTH_GREEN: 3s
    SOUTH_GREEN --> SOUTH_YELLOW: timer expired
    SOUTH_YELLOW --> WEST_GREEN: 3s
    WEST_GREEN --> WEST_YELLOW: timer expired
    WEST_YELLOW --> NORTH_GREEN: 3s

    NORTH_GREEN --> EMERGENCY_MODE: emergency flag set
    NORTH_YELLOW --> EMERGENCY_MODE: emergency flag set
    EAST_GREEN --> EMERGENCY_MODE: emergency flag set
    EAST_YELLOW --> EMERGENCY_MODE: emergency flag set
    SOUTH_GREEN --> EMERGENCY_MODE: emergency flag set
    SOUTH_YELLOW --> EMERGENCY_MODE: emergency flag set
    WEST_GREEN --> EMERGENCY_MODE: emergency flag set
    WEST_YELLOW --> EMERGENCY_MODE: emergency flag set

    state EMERGENCY_MODE {
        [*] --> ALL_RED_TRANSITION
        ALL_RED_TRANSITION --> AMBULANCE_LANE_GREEN: 1s all-red clearance
        AMBULANCE_LANE_GREEN --> HOLD_MIN_30S: display "EMERGENCY"
        HOLD_MIN_30S --> CHECK_CLEAR: 30s minimum elapsed
        CHECK_CLEAR --> AMBULANCE_LANE_GREEN: still detected (extend)
        CHECK_CLEAR --> [*]: cleared
    }

    EMERGENCY_MODE --> NORTH_GREEN: resume normal cycle\n(always resumes at NORTH, never mid-cycle)

    note right of EMERGENCY_MODE
        A 1s all-red clearance phase is
        inserted before granting green to the
        ambulance lane — the original diagram
        switched directly from one GREEN lane
        to another GREEN lane with no
        intersection-clearing interval, which is
        an unsafe transition.
    end note
```

### What changed vs. the original report's Fig 2.6

The original state machine (see `diagrams/originals/Traffic_State_Machine_v1_original.png`) had two
issues worth calling out explicitly, since both are realistic
mistakes that a reviewer or interviewer is likely to probe:

1. **No all-red clearance interval before EMERGENCY_MODE.** The original diagram transitioned straight
   from whichever lane was GREEN into the ambulance lane's GREEN. Two perpendicular lanes both showing
   green for even a moment is a safety hazard. This revision inserts a brief mandatory all-red phase
   before granting the ambulance lane green, matching standard traffic-engineering practice for
   priority/pre-emption systems.
2. **Unreachable yellow states.** The original diagram's yellow boxes existed for North/East but the
   transitions for South/West collapsed straight from GREEN to the next lane's GREEN. This version gives
   every lane a symmetric GREEN → YELLOW → next-lane-GREEN path.

The 30-second minimum hold and "resume always at NORTH_GREEN" behavior from the original are kept, since
they reflect a deliberate (and reasonable) design choice for predictability after an override.
