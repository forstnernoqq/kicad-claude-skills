---
name: kicad-schematic
description: Create or restructure KiCad 10 schematics that people can read - functional blocks wired together, power symbols, labels only between blocks, signal flow, decoupling at the pins - plus JLC part selection while drawing. Edits .kicad_sch as text with a pin-position/lint tool (sch_tool.py) and proves the netlist did not change. Use when drawing a schematic, turning a netlist-style schematic (every pin on a net label) into a readable one, or reviewing schematic readability.
---

# KiCad schematics people can read

KiCad does not care how a schematic looks; people do. A netlist-style schematic (every pin stubbed to a net label) is correct, but nobody can follow the circuit. The goal is a page where each **functional block is drawn as a circuit**, and only the **connections between blocks** use labels.

Tool: `scripts/sch_tool.py` (plain python3, no KiCad needed; KiCad 8–10 files, single sheet).

| Command | What it does |
|---|---|
| `pins FILE [REF ...]` | pin tips in schematic coordinates (where wires must end) |
| `check FILE` | dangling wire ends, floating labels, unconnected pins, pins off the 1.27 mm grid |
| `lint FILE [--near MM]` | readability: share of pins connected only through a label, label-only links between pins that sit close together, power nets drawn as labels |
| `blocks FILE [--gap MM]` | which symbols are drawn near each other (the current clusters) |
| `same A.kicad_sch B.kicad_sch` | proves two schematics have identical connectivity (the same nets, by ref.pin) |

Its connectivity was checked against KiCad's own netlist on WRT v2: 62 of 62 nets identical, including rotated and mirrored symbols.

## Conventions (apply when drawing or restructuring)
1. **One block per function.** Examples: USB-C input with protection; buck regulator; LDO/filter; MCU with decoupling, crystal and boot/reset; debug header; each sensor front end; each power switch; LEDs and buttons; display.
   - Each block sits in its own area of the sheet: a graphic rectangle with a text title, or one hierarchical sheet per block when the page gets crowded (more than about 60 symbols or A3 is full).
2. **Inside a block, use wires.** Draw the circuit as it works: input on the left, output on the right; higher voltage at the top, GND at the bottom.
   - The switching loop, feedback divider, gate network and filter chains are drawn as connected wires, never as label pairs.
3. **Power uses power symbols.** GND, +3V3, VBUS and the like are power symbols (`power:GND`, `power:+3V3`, …) pointing up (supplies) or down (GND), not net labels.
   - A rail made in a block (the buck's +3V3) gets a power symbol at the output, so the rail is visible everywhere.
4. **Labels only between blocks.**
   - On one sheet: local labels (`label`), placed at the block edge on a short wire, not at the pin.
   - Between hierarchical sheets: hierarchical labels and sheet pins.
   - Name them by function (`USB_DP`, `T_CH1`, `FET_PWM`), not by pin.
5. **MCU and connector pins** may carry labels directly at the pin, since that is where blocks meet. Group them by function (USB, debug, I2C, analog, PWM) along the pin side.
6. **Decoupling at the pin it serves:** the 100 nF cap is drawn next to its VDD pin with a wire, then bulk, then the GND symbol. One cap symbol per pin, in pin order.
7. **Pull-ups, series resistors and RC filters** sit at the pin or the label they belong to, wired, not floating in a corner.
8. **Grid and geometry:**
   - Everything on the 1.27 mm grid; KiCad's pin tips are on it when the symbol origin is.
   - Wires are orthogonal, with a junction at every T.
   - No wire runs through a pin.
   - No 4-way junctions (offset them).
   - Text never overlaps a wire.
9. **Every unused pin** gets a `no_connect` flag. ERC must pass with 0 errors; ERC warnings get explained.
10. **Values and fields** stay visible: value, plus the voltage rating or the 1 % tolerance where it matters. The LCSC number is a field (hidden). JLC part selection: see `../kicad-pcb-workflow/reference_jlcpcb.md` section 3.

## Restructuring a netlist-style schematic (procedure)
1. **Baseline:**
   - copy the file (`x.kicad_sch.before_readable`);
   - run `sch_tool.py lint` and `blocks`;
   - export the netlist: `../kicad-pcb-workflow/scripts/kcli sch export netlist --format kicadxml`.
2. **Plan the blocks** from the netlist and the design notes: which symbols belong together, and which nets cross blocks (those keep labels). Write the plan (blocks, page areas, signal flow) and show it to the user before moving 200 symbols.
3. **Edit as text with KiCad closed.** For each block:
   - move its symbols (change `(at x y angle)` of each symbol instance; property text positions move with the same offset);
   - delete the old label stubs inside the block;
   - add wires between the pin tips from `sch_tool.py pins` (emit helpers in the module: `wire()`, `junction()`, `label()`, `global_label()`, `no_connect()`);
   - add power symbols. Copy an existing `power:` instance and give it a new UUID and a new `#PWR0xx` reference. The lib symbol must be in `lib_symbols`.

   Keep every `(uuid ...)` unique (`uuid.uuid4()`). Do not change symbol UUIDs or references, or the board's link to the schematic breaks.
4. **Prove nothing changed electrically:**
   - `sch_tool.py same before.kicad_sch after.kicad_sch` must report identical nets;
   - `sch_tool.py check` gives 0 geometry issues;
   - ERC gives 0 errors.
   - Then the user opens it, checks it visually, and presses F8. The board must show **no changes** except possibly net names.
5. Repeat per block. Small steps keep the diff reviewable.

## Gotchas
- **Coordinates:**
  - Library pins use y-up. The schematic uses y-down, and a symbol's `(at x y a)` rotates counter-clockwise on screen.
  - `(mirror x)` flips vertically and `(mirror y)` horizontally.
  - `sch_tool.py pins` applies all of this; do not hand-compute.
- **Multi-unit symbols:** each unit is a separate instance with `(unit n)`. Pins of unit 0 are shared by all units, for example the power pins of an op-amp.
- **Power symbols are global:** two GND symbols on different sheets are one net. A local label with the same name as a power net also joins it, which is confusing, so don't.
- **File versions:** `.kicad_sch` 20260306 for KiCad 10; project `.kicad_sym` libraries must stay at version 20251024 (newer fails to load). Symbol `justify` has no `center`.
- **KiCad must be closed** while editing the file as text. An open eeschema overwrites the edit on its next save.
- `sch_tool.py` handles single-sheet schematics. For hierarchical designs, run it per sheet; cross-sheet nets are not followed.
