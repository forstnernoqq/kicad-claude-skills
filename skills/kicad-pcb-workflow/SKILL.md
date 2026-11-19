---
name: kicad-pcb-workflow
description: KiCad 10 PCB design workflow from schematic to JLCPCB order (schematic edits, F8, placement via Konnect or pcbnew, Freerouting, 4-layer routing, GND/heater copper, DRC, JLC Gerbers + BOM + CPL, footprint checks). Use for any KiCad board work. Platform-neutral; load the matching kicad-env-* skill for how KiCad runs on this machine.
---

# KiCad PCB workflow (platform-neutral)

**Platform first.** Every command goes through `scripts/kcli` (kicad-cli) and `scripts/kpy` (KiCad's python with pcbnew).
- They pick the right tools through `scripts/kenv.sh`, which sources the matching platform skill: `kicad-env-linux-flatpak` or `kicad-env-windows`.
- Run `scripts/kenv_info` once per session. It prints the platform, the KiCad and pcbnew versions, and the Freerouting jar.
- Read that platform skill's SKILL.md for its gotchas.
- Shell scripts are POSIX sh. On Windows they run in Git Bash.

Step details are in `reference.md`; read only the step you are on. **JLC board rules, assembly tiers, fees and part selection** are in `reference_jlcpcb.md`; KiCad rule templates are in `templates/jlcpcb_{2,4}layer.kicad_dru`. **Drawing or restructuring schematics:** use the `kicad-schematic` skill. **For 4-layer, dense, JLC-assembled or high-current boards, also read `reference_4layer.md`.** It covers JLC 4-layer rules, Freerouting with a GND plane, the GND clean-up chain, heater pours, pcbnew SWIG pitfalls and the lessons from WRT; its scripts are in `scripts/route4l/`.

## Gotchas (KiCad and Konnect, any OS)
- **KiCad editors hold files.**
  - Konnect refuses to edit a board that KiCad has open (AS_BUSY).
  - An open editor overwrites your offline edit on its next save. Ask the user to close it ("Don't save") first, and verify afterwards. Lock files `~*.lck` are a hint, not proof.
- **KiCad caches libraries.** A text edit of a `.kicad_mod` or `.kicad_sym` while KiCad runs is not seen. "Update footprint from library" then writes the *old* version back. Have the user restart KiCad (or reload the library) before updating from it.
- **Board-only settings are lost:**
  - F8 resets assembly flags from the schematic.
  - "Update from library" resets footprint flags, such as jumper pads.
  - Merging a candidate board does not bring its `.kicad_pro` net classes.

  Put such settings in the schematic, the library or the project file.
- KiCad reads **project library tables only when the project is opened**. After adding `fp-lib-table` or `sym-lib-table`, the user must reopen the project, or F8 reports "footprint not found".
- **Konnect:**
  - Tools that need a live board need the PCB editor open; schematic tools work on files.
  - Load toolsets with `load_toolset` (`pcb_components`, `pcb_board`, `sch_export`, `verification`, `pcb_export`).
  - `save_project` saves the live board; `get_board_2d_view` renders the saved file only.
  - `export_specctra_dsn` refuses bottom-side footprints and boards with tracks or zones; use `scripts/export_dsn.py`.
  - If `update_pcb_from_schematic` fails, ask the user to press **F8**.
  - Do not run `konnect init` without asking.
- KiCad 10 files: `.kicad_sch` version 20260306, but `.kicad_sym` libraries must use version 20251024 (newer fails with "Unable to load library"). Symbol `justify` has no `center`.
- Mouser pages usually can't be fetched: use WebSearch and say which Mouser numbers are inferred.
- `rm -rf` is blocked by the Claude Code safety layer: `mv` scratch into a `scratch/` folder and tell the user what to delete.

## Pipeline (details in reference.md)
1. Clarify geometry before placing (edges, connector type, dimensions, sides). Ask once, with a recommendation.
2. Pinouts from physical evidence; show the pin table to the user.
3. Schematic: readable blocks, JLC parts with LCSC fields, and assembly flags in the symbols (`kicad-schematic` skill). Run ERC on a copy: `scripts/kcli sch erc --severity-all --format json`.
4. F8 by the user, then `save_project`. Read pad coordinates from the saved `.kicad_pcb`.
5. Placement via Konnect or pcbnew. 6. Autoroute with `scripts/route.sh` (2-layer) or the `route4l/` method. 7. Silkscreen with `scripts/add_silk.py`.
8. DRC: target 0 errors, 0 unconnected, 0 parity issues. 9. Work on a copy until the user says it is done.
10. JLC files with `scripts/export_jlcpcb.sh` (Gerbers, drills, zip, plus BOM/CPL from the schematic). 11. Check footprints against datasheets. 12. BOM. 13. Update `HANDOFF.md`.

## Layout style rules (user, apply to every layout)
- **Align and space evenly.** Close-by parts of the same kind (resistor and cap columns, decoupling rows, LEDs, buttons) get a common x or y, equal pitch and the same rotation, unless there is a specific electrical reason not to.
  - Snap placement to a 0.05/0.1 mm grid.
  - After placement, run a pass that lines up neighbours whose centres differ by less than 0.3 mm.
- **45° routing.** Tracks are horizontal, vertical or 45°. Arbitrary angles only where unavoidable (fine-pitch escapes, tight gaps).
  - Check with `../pcb-review/scripts/angles.py`. WRT final3 had 18 % off-angle segments, mostly from the grid router's line-of-sight smoothing and hand pre-routes. Fix that in the router, not afterwards.
- **Minimum track width:** 0.1 mm board minimum (JLC 4-layer allows about 0.09); default class 0.127–0.15. Use 0.1 only for necks at QFN escapes and between 0402 pads.

## 4-layer pointers (details in reference_4layer.md)
- Make GND an In1 plane and strip the GND pins from the DSN, so Freerouting routes only signals; add GND vias and pours after.
  - Relax class clearances on the router copy only, and never add analog-separation DRC rules to that copy.
  - **Ship the relaxed net classes in the project `.kicad_pro`**, or the user's board shows 100+ clearance errors.
- pcbnew objects added to a board must be kept in a global list (SWIG segfaults otherwise); use `RemoveNative`. Run DRC-guided prune loops, because geometric via checks give false negatives.
- Wide heater paths need reserved copper (a locked pre-routed bus plus pours) and a placement that makes room; pours added after routing gain almost nothing.
- **Placement fixes most review findings**; see `reference_4layer.md` section 9 before starting a layout.
- Build candidates in `route_job/<name>/`, leave the live project board alone, and list scratch folders for the user to delete.

## User preferences
- Short, decisive answers with a recommendation.
- Schematic and BOM first, layout second.
- Compact boards and cheap parts.
- Silkscreen: only connector names, pin-1 marks and necessary pin names; no reference designators.
- Do not change the schematic unprompted.
- The user does the final manual clean-up and runs DRC themselves, often on Windows and Linux alternately.
