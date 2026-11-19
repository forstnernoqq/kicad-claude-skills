---
name: kicad-env-windows
description: How KiCad 10 runs on a Windows machine (official installer, Claude Code in Git Bash) - kicad-cli.exe, KiCad's bundled python with pcbnew, Freerouting jar, host tools. Load together with kicad-pcb-workflow or pcb-review when working on Windows. Paths are NOT verified yet - verify and update on first use.
---

# KiCad on Windows

`env.sh` in this folder plugs into `kicad-pcb-workflow/scripts/kenv.sh`. It is picked when `uname -s` is MINGW, MSYS or CYGWIN (Git Bash) and `C:\Program Files\KiCad\<ver>\bin\kicad-cli.exe` exists. It defines:
- `kcli` = `<KiCad>/bin/kicad-cli.exe`;
- `kpy` = `<KiCad>/bin/python.exe`, the bundled python that ships pcbnew;
- `FR_JAR` = `%USERPROFILE%\Documents\KiCad\<ver>\3rdparty\plugins\app_freerouting_kicad-plugin\jar\freerouting-*.jar`, when Freerouting was installed through KiCad's Plugin and Content Manager.

## First session on Windows: verify, then update this file
1. Run `kicad-pcb-workflow/scripts/kenv_info`. It should print `platform: windows`, the kicad-cli version, the pcbnew version and the jar path. If something is missing, fix `env.sh`.
   - Is KiCad installed somewhere other than `C:\Program Files\KiCad`?
   - Is Documents redirected to OneDrive (then the jar path differs)?
   - Override without editing anything: `export KCLI_BIN=... KPY_BIN=... FR_JAR=...`.
2. **numpy** in KiCad's python is needed by `route4l/miniroute.py`, `draw.py` and the placement packer. Check with `kpy -c "import numpy"`. If it is missing: `kpy -m pip install numpy`. Ask the user first, because this changes the KiCad install.
3. **Host tools** for the review and render scripts:
   - a normal python with matplotlib (`plot_netmap.py`);
   - ImageMagick `magick` and `rsvg-convert` (`render.sh`). If `rsvg-convert` is missing, `magick in.svg out.png` can replace it; adapt `render.sh`.
   - Java 25+ for Freerouting.

   Record what exists here.
4. Write down the answers in this file (the "Verified" section below) and remove "NOT verified" from the description.

## Gotchas (expected; confirm)
- **Line endings:** `.sh` files must stay LF. A Git checkout with `core.autocrlf=true` breaks them. Use a `.gitattributes` with `*.sh text eol=lf` in the skills repo.
- **Paths:** Git Bash passes `/c/...` paths to native `.exe` programs as `C:\...` (MSYS path conversion), so `kcli`/`kpy` accept either. Paths inside JSON or `.kicad_*` files that python reads should be Windows-style, or relative.
- **No private /tmp** (unlike the Linux Flatpak): any folder works for scratch files.
- **Is KiCad running?** `tasklist | grep -i -E "kicad|pcbnew|eeschema"`.
- KiCad on Windows locks open files harder than on Linux: a save from a script can fail while the editor has the file open.

## Verified
(nothing yet)
