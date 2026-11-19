# Platform: Windows, KiCad from the official installer, scripts run in Git Bash (Claude Code's shell on Windows).
# NOT VERIFIED YET: check with kicad-pcb-workflow/scripts/kenv_info on the first Windows session and fix the paths here.
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    _kb=""
    for _d in "/c/Program Files/KiCad"/*/bin; do [ -x "$_d/kicad-cli.exe" ] && _kb="$_d"; done   # newest version wins
    if [ -n "$_kb" ]; then
      KENV=windows
      KICAD_BIN="$_kb"
      kcli() { "$KICAD_BIN/kicad-cli.exe" "$@"; }
      kpy() { "$KICAD_BIN/python.exe" "$@"; }
      _docs=$(cygpath -u "$USERPROFILE" 2>/dev/null)/Documents
      FR_JAR=$(ls "$_docs"/KiCad/*/3rdparty/plugins/app_freerouting_kicad-plugin/jar/freerouting-*.jar 2>/dev/null | tail -1)
    fi;;
esac
