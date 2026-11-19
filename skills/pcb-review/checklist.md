# Review checklist (what found real problems before)

## Power / high current
- Path, segment by segment (connector → switch → bulk → load switch → load connector → return): width per layer, which layer, vias per layer change.
- IPC-2221 rough numbers (*verify*): a 0.5 mm outer 1 oz trace carries about 2 A at a 20 °C rise. 3.5–4 A needs about 1.1–1.3 mm outer (1.7 mm at 10 °C). On a 0.5 oz inner layer it needs several mm, so no high current on inner layers.
  Formula: I = k·ΔT^0.44·A^0.725, with A in mil², k = 0.048 for outer layers and 0.024 for inner.
- Vias: a 0.3 mm drill via carries about 0.7–1 A comfortably, so use ≥ 6–8 per transition for about 4 A. A single 0.2 mm via on a 4 A path is a P1.
- Parts stacked F/B (FET tab over a connector pad): put a via array straight through.
- Test points or sense resistors that drag a power net across the board (a long thin trace only to reach a TP). Move the TP.
- Heat: FET loss divided by copper area on its tab net. A switching-node tab needs compact copper surrounded by GND, not a huge pour.
- Via-in-pad on parts the assembler places: order filled/capped vias or move them outside the pad.
- Bulk caps "at the FET": measure the real distance.

## Switching regulator
- Inductor at the SW pin (≤ 1–2 mm), SW on the outer layer only, no vias, never on an inner layer next to analog.
- Cin (100 nF + bulk) across VIN/GND at the pins; Cout at the inductor, returning to the same GND island.
- FB divider at the FB pin, top tap taken at Cout. SS/RT parts at their pins.
- DNP footprints on floating pins (RT) leave a trace antenna: move the footprint to the pin or delete the trace.

## MCU / digital
- 100 nF at every VDD pin (≤ 1–2 mm), plus bulk nearby. `checks.py` section 1.
- Pull-ups/downs on boot or USB lines next to the pin (no long stubs on USB D±).

## Analog front end
- The inverting input / feedback network of a high-gain amplifier within 2 mm of the op-amp. Net length < 5 mm.
- High-value resistors (MΩ bias) away from switching nodes (≥ 3 mm), with no vias or silk on the high-Z node.
- ADC filter caps (C_ADC, divider caps) **at the MCU pin**; divider top resistors at the source node.
- Cold-junction sensor at the connector it represents, away from FETs and bulk caps.
- Inner-layer analog runs: are they next to SW/PWM/gate traces or under inductors? Is there a GND fill on that layer?
  Does the .kicad_dru have an analog keep-away rule?
- Load return current paths: do they run under the front end? Is a pour cut by a trace between the return pads and the bulk caps?

## Mechanics / assembly
- Holes (Tag-Connect guide pins, NPTH) under displays, glass or batteries on the other side.
- Single-sided assembly: the B side holds only hand-fitted parts. Hand-fitted parts are excluded from pos/BOM (`checks.py` section 7).
- Parts that differ from the library copy (DRC lib_footprint_mismatch): check them against the datasheet.
- LEDs and buttons on the user-facing side.

## Clean-up
- Alignment: neighbouring parts of the same kind on a common line with equal pitch and the same rotation (user rule). List offenders with coordinates.
- Track angles: `scripts/run.sh scripts/angles.py b.kicad_pcb` gives the share of non-0/45/90° segments; list the long ones that are not at fine-pitch escapes.
- DRC errors and their root cause, zone fragments, dangling vias, router rule areas left over.
- Silk: the user's rule is connector names, pin-1 marks, needed pin and test-point labels, no reference designators. Silk clipped by the edge.
- Notes vs board: layer count, outline, stackup, DNP plan.
