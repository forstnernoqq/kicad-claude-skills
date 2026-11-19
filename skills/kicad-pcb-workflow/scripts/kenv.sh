# kenv.sh: sourced by the scripts (the caller sets S to its own directory).
# Defines the shell functions kcli (kicad-cli) and kpy (KiCad's python with pcbnew), and FR_JAR (Freerouting jar).
# Platform specifics live in the platform skills: <skills root>/kicad-env-*/env.sh. Each one defines them only on
# a machine it matches and then sets KENV. To use your own tools instead, set KCLI_BIN and KPY_BIN (and FR_JAR).
KENV=""
if [ -n "$KCLI_BIN" ] && [ -n "$KPY_BIN" ]; then
  KENV=custom
  kcli() { "$KCLI_BIN" "$@"; }
  kpy() { "$KPY_BIN" "$@"; }
else
  for _root in "$HOME/.claude/skills" "$S/.." "$S/../.." "$S/../../.."; do
    for _e in "$_root"/kicad-env-*/env.sh; do
      [ -f "$_e" ] || continue
      . "$_e"
      [ -n "$KENV" ] && break 2
    done
  done
fi
[ -n "$KENV" ] || { echo "kenv: no kicad-env-* skill matches this machine; set KCLI_BIN and KPY_BIN" >&2; exit 1; }
