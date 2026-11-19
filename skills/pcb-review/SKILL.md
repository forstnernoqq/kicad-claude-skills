---
name: pcb-review
description: Review a KiCad PCB layout (placement, power paths, analog/switching separation, decoupling, vias, DRC, assembly flags) and write a concrete change list as a .md file. Use when the user asks to inspect, review, check or critique a routed or placed .kicad_pcb, including "look at the layout" or "inspect it visually". Builds on kicad-pcb-workflow; platform specifics come from the kicad-env-* skills.
---

# PCB layout review

The result is a Markdown file next to the board (`LAYOUT_REVIEW.md`) with **concrete, located changes** (ref, coordinates, net, length), ranked P1/P2/P3, plus a net-colored picture.
Read-only: never edit the board. Scripts run KiCad through `scripts/run.sh` (KiCad python) and `scripts/kcli` (kicad-cli), which resolve the platform via the `kicad-env-*` skill. General gotchas are in `kicad-pcb-workflow`.

## Steps
1. **Intent first.** Read the design notes / HANDOFF / routing report next to the board: currents (peak and rms), which parts are hand-fitted or on which side, layer count and outline decisions, the assembly house.
   Flag every place where the board contradicts the notes (layer count, outline, "at the FET", "at the jack", DNP plans).
2. **Copy** `board.kicad_pcb` + `.kicad_pro` + `.kicad_dru` into `$HOME/.pcb_review/` and rename all three to the same stem (`b.*`). Without the .kicad_pro the net classes and rules are defaults.
3. **Extract:** `scripts/run.sh scripts/extract.py $HOME/.pcb_review/b.kicad_pcb $HOME/.pcb_review` writes `report.txt` (stackup copper µm, footprints with dnp/pos/bom flags, pad nets, per-net length by layer/width, vias, zones) and `geom.json`.
4. **Heuristics:** `scripts/run.sh scripts/checks.py $HOME/.pcb_review/b.kicad_pcb [--power VBUS,/VH,...]`. It lists supply pins without a nearby cap, passives far from their IC, long sensitive nets and their inner-layer length, power-net widths and vias per pad, via-in-pad, traces leading only to DNP parts, and B-side parts that are still in the position file.
   It is a worklist: confirm each hit in the pictures before writing it down.
5. **DRC:** `scripts/kcli pcb drc --severity-all --format json --schematic-parity -o $HOME/.pcb_review/drc.json $HOME/.pcb_review/b.kicad_pcb`, then summarize with `../kicad-pcb-workflow/scripts/drc_summary.py`. Find the root cause: one dangling via often causes several errors.
6. **Look at it.**
   - `python3 scripts/plot_netmap.py $HOME/.pcb_review/geom.json $HOME/.pcb_review/netmap.png` runs with a normal python that has matplotlib (KiCad's python usually lacks it). Crop it per layer with `magick netmap.png -crop 100%x25%+0+Y +repage` for 4 layers.
   - `scripts/render.sh $HOME/.pcb_review/b.kicad_pcb $HOME/.pcb_review/img` renders the real copper, silk and courtyard, with left/right halves at readable zoom.
   - Read the images: the net map shows what the numbers don't, such as a switch node beside ADC traces, a pour cut by one trace, or heater current on an inner layer.
7. **Write** `LAYOUT_REVIEW.md` (structure below), copy `netmap.png` next to it as `layout_review_netmap.png`, delete `$HOME/.pcb_review`, and give the user a short summary with the top items.

## Gotchas
- `GetStackupDescriptor().GetList()` is not exposed in KiCad 10 python. `extract.py` parses the copper thickness from the file text instead. JLC 4-layer inner copper is 0.5 oz (15 µm): keep high current off it.
- Paste-only pads have an empty number and no copper layer. Don't mistake them for unconnected leads (PowerDI/QFN footprints have several).
- The `kicad-cli` svg export with `F.Fab` included is cluttered by value text; `render.sh` leaves fab out except in the courtyard view.
- DRC "unconnected items" at a zone corner coordinate are usually unstitched zone fragments, not real opens.
- Lock files (`~*.lck`) mean the board is probably open in KiCad. Reading is fine; mention it.

## Report structure
Header: the board, its size and layers, the method, and what the picture's colors mean. Then a 3–4 line verdict: what is good and what the main problem class is.
- **P1 (fix before fab):** each item has a "Now / Problem" table with refs, coordinates and lengths, then a **Change:** paragraph that says where things go and what to delete.
- **P2 (should)**, **P3 (clean-up, DRC, assembly flags, silk)**.
- **Decisions for you:** contradictions with the notes, each with a recommendation.
- **Order of work:** placement first, then hand-made pours and vias, then re-route, then DRC.
Mark estimates (IPC-2221 currents, thermal) as *(verify)*. Follow the user's silk preference (no reference designators).

See `checklist.md` for what to look for.
