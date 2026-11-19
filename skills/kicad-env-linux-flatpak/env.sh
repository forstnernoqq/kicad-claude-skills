# Platform: Linux with KiCad as the Flatpak org.kicad.KiCad (sourced by kicad-pcb-workflow/scripts/kenv.sh).
if command -v flatpak >/dev/null 2>&1 && flatpak info org.kicad.KiCad >/dev/null 2>&1; then
  KENV=linux-flatpak
  kcli() { flatpak run --command=kicad-cli org.kicad.KiCad "$@"; }
  # --filesystem=/tmp: the Flatpak has a private /tmp, and scratch files often live in the host /tmp.
  # The grep drops wx debug and leak noise, and it also merges stderr into stdout.
  kpy() { flatpak run --filesystem=/tmp --filesystem=home --command=python3 org.kicad.KiCad "$@" 2>&1 \
          | grep -v -i "memory leak\|gtk-\|dbind\|Adding duplicate image handler"; }
  FR_JAR=$(ls "$HOME"/.var/app/org.kicad.KiCad/data/kicad/*/3rdparty/plugins/app_freerouting_kicad-plugin/jar/freerouting-*.jar 2>/dev/null | tail -1)
fi
