#!/bin/sh
# export_jlcpcb.sh board.kicad_pcb outdir
# DRC summary, Gerbers (all copper layers incl. inner, mask, paste, silk, outline), PTH + NPTH drill, zip.
# If board.kicad_sch exists next to the board: JLC BOM + CPL as well (jlc_assembly.py; needs an LCSC field on the symbols).
set -e
S=$(cd "$(dirname "$0")" && pwd); . "$S/kenv.sh"
BOARD=$(readlink -f "$1"); mkdir -p "$2"; OUT=$(readlink -f "$2"); NAME=$(basename "$BOARD" .kicad_pcb)
SCH="${BOARD%.kicad_pcb}.kicad_sch"
rm -rf "$OUT/gerbers"; mkdir -p "$OUT/gerbers"
kcli pcb drc --severity-all --format json --all-track-errors --schematic-parity --refill-zones -o "$OUT/drc.json" "$BOARD" | tail -1
python3 "$S/drc_summary.py" "$OUT/drc.json"; rm -f "$OUT/drc.json"
INNER=$(grep -o '"In[0-9]*\.Cu"' "$BOARD" | tr -d '"' | sort -u -V | tr '\n' ',')
kcli pcb export gerbers --layers "F.Cu,${INNER}B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts" \
  --check-zones --subtract-soldermask -o "$OUT/gerbers/" "$BOARD" | tail -1
kcli pcb export drill --format excellon --excellon-separate-th --excellon-units mm --excellon-zeros-format decimal \
  --drill-origin absolute -o "$OUT/gerbers/" "$BOARD" | tail -1
for f in "$OUT"/gerbers/*NPTH.drl; do [ -f "$f" ] && ! grep -q '^X' "$f" && rm -f "$f"; done   # drop an empty NPTH file
python3 - "$OUT" "$NAME" <<'PY'
import zipfile, glob, os, sys
out, name = sys.argv[1:3]
z = zipfile.ZipFile(f'{out}/{name}_jlcpcb_gerbers.zip', 'w', zipfile.ZIP_DEFLATED)
for f in sorted(glob.glob(f'{out}/gerbers/*')):
    if not f.endswith('.gbrjob'): z.write(f, os.path.basename(f))
z.close(); print('zip:', f'{out}/{name}_jlcpcb_gerbers.zip', len(z.namelist()), 'files')
PY
if [ -f "$SCH" ]; then
  kcli sch export bom --fields 'Reference,Value,Footprint,LCSC,${DNP}' --labels 'Ref,Value,Footprint,LCSC,DNP' \
    --group-by '' -o "$OUT/_bom.csv" "$SCH" | tail -1      # kicad-cli already leaves out 'exclude from BOM' symbols
  kcli pcb export pos --format csv --units mm --side both -o "$OUT/_pos.csv" "$BOARD" | tail -1
  python3 "$S/jlc_assembly.py" "$OUT/_bom.csv" "$OUT/_pos.csv" "$OUT" "$NAME"; rm -f "$OUT/_bom.csv" "$OUT/_pos.csv"
fi
