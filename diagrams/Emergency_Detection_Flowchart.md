```mermaid
flowchart TD
    A([Camera Capture<br/>continuous stream]) --> B[Frame Buffer<br/>rolling window, 5 frames]
    B --> C[Preprocess<br/>resize 224×224 · normalize · color-correct]
    C --> D[YOLOv8n Inference<br/>feature extraction → bbox → class]
    D --> E[Confidence Score]
    E --> F{Validation Gate}
    F -->|conf < 0.85| Z1[Discard frame<br/>continue stream]
    F -->|conf ≥ 0.85| G{Multi-frame<br/>confirmation<br/>≥3 of 5 frames}
    G -->|No| Z1
    G -->|Yes| H{Position check<br/>inside lane ROI}
    H -->|No| Z1
    H -->|Yes| I{Size check<br/>matches expected<br/>vehicle bbox range}
    I -->|No| Z1
    I -->|Yes| J[[Trigger Emergency]]
    J --> K[Set emergency flag<br/>MQTT publish: traffic/emergency]
    J --> L[Capture evidence<br/>save annotated frame + timestamp]
    J --> M[Send alert<br/>dashboard + log]
    K & L & M --> N([Return to detection loop])
    Z1 --> A

    classDef gate fill:#fef9ec,stroke:#d97706,color:#92400e;
    classDef action fill:#f0fdf4,stroke:#16a34a,color:#166534;
    classDef discard fill:#fef2f2,stroke:#dc2626,color:#991b1b;
    class F,G,H,I gate;
    class J,K,L,M action;
    class Z1 discard;
```

### What changed vs. the original report's Fig 2.5

The original flowchart (see `diagrams/originals/Emergency_Detection_Flow_v1_original.png`) had several
typos that suggested it was hand-traced rather than generated from the real pipeline (`FrameBubber`,
`Normlaize`, `Precpcesssing`). The logic itself was sound — multi-stage validation before triggering an
override is the right design — so this version keeps the same four-gate validation strategy
(confidence → multi-frame → position → size) but:

- Fixes the labelling/spelling throughout.
- Makes the **discard path explicit** — the original didn't show what happens when a check fails; here,
  a failed gate at any stage returns to the live stream instead of silently disappearing.
- Names the actual model (**YOLOv8n**, chosen for its balance of accuracy and edge-inference speed on
  the Raspberry Pi 4B) instead of an unspecified "ML Inference" block.
- Ties each output action to a concrete system effect (MQTT topic, evidence file, dashboard log) instead
  of generic boxes.
