# diagrams/

| File | Type | What it shows |
|---|---|---|
| `System_Architecture.svg` | Hand-built SVG | 3-tier overview: edge / communication / cloud |
| `Block_Diagram.svg` | Hand-built SVG | Corrected version of the original report's Fig 2.1 |
| `Circuit_Diagram.svg` | Hand-built SVG | Validated Pico WH GPIO wiring (every pin used exactly once) |
| `Main_System_Flow.md` + `.png` | Mermaid | Three concurrent tasks (detection / control / comms) and which board runs each |
| `Emergency_Detection_Flowchart.md` + `.png` | Mermaid | The four-gate detection validation pipeline |
| `Traffic_State_Machine.md` + `.png` | Mermaid | Signal FSM, including the added all-red clearance safety gap |
| `Communication_Architecture.md` + `.png` | Mermaid | Full sequence diagram across MQTT / REST / WebSocket |
| `Database_Design.md` + `.png` | Mermaid | ER diagram for the event-logging schema |
| `Deployment_Architecture.md` + `.png` | Mermaid | Docker Compose topology |
| `originals/` | — | The original report's diagrams, kept for direct before/after comparison |

Each `.md` file's Mermaid source renders natively when viewed on GitHub — the matching `.png` is
provided alongside for anyone viewing this repository outside GitHub (a downloaded zip, a plain
markdown viewer, etc.) where Mermaid won't auto-render. Both were generated from the same source, so
they never drift out of sync — if you edit a diagram, edit the `.md` file and re-render the `.png` with
[mermaid-cli](https://github.com/mermaid-js/mermaid-cli):

```bash
mmdc -i diagrams/Traffic_State_Machine.md -o diagrams/Traffic_State_Machine.png -b white
# Note: when given a .md file, mmdc extracts the mermaid block and writes the
# result as Traffic_State_Machine-1.png (it appends an index before renaming
# is needed) — rename it back to the matching .png filename afterward.
```

(`mmdc` can read a fenced ```` ```mermaid ```` block straight out of a `.md` file — confirmed by
generating every `.png` in this folder that way — though it appends a `-1` to the output filename, which
needs a quick rename to match the convention used here.)

See the root README's [Architecture Corrections](../README.md#architecture-corrections) section for a
summary table of every fix reflected in these diagrams, and each individual `.md` file for the specific
reasoning behind that diagram's corrections.
