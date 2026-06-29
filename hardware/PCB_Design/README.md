# hardware/PCB_Design/

## Honest status

**No PCB layout files (Gerbers, KiCad/Eagle projects) exist in this repository.** The prototype shown in
`images/Prototype_System_Setup.png` was built on perfboard/breadboard with jumper wires, validated
against the GPIO map in `hardware/Circuit_Schematics/`. Claiming a finished PCB design here without one
actually existing would misrepresent the project's hardware maturity — so instead, this document is the
specification a PCB layout would need to satisfy, ready to hand to a KiCad project.

## What a production PCB for this project would need to include

Based on the validated GPIO map and BOM:

1. **RP2040 carrier or Pico WH castellated-edge footprint** (using the Pico as a module rather than
   bringing up a bare RP2040 avoids re-certifying the radio section).
2. **12-channel relay driver section** (or replace relays with logic-level MOSFETs + flyback protection
   if switching DC LED arrays instead of mains-adjacent loads) for the 4×Red/Green/Yellow outputs.
3. **I2C header breakout** for the PCA9548A mux + 4× OLED, with 4.7kΩ pull-ups placed on-board.
4. **IR sensor header** (4×, digital in, with a shared 5V/GND rail).
5. **Buzzer driver header** for the ESP8266's GPIO5 line (or an on-board ESP8266 footprint, if
   integrating it directly rather than as a separate module).
6. **Power section**: 5V/12V input terminals, reverse-polarity protection diode, a 5V linear or buck
   regulator stage feeding the Pico's VSYS, and adequate trace width for the 12V/relay-switched current
   (see `hardware/BOM.xlsx` for current budgets per rail).
4. **Test points** on every GPIO net, since this is exactly the kind of board where a single
   mis-assigned pin (as in the original report's Fig 2.3 — see the root README's corrections section)
   is much cheaper to catch with a multimeter on a test point than after fabrication.

## Suggested next step

Open a new KiCad project (`traffic-clearance-controller.kicad_pro`), build the schematic from
`hardware/Circuit_Schematics/Pico_GPIO_Wiring.svg` net-by-net, and commit the resulting `.kicad_sch` /
`.kicad_pcb` / exported Gerbers here. Until then, treat this folder as the spec, not the deliverable.
