# 4-layer JLCPCB board: findings from WRT v2 (2026-11)

Read this when a board is 4-layer, JLCPCB-assembled, dense (about 100 parts on 56 x 18 mm), or has a heater/power path. Scripts are in `scripts/route4l/` (project-specific constants are marked below).

## 1. Setting up the board for JLCPCB 4L (via pcbnew/text, KiCad closed)
- Stackup JLC04161H-7628, 1.6 mm: 1 oz outer, 0.5 oz inner, prepreg 0.2104, core 1.065. ENIG is a sensible finish for fine pitch QFN.
- Rules used (full JLC table and templates: `reference_jlcpcb.md`; note the 0.3 mm inner-layer PTH pad clearance, which WRT missed at the USB-C shell): clearance/track min 0.1 (default class 0.15), via 0.45/0.2 min (default 0.5/0.2), annular 0.125, copper-to-edge 0.3, hole-to-hole 0.25, NPTH >= 0.5, silk text >= 1.0 high / 0.15 stroke, mask expansion 0.05, pad holes 0.45 custom rule.
- KiCad must be closed before writing `.kicad_pro`/`.kicad_dru`; Konnect refuses otherwise.
- Net classes worth having from the start: Default, Power_heater (1.0 mm, clearance 0.2, via 0.6/0.3), Buck_SW, PWM_gate, Analog_sensitive, USB_FS (diff pair), Supply_3V3.
- Do not put "analog separation" custom DRC rules (SW node vs analog nets, etc.) in the `.kicad_dru` you hand to the router run: they produced 80+ DRC errors and starved the router. Use net classes and review by eye.

## 2. Freerouting on a 4L board (what actually worked)
- Freerouting jar 2.5.0 (the path comes from the platform skill, as `$FR_JAR` in `kenv.sh`), Java 25+; DSN from `scripts/export_dsn.py` (pcbnew), never Konnect's exporter.
- Make GND a plane, not routed copper: set In1 to `LT_POWER`, fill a GND zone on In1, then edit the DSN and remove GND pins: `(net GND (pins ))` (regex in `scripts/route4l/pipe.sh`). The router then routes only signals. GND pads reach In1 through vias added afterwards (section 3).
- Relax the router copy only (`relax.py`): default clearance/track 0.127, vias 0.45/0.2, heater class 0.5/0.15. Setting heater clearance to 0.3-0.4 mm made 41 nets unroutable; stay at 0.15.
- Keep-out rule areas along the board edge (0.35 mm, incl. rounded corners) and around milled holes stop the router violating copper-to-edge (`stage2b.py`; constants X0/Y0/R are WRT-specific). Remove them again once routed.
- The optimiser pass only runs when 0 nets are unrouted. A 56 x 18 mm, ~100 part board routed in under a minute once the placement was loose enough.
- `ImportSpecctraSES` then `ZONE_FILLER(b).Fill(zones)` (`imp.py`).
- Tracks that Freerouting necks below 0.1 mm: widen to 0.1 (all of them) after import.
- **Locked pre-routed tracks** export as `(type fix)`. A fixed wire that touches no pin or via is NOT part of the net and the router ignores or cuts it; it must end on pads/vias of the same net (put vias into the pad or the pour).

## 3. GND clean-up after routing (the long tail)
Chain in `chain.sh` (post13 -> prune -> frag2 -> heat2 -> gndfix2 -> prune -> frag2 -> prune -> DRC):
1. `post13.py`: GND pours on F/B plus stitching vias placed only where an exact-shape clearance check passes, QFN exposed-pad vias, vias for pour fragments, short stubs for isolated pads, widen thin tracks, solid zone connection for starved thermals. Constants `RC` (corner radius) and `J3H` (milled holes) are WRT-specific.
2. `prune.py`: the exact-shape check still gives false negatives, so always run DRC and delete GND vias that appear in clearance/hole errors, refill, repeat 2-3 times.
3. `frag2.py`: remove or stitch copper islands. 4. `gndfix2.py`: via-in-pad / stubs for pads still floating (hand-fitted pads such as bank caps, J4, buck GND pin). 5. `full4.py`: `ZONE_CONNECTION_FULL` per pad (`SetLocalZoneConnection`) for pads starved by thermal reliefs.
Final state on WRT: all pads connected, 6 DRC items left (pairs of tiny GND islands). Accept that and tell the user.

## 4. Heater / high-current paths
- Pours alone do nothing when the corridor is already full of other routes (average +0.1 mm width). Reserve the route first: pre-route a wide locked bus (2 mm along the board edge) and tie it into a pour under the part bank, then let the router work around it. This needed the placement changed (series FET next to the connector, bulk bank next to the load FET) and +1 mm board length.
- Heater pours (`heat2.py`): per net (VBUS, /VH, /OUT_CH1) and per layer (F, In2, B) a union of 3 mm wide rectangles along each routed track, solid pad connection, priority above GND. Constants for the VH bank pocket polygon are WRT-specific.
- Use via arrays for layer changes (0.45/0.2 vias carry about 1 A each), and via-in-pad only on hand-fitted pads. On JLC-assembled QFN exposed pads ask for filled/capped vias or accept solder wicking.
- In2 is a 0.5 oz layer and carries signals too; do not count it as a clean power plane.
- Measuring: `path.py` is a resistance proxy over tracks only (ignores zones), so it understates pours. DRC-guided track widening (`widen.py` idea: widen, run DRC, revert segments that cause errors) only works where room exists.

## 5. Placement method that worked
- Keep rot-0 courtyard bboxes per footprint (from pcbnew) in a JSON, run a free-rectangle packer (numpy summed-area table), connectivity-weighted target centroids, and sweep parameters (board length/height, part gap) writing one JSON per run. Render each (`draw.py`) and compare. The v1-like arrangement needed 56 x 18 mm vs the hoped 50 x 15 mm; user allowed up to 20 x 60.
- Apply positions with pcbnew (`t1.py`) or Konnect `set_component_placements`. When pasting batches by hand a typo happened (R8 y): diff against the saved board (`cmpb2.py`) and apply only changed parts.
- Never edit the live project board while KiCad is open (Konnect returns AS_BUSY). Build candidates in `route_job/<name>/` and leave the project board untouched.

## 6. Konnect / pcbnew quirks learned
- Bottom side model: board pos/orientation of a B-side footprint = mirror local y, then rotate theta CCW (`x' = x c + y s`, `y' = -x s + y c`). Verify with `get_pad_position` (arg `pad_number`; tools need `board`).
- pcbnew SWIG: every object you `Add` to a board (zones, vias, outlines, LSET) must live in a global `KEEP` list, otherwise segfault (exit 139) or "typed object lost". `Remove` on tracks/vias must be `RemoveNative`. Split big scripts into stages.
- API names: `z.SetDoNotAllowZoneFills` (no `CopperPour`), `PAD.GetEffectiveShape(layer)`, `zone.HitTestFilledArea(layer, pt, 0)`, `SetIslandRemovalMode`, `SetLocalZoneConnection`.
- Do not `pkill -f freerouting`: the pattern also matches your own shell command line. Wait with `pgrep -f "freerouting-.*jar"`.
- The safety layer blocks `rm -rf` of directories/globs: `mv` scratch into a `scratch/` folder and tell the user what to delete.

## 7. Parts / footprint notes from this board
- TPS62932 needs inductor Isat >= ~0.8-1 A (IPEAK_MIN 0.53 A, high-side limit 2.8-4 A) even for a 30 mA load; 4.7 uH 2520 (Isat about 1.4 A) was chosen.
- OLED flex: fingers exposed on both faces, so fold-over-its-own-pads works; a 1 mm VHB tape gives a fold radius around 0.45 mm, which is the main risk. Wrap-around footprint was dropped.

## 8. Delivering the result
Say what was changed vs the user's board, DRC counts, and what to check by hand (heater path width, sense net length, via-in-pad choices, router leftovers: keepouts, In1 as power layer). List scratch folders for the user to delete. Do not change the schematic unprompted.

## 9. Lessons from WRT final3 (review fix-up, 2026-11)
Result: every P1/P2 item fixed, DRC 0/0/0; critical nets shrank 5-15x (buck SW 13.4 -> 2.0 mm, op-amp (-) 34 -> 3.4, Q3 gate 18.8 -> 4.4).
- **Placement is the fix.** Almost every review finding (long SW/FB nodes, analog next to FETs, far decoupling) was a placement problem; re-routing cannot repair it. Build functional cells first (buck cell, gate cell, front-end cell, MCU + decoupling), each with its critical loop closed by hand, then place cells, then route.
- **Put the MCU next to the analog front end**, not next to USB. On WRT the MCU stayed left and the front end right, so T_CH1/NTC/OUT_SENSE are still 37-43 mm. Decide this before anything else.
- **Pre-route what matters as locked copper**: heater paths + via arrays, buck SW/VIN/GND loop, QFN escape lanes for the crowded pin row, cap fan-outs at connectors. Freerouting then only does logic signals.
- **Freerouting limits**: a via in the middle of a fixed wire is not seen as connected (empty those nets' pins in the DSN and keep the copper as obstacles); netless pads get the default clearance; class_class rules in the DSN do give an analog keep-away. Expect 1-5 unrouted nets on a dense board: close them with `miniroute.py` (grid A*, class-aware clearance, `'net'` goal mode, per-job layers; constants are WRT-specific). **TODO: restrict its path smoothing to 0/45/90° shortcuts** (it currently makes arbitrary angles).
- **Keep `.kicad_pro` + `.kicad_dru` next to every intermediate board**, or zone fill and DRC silently use default rules.
- **Measure before/after**: per-critical-net length and layer table (`metrics.py`) for the report; it convinced faster than pictures.
- Use `prune2.py` (skips locked items) instead of `prune.py`, which deletes locked pre-route vias. Use `svia.py` for GND vias (uses `GetEffectivePolygon`).
- pcbnew KiCad 10: `PAD.GetEffectiveShape()` can return stale geometry after moving a footprint, use `GetEffectivePolygon()`; `BoardConnectivity` re-nets a via that overlaps another net's pad; remove "dangling" tracks one at a time with a connectivity check (some carry the connection in their middle).
- Jack/connector legs with duplicate pad numbers: `FOOTPRINT.SetDuplicatePadNumbersAreJumpers(True)` instead of routing every leg; set it in the library too.
- Do alignment and 45° clean-up as part of the job (SKILL.md style rules), not as a user chore.
- **Board-only settings do not survive the user's clean-up:** F8 resets assembly flags from the schematic, "update footprint from library" resets footprint flags (jumper pads), and merging a candidate board does not carry its `.kicad_pro` net classes (gives 100+ clearance errors). Put flags in the schematic or library, and ship the net classes in the project file, or list each one as a merge step.
- Check vias-in-pad on *every* assembled part (`pcb-review` `checks.py` section 5), not only the QFN exposed pad. WRT final3 had 5 on 0402/0603 GND pads that the report missed.
