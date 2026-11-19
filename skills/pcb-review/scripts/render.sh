#!/bin/sh
# render.sh board.kicad_pcb outdir [zoom]  -- per-layer PNGs (copper+silk, no fab clutter), plus left/right halves.
# Needs rsvg-convert + ImageMagick (magick) on the host.
B="$1"; O="$2"; Z="${3:-14}"; K="$(cd "$(dirname "$0")" && pwd)/kcli"; mkdir -p "$O"
n=$(grep -c '"In[0-9]*.Cu"' "$B" >/dev/null; grep -o '(layer "In[0-9]*\.Cu"' "$B" | sort -u | wc -l)
set -- "F.Cu,F.SilkS,Edge.Cuts:F" "B.Cu,B.SilkS,Edge.Cuts:B" "F.SilkS,Edge.Cuts:silkF" "B.SilkS,Edge.Cuts:silkB" "F.Courtyard,B.Courtyard,F.Fab,B.Fab,Edge.Cuts:court"
i=1; while [ $i -le "$n" ]; do set -- "$@" "In$i.Cu,Edge.Cuts:In$i"; i=$((i+1)); done
for spec in "$@"; do L=${spec%%:*}; N=${spec##*:}
  $K pcb export svg --layers "$L" --mode-single --fit-page-to-board --exclude-drawing-sheet -o "$O/$N.svg" "$B" >/dev/null 2>&1
  rsvg-convert -b white -z "$Z" "$O/$N.svg" -o "$O/$N.png"
  w=$(magick identify -format %w "$O/$N.png"); h=$(magick identify -format %h "$O/$N.png")
  magick "$O/$N.png" -crop $((w/2+100))x$h+0+0 +repage "$O/${N}_L.png"
  magick "$O/$N.png" -crop $((w/2+100))x$h+$((w/2-100))+0 +repage "$O/${N}_R.png"
done; ls "$O"/*.png
