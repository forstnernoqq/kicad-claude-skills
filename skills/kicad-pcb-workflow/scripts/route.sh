#!/bin/sh
# route.sh board.kicad_pcb workdir [freerouting passes=40]   (2-layer boards; 4-layer: see route4l/ and reference_4layer.md)
# The board must be saved. Work happens on a copy in workdir.
set -e
S=$(cd "$(dirname "$0")" && pwd); . "$S/kenv.sh"
BOARD=$(readlink -f "$1"); WD=$(readlink -f "$2"); PASSES=${3:-40}
[ -n "$FR_JAR" ] || { echo "Freerouting jar not found (install the Freerouting plugin via KiCad's PCM)"; exit 1; }
mkdir -p "$WD"; cp "$BOARD" "$WD/in.kicad_pcb"; cp "${BOARD%.kicad_pcb}.kicad_pro" "$WD/in.kicad_pro" 2>/dev/null || true
cd "$WD"
kpy "$S/export_dsn.py" in.kicad_pcb adapter.dsn
timeout 280 java -Djava.awt.headless=true -jar "$FR_JAR" --gui.enabled=false -de adapter.dsn -do out.ses -mp "$PASSES" > freerouting.log 2>&1
tail -n 3 freerouting.log
kpy "$S/import_ses_finish.py" in.kicad_pcb out.ses routed.kicad_pcb 0.15 1
echo "routed board: $WD/routed.kicad_pcb  (set min_track_width in the .kicad_pro, then run DRC)"
