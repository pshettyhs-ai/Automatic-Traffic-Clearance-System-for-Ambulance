```mermaid
flowchart TD
    S([System Boot]) --> CFG[Load configuration<br/>thresholds, network, GPIO map]
    CFG --> NET[Connect Wi-Fi + MQTT broker]
    NET --> INIT[Initialize OLEDs, relays, IR sensors]
    INIT --> PAR{{Fork into parallel tasks}}

    subgraph T1["Detection Task (Raspberry Pi 4B)"]
        direction TB
        D1[Capture frame] --> D2[Preprocess]
        D2 --> D3[YOLOv8 inference]
        D3 --> D4{Ambulance<br/>validated?}
        D4 -->|Yes| D5[Publish MQTT<br/>traffic/emergency]
        D4 -->|No| D1
        D5 --> D1
    end

    subgraph T2["Control Task (Raspberry Pi Pico WH)"]
        direction TB
        C1[Check emergency flag] --> C2{Emergency<br/>active?}
        C2 -->|Yes| C3[Override: ambulance lane → GREEN<br/>all others → RED]
        C3 --> C4[Update OLEDs: 'EMERGENCY']
        C4 --> C5[Hold ≥30s minimum]
        C5 --> C6[Resume normal cycle]
        C2 -->|No| C7[Run timer-based FSM]
        C7 --> C8[Update OLED countdowns]
        C8 --> C9[Poll IR sensors → extend green if occupied]
        C9 --> C1
        C6 --> C1
    end

    subgraph T3["Comms Task (Backend)"]
        direction TB
        N1[Subscribe MQTT] --> N2[Bridge to WebSocket]
        N2 --> N3[Persist event to DB]
        N3 --> N4[Serve REST + push dashboard]
        N4 --> N1
    end

    PAR --> T1
    PAR --> T2
    PAR --> T3

    T2 -.heartbeat / health.-> SHUT{Shutdown<br/>requested?}
    T1 -.health.-> SHUT
    T3 -.health.-> SHUT
    SHUT -->|No| PAR
    SHUT -->|Yes| END[All-red fail-safe state] --> X([End])
```

### What changed vs. the original report's Fig 2.4

The original "Autonomous System Operation Flow" diagram (see
`diagrams/originals/Main_System_Flow_v1_original.png`) mixed several swimlanes into a single column with
unlabeled arrows looping back into earlier boxes, making it hard to tell which steps ran in parallel and
which were sequential. This version keeps the same three concurrent responsibilities the original text
described (detection, control, communication) but represents them as explicit parallel lanes, names which
physical board executes each lane (Pi 4B vs. Pico WH vs. backend), and gives the shutdown path a defined
fail-safe end state (all signals red) rather than an ambiguous "Shutdown Sequence" box with no specified
output.
