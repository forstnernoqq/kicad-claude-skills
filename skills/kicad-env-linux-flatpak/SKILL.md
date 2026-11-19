---
name: kicad-env-linux-flatpak
description: How KiCad 10 runs on a Linux machine where KiCad is the Flatpak org.kicad.KiCad (kicad-cli, pcbnew python, Freerouting jar, private /tmp, host tools, shell quirks). Load together with kicad-pcb-workflow or pcb-review when working on Linux, or when kicad-cli / pcbnew python / Konnect misbehave there.
---

# KiCad on Linux (Flatpak)

`env.sh` in this folder plugs into `kicad-pcb-workflow/scripts/kenv.sh`. It is picked when `flatpak info org.kicad.KiCad` succeeds. It defines:
- `kcli` = `flatpak run --command=kicad-cli org.kicad.KiCad`;
- `kpy` = the Flatpak's `python3` with `--filesystem=/tmp --filesystem=home`, with wx and leak noise filtered out;
- `FR_JAR` = `~/.var/app/org.kicad.KiCad/data/kicad/<ver>/3rdparty/plugins/app_freerouting_kicad-plugin/jar/freerouting-*.jar`.

## Gotchas
- There is no host `kicad-cli`. `~/.local/bin/kicad-cli-flatpak` also exists; **do not edit that wrapper**. It has no `--filesystem=/tmp`.
- The **Flatpak has a private /tmp**. Without `--filesystem=/tmp`, kicad-cli and pcbnew only see files under `$HOME`. `kpy` passes it; for `kcli`, keep its inputs and outputs under `$HOME` (for example a `scratch/` folder in the project).
- The Flatpak python (3.14) has **numpy only**: no matplotlib, scipy, numba or shapely. Plot with the host `python3` (for example `pcb-review/scripts/plot_netmap.py`).
  - Do not use `python3 -I` for scripts that import sibling modules.
  - `kpy` merges stderr into stdout, because of the noise filter.
- **Is KiCad running?** `pgrep -af pcbnew|eeschema` finds nothing under Flatpak; use `pgrep -af "kicad"` (it shows `bwrap ... kicad-startup`).
- Konnect `update_pcb_from_schematic` fails, because the netlist goes to the private /tmp: ask the user to press **F8**. Ignore Konnect's `check_freerouting` "not found".
- Freerouting needs host Java 25+ (Java 27 worked). Run it headless: `java -Djava.awt.headless=true -jar "$FR_JAR" --gui.enabled=false -de x.dsn -do x.ses -mp 40`.
- Stock KiCad symbol libraries (for copying a lib symbol into a schematic): `/var/lib/flatpak/runtime/org.kicad.KiCad.Library.Symbols/x86_64/stable/active/files/symbols/`.
- **Shell:** the interactive shell is zsh, which does not word-split a string variable. Use `${=var}`, `set -- ${=var}` or a wrapper script. Glob misses are errors in zsh (`no matches found`); guard with `ls` or run the commands inside `sh -c`.

## Host tools on this machine (2026-11)
- Available: python3 3.14 with matplotlib, `rsvg-convert`, ImageMagick `magick`, Java, `gcc`/`g++`, `pdftotext`/`pdftoppm`.
- No Rust toolchain; the user is willing to install one (`sudo pacman -S rustup && rustup default stable`, CachyOS/Arch).
