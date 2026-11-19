# JLCPCB: board rules, assembly, and part selection

**Sources:**
- [PCB capabilities](https://jlcpcb.com/capabilities/pcb-capabilities)
- [PCBA capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities)
- [PCBA price guide](https://jlcpcb.com/help/article/pcb-assembly-price)

These were checked on **2026-11-19**. JLC changes its limits and fees: re-check before relying on an edge value, and update this file with the date.

Templates for the custom rules are `templates/jlcpcb_2layer.kicad_dru` and `templates/jlcpcb_4layer.kicad_dru`. They hold JLC's limits. Copy one next to the board as `<board>.kicad_dru` and append any project rules (net-class keep-aways). Never give it to the Freerouting copy of the board; see `reference_4layer.md`.

## 1. Board rules

"JLC min" is the fab limit. "Design to" is what to put in Board Setup and the net classes, leaving margin and avoiding surcharges.

| Item | JLC min, 1–2 layers | JLC min, 4/6 layers | Design to | KiCad setting |
|---|---|---|---|---|
| Track width (1 oz outer) | 0.10 mm | 0.09 mm | 0.15 (2-layer), 0.127 (4-layer) default; 0.1 only for necks | `min_track_width`, net class |
| Spacing / clearance (1 oz) | 0.10 | 0.09 | 0.15 (2-layer), 0.127 (4-layer) default; 0.1 board minimum | `min_clearance`, net class |
| Track/space, 2 oz outer | 0.16 | 0.15 | 0.2 | net class |
| SMD pad to pad (different nets) | 0.15 | 0.15 | from footprints | template rule |
| Pad to track | 0.10 | 0.10 (0.09 at BGA pads) | = clearance | — |
| Via drill / diameter | 0.15 / 0.25 (extra cost) | same | **0.2 / 0.45** is the smallest with no surcharge; 0.3 / 0.6 for power | `min_via_diameter` 0.45, `min_through_hole_diameter` 0.2 |
| Surcharge | — | — | drill 0.1–0.15 mm (any via size), or drill 0.2–0.25 mm with via diameter < 0.45 mm | — |
| Via annular ring | via diameter ≥ drill + 0.1 (+0.15 preferred) | same | 0.125 (0.45/0.2) | `min_via_annular_width` |
| PTH annular ring (1 oz) | 0.18 min, 0.25 recommended | 0.15 min, 0.20 recommended | follow the recommended value | template rule |
| NPTH hole | 0.50 min | same | — | template rule |
| Via hole to via hole | 0.2 | same | 0.25 | `min_hole_to_hole` |
| Pad hole to pad hole | 0.45 | same | — | template rule |
| Via hole to track | 0.2 | same | 0.2 | `min_hole_clearance` |
| PTH hole to track | 0.28 (0.35 recommended) | same | 0.35 | template rule |
| Inner layer: via hole to copper | — | 0.2 | 0.2 | `min_hole_clearance` |
| **Inner layer: PTH pad to copper** | — | **0.3** | 0.3. Set a local pad clearance on PTH connector pads (USB-C shell, jacks), because zone fills ignore it otherwise | template rule (layer inner) |
| Copper to routed edge | 0.2 | same | 0.3 | `min_copper_edge_clearance` |
| Copper to V-cut | 0.4 | same | 0.5 | — |
| Silk line / text height | 0.15 / 1.0 | same | 0.15 / 1.0 | `min_text_thickness`, `min_text_height` |
| Silk to pad | 0.15 | same | 0.15 | `min_silk_clearance` |
| Solder mask bridge between pads | 0.10 (green and other colours), 0.13 (black/white), 0.20 (2 oz) | same | green | — |
| Mask expansion | 1:1 | same | 0 to 0.05 | pad mask margin |
| Plated slot width | 0.5 | 0.35 | — | — |
| Non-plated slot width | 1.0 | same | — | — |
| Castellated holes | hole ≥ 0.5, hole to edge ≥ 1, board ≥ 10 × 10 mm | same | Standard PCBA only | — |
| Board size | ≥ 3 × 3 mm (≥ 10 × 10 mm for Economic assembly) | same | — | — |
| Thickness | 0.4–2.0 mm standard (1.6 is the default) | same | 1.6 | stackup |
| Copper weight | outer 1–4.5 oz | outer 1/2 oz; inner 0.5 oz default (1/2 oz optional) | — | stackup |

**Notes:**
- **4-layer stackup:** **JLC04161H-7628** (1.6 mm, 1 oz outer, 0.5 oz inner, 7628 prepreg εr 4.4) was used for WRT.
  - For impedance-controlled traces (USB at 90 Ω differential, RF), use JLC's impedance calculator for that exact stackup.
  - Do not reuse widths from another stackup.
- **Inner copper is 0.5 oz by default:** keep high current off it (see `reference_4layer.md` section 4).
- **Hatched zones:** grid width and spacing ≥ 0.25 mm. Same-net track spacing ≥ 0.25 mm also applies, for example to meanders.
- **Via covering:**
  - Tented vias are the default and free.
  - "Epoxy filled & capped" (via-in-pad) costs extra on 4–6 layers; check the price.
  - A plugged via must be ≤ 0.5 mm in diameter and ≥ 0.35 mm from other mask openings.
- **Surface finish:** ENIG for QFNs at 0.4 mm pitch and BGAs (BGA pads of 0.2–0.25 mm require ENIG). Lead-free HASL is fine for 0.5 mm pitch and coarser.

## 2. Assembly (PCBA)

| | Economic | Standard |
|---|---|---|
| Sides | one side (SMT and THT) | one or both sides |
| Layers / thickness | 2, 4, 6 / 0.8–1.6 mm | 1–32 / any |
| Board size | 10 × 10 to 470 × 500 mm | 70 × 70 to 460 × 500 mm (smaller boards need a panel) |
| Quantity | 2–50 | 2–80 000 |
| Smallest package | 0402 | 01005 |
| Minimum IC pitch / BGA pitch | 0.4 mm / 0.5 mm | 0.35 mm / 0.3 mm |
| Edge rails / fiducials | not needed | needed |
| Castellated holes, gold fingers, edge plating | no | yes |
| Setup fee | $8.18 | $25.56 (one side), $51.12 (two sides) |
| Stencil | $1.53 | $8.21 (one side) |
| Feeder loading fee | **$3.07 per extended part type** | $1.53 per part type (basic and extended) |
| Hand-soldering labour (THT) | $3.58 per order, plus about $0.016 per joint | same |
| X-ray (BGA/QFN/LGA, automatic) | $1.64 per component for 1–10 pcs, less at volume | same |

**Rules that follow from this:**
- Economic assembly means a **single-sided** board. Put every JLC-placed part on one side (normally the top), and only hand-fit parts on the other side.
- QFNs at 0.4 mm pitch and 0402 passives are the Economic limit. Use 0402 or bigger, and no 0201.
- Boards under 70 × 70 mm need a panel for Standard assembly, but not for Economic.
- In Economic, the per-type loading fee is what makes extended parts expensive (section 3).

## 3. Part selection in the schematic (do this while drawing it)
1. **Every JLC-placed symbol gets an `LCSC` field** with the C-number. `export_jlcpcb.sh` reads it; parts without one are listed.
   - Check stock in the JLC parts library at selection time. Note the class (Basic, Preferred extended or Extended) in the BOM notes.
2. **Prefer Basic, then Preferred extended, then Extended.**
   - Basic parts have no loading fee.
   - JLC's FAQ says Preferred extended parts are exempt from the loading fee in Economic assembly (re-check).
   - Every *unique* extended part costs $3.07 in Economic.
3. **Consolidate values.**
   - Use one pull-up value (4.7k or 10k) and one bulk MLCC (10 µF) wherever the circuit allows.
   - Use one part type for two similar transistors (WRT: one DMP3017 for both P-FETs).
   - Consolidating saves fees and feeder changes.
4. **Package matches footprint.** The LCSC part's package (0402 vs 0603, SOT-23 vs SOT-23-6, QFN body size and exposed pad) must match the KiCad footprint. Check the land pattern against the datasheet for anything not a standard chip part (`reference.md` step 11).
5. **MLCC DC bias:** a 10 µF X5R 0805 at 12 V keeps only about 4 µF. Pick the voltage rating and size for the *effective* capacitance, and write the reason in the BOM notes.
6. **Power ratings:** check the resistor dissipation (WRT: a gate pull-up to 12 V needed a 1206). Check MOSFET Rds and the package's thermal limits.
7. **Hand-fit parts** (connectors from stock, expensive or large parts, bottom-side parts) are set in the *schematic*, so F8 does not reset them:
   - **Exclude from BOM** and **Exclude from position files**;
   - an `Assembly` field (`JLC` or `hand`) documents the intent.
8. **Not fitted:** mark the symbol **DNP**. The BOM and CPL export skip it.
9. **Keep connectors cheap** (user preference). Through-hole connectors JLC solders by hand cost labour; hand-fitting them yourself is free.

### Known-good JLC parts (WRT v2, 2026-11; re-check stock)

| Class | Parts |
|---|---|
| Basic, resistors 0402 1 % | 33R C25105, 120R C25079, 470R C25117, 3.3k C25890, 4.7k C25900, 5.1k C25905, 10k C25744, 15k C25756, 47k C25792, 100k C25741, 1M C26083, 10R C25077, 0R C17168 |
| Basic, resistors (other sizes) | 10M 0603 C7250, 1k 1206 C4410 |
| Basic, capacitors | 100n 16 V 0402 C1525; 100n 50 V 0402 C307331; 1n 50 V 0402 C1523; 10n 50 V 0402 C15195; 1µ 25 V 0402 C52923; 470n 25 V 0603 C1623; 2.2µ 16 V 0603 C23630; 4.7µ 16 V 0603 C19666; 10µ 10 V 0603 C19702; 10µ 25 V 0805 C15850 |
| Basic, other | red LED 0603 C2286 |
| Preferred extended | 2N7002K SOT-23 C22379475; H5VHD3BC 5 V ESD SOD-323 C20615804; 120k 0402 C25750; 510k 0402 C11616; 470p 0402 C1537 |
| Extended | CH32X035G8U6 QFN-28 C7437027; OPA376 SC-70-5 C2057475; DMP3017SFG-TP PowerDI3333 C49452329; NTC 10k B3435 0603 C524452 |

## 4. Order checklist
- Production files: `scripts/export_jlcpcb.sh board.kicad_pcb outdir`. It produces Gerbers for all layers, PTH and NPTH drills, the zip, and the BOM/CPL from the schematic.
- PCB settings: layers, thickness 1.6, the stackup for 4-layer boards, finish, via covering. "Remove order number" (or "specify a location") when the silkscreen has no room.
- PCBA settings: Economic, top side, the quantity. Upload the BOM and CPL, then **check the rotation preview** for QFN pin 1, SOT-23/SC-70 parts, diodes, LEDs and polarised capacitors. KiCad and JLC can differ by 90° or 180°.
- After any change to the board or the schematic, re-export. The export reads the saved files only.
