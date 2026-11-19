# KiCad + JLCPCB skills for Claude Code

Agent skills for [Claude Code](https://docs.claude.com/en/docs/claude-code) that take a KiCad 10 project from schematic to a JLCPCB order:
- readable schematics;
- JLC part selection;
- placement and routing (including dense 4-layer boards with high-current paths);
- layout reviews;
- DRC;
- Gerbers, BOM and CPL files.

There is also a small KiCad symbol library. The skills were written while designing real boards, but they work for any KiCad 10 project. The scripts run on **Linux (KiCad Flatpak)** and **Windows (KiCad installer, Git Bash)** through a small platform layer.

## Contents

| Skill | Platform | What it does |
|---|---|---|
| [`kicad-schematic`](skills/kicad-schematic/SKILL.md) | any | Readable schematics: functional blocks wired together, power symbols, labels only between blocks. `sch_tool.py` gives pin positions, geometry checks and a readability lint, and proves that a restructured schematic has the same nets as before |
| [`kicad-pcb-workflow`](skills/kicad-pcb-workflow/SKILL.md) | any | The full pipeline: schematic → F8 → placement → Freerouting → 4-layer method (GND plane, heater copper, GND clean-up) → DRC → JLC production files. It also holds the [JLC rules and part-selection guide](skills/kicad-pcb-workflow/reference_jlcpcb.md) and KiCad `.kicad_dru` templates |
| [`pcb-review`](skills/pcb-review/SKILL.md) | any | Reviews a routed board: decoupling, power paths, analog/switching separation, vias, assembly flags, 45° routing. Writes a ranked change list (`LAYOUT_REVIEW.md`) with a net-coloured picture |
| [`kicad-env-linux-flatpak`](skills/kicad-env-linux-flatpak/SKILL.md) | Linux | How KiCad runs as the Flatpak `org.kicad.KiCad`: commands, private `/tmp`, Freerouting jar, host tools, shell quirks |
| [`kicad-env-windows`](skills/kicad-env-windows/SKILL.md) | Windows | How KiCad runs from the official installer under Git Bash. **Not verified yet**: run `kenv_info` on the first Windows session and update it |

| Library | Contents |
|---|---|
| [`libraries/RCL.kicad_sym`](libraries/README.md) | Generic resistor and capacitor symbols that show value, package and tolerance or dielectric |

## Install

```sh
git clone <repo-url> kicad-claude-skills
cd kicad-claude-skills
./install.sh            # Linux/macOS: symlinks into ~/.claude/skills (git pull updates them)
                        # Windows (Git Bash): copies (symlinks need Developer Mode there)
./install.sh --copy     # always copy
./install.sh --force    # replace existing skills of the same name (old ones are renamed *.old-<date>)
```

Claude Code picks up skills from `~/.claude/skills/<name>/SKILL.md` at the start of a session. To check the platform layer:

```sh
~/.claude/skills/kicad-pcb-workflow/scripts/kenv_info
# platform: linux-flatpak
# freerouting jar: …/freerouting-2.5.0.jar
# 10.0.8
# pcbnew 10.0.8 python 3.14.9
```

To install the symbol library, open KiCad → Preferences → Manage Symbol Libraries and add `libraries/RCL.kicad_sym` with the nickname `RCL`.

## Requirements

| | Linux | Windows |
|---|---|---|
| KiCad 10 | Flatpak `org.kicad.KiCad` | official installer (`C:\Program Files\KiCad\10.0`) |
| pcbnew python | inside the Flatpak (numpy included) | `KiCad\10.0\bin\python.exe` (check numpy) |
| Freerouting | KiCad PCM plugin `app_freerouting_kicad-plugin`, Java 25+ | same |
| Review pictures | host `python3` + matplotlib, `rsvg-convert`, ImageMagick | python + matplotlib, ImageMagick |
| Shell | POSIX `sh` | Git Bash (Claude Code's shell on Windows) |
| Optional | Konnect KiCad MCP plugin (installed through KiCad's PCM), for live placement | same |

## How the platform layer works

The general skills never call KiCad directly. They use two wrappers:
- `kicad-pcb-workflow/scripts/kcli`: `kicad-cli` on this machine;
- `kicad-pcb-workflow/scripts/kpy`: KiCad's python with `pcbnew`.

Both source `scripts/kenv.sh`, which loads the first `kicad-env-*/env.sh` that recognises the machine. That file defines the shell functions `kcli` and `kpy` and the variable `FR_JAR`.

To use your own tools without a platform skill:

```sh
export KCLI_BIN=/path/to/kicad-cli KPY_BIN=/path/to/python-with-pcbnew FR_JAR=/path/to/freerouting.jar
```

To support a new setup (native Linux KiCad, macOS), add `skills/kicad-env-<name>/` with:
- an `env.sh` that sets `KENV` only when it detects its platform;
- a `SKILL.md` describing that platform's gotchas.

The general skills don't change.

## Typical use (what to ask Claude)

| Ask | What happens |
|---|---|
| "Restructure the schematic so the power supply is drawn as a circuit" | `kicad-schematic`: lint, block plan, text edits, then `sch_tool.py same` before and after |
| "Place and route the board, 4 layers, JLC" | `kicad-pcb-workflow`: the candidate goes in `route_job/<name>/`; the project board is left alone |
| "Review the layout" | `pcb-review`: writes `LAYOUT_REVIEW.md` next to the board |
| "Create the production files for JLC" | `scripts/export_jlcpcb.sh board.kicad_pcb production/`: zip, BOM, CPL |

## Repository layout

```
install.sh                       links or copies skills/* into ~/.claude/skills
skills/
  kicad-schematic/               SKILL.md, scripts/sch_tool.py
  kicad-pcb-workflow/            SKILL.md, reference.md, reference_4layer.md, reference_jlcpcb.md,
                                 templates/jlcpcb_{2,4}layer.kicad_dru,
                                 scripts/ (kcli, kpy, kenv.sh, kenv_info, route.sh, export_jlcpcb.sh, jlc_assembly.py, …),
                                 scripts/route4l/ (4-layer pipeline: placement, DSN, GND chain, heater pours, miniroute.py)
  pcb-review/                    SKILL.md, checklist.md, scripts/ (extract, checks, angles, plot_netmap, render)
  kicad-env-linux-flatpak/       SKILL.md, env.sh
  kicad-env-windows/             SKILL.md, env.sh
libraries/
  RCL.kicad_sym                  generic R/C symbols with spec fields
```

## Conventions for contributors
- **Shell scripts are POSIX `sh` with LF line endings** (`.gitattributes` enforces this), so they run in Git Bash on Windows.
- **Platform-specific paths and quirks go only in `kicad-env-*`.**
- **Python:**
  - scripts that use `pcbnew` run with `kpy`;
  - everything else is plain `python3` (standard library; numpy only where noted);
  - pcbnew scripts keep every object they add in a global list (SWIG crashes otherwise).
- **Lessons go into the skill files.** Each `SKILL.md` stays short and links to its reference files for detail. Anything learned the hard way goes into the gotchas, with the board it came from.
- **Some `route4l/` scripts contain board-specific constants**, marked in `reference_4layer.md`. Treat them as worked examples, not general tools.
- **JLC numbers carry a "checked on" date.** Re-check against JLC's capability pages before relying on edge values.
- **KiCad library files stay at format version 20251024** (KiCad 10).

## Status
- Used end to end on two boards (2026-11):
  - a 2-layer WCH-LinkE/TC2030 adapter;
  - a 4-layer 56 × 18 mm heater controller with about 100 parts (CH32X035, thermocouple front end, 3.5 A heater path, buck).
- The Windows platform skill is untested.

## License

[The Unlicense](LICENSE): public domain. Use, copy, change and sell it however you like, with no conditions.
