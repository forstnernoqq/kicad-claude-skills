#!/bin/sh
# install.sh [--copy] [--force]
# Puts every skill from skills/ into ~/.claude/skills/<name>.
#   default : symbolic links on Linux/macOS (a git pull updates the skills); copies on Windows (Git Bash)
#   --copy  : always copy
#   --force : replace existing skills with the same name (the old ones are moved to <name>.old-<date>)
set -e
REPO=$(cd "$(dirname "$0")" && pwd)
DEST="$HOME/.claude/skills"
MODE=link; FORCE=no
case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) MODE=copy;; esac
for a in "$@"; do
  case "$a" in --copy) MODE=copy;; --force) FORCE=yes;; *) echo "unknown option $a"; exit 1;; esac
done
mkdir -p "$DEST"
for src in "$REPO"/skills/*/; do
  name=$(basename "$src"); dst="$DEST/$name"
  if [ -e "$dst" ] || [ -L "$dst" ]; then
    if [ -L "$dst" ] && [ "$(readlink "$dst")" = "${src%/}" ]; then echo "ok      $name (already linked)"; continue; fi
    if [ "$FORCE" = no ]; then echo "skip    $name (exists; use --force to replace)"; continue; fi
    mv "$dst" "$dst.old-$(date +%Y%m%d%H%M%S)"
  fi
  if [ "$MODE" = link ]; then ln -s "${src%/}" "$dst"; echo "linked  $name"; else cp -r "${src%/}" "$dst"; echo "copied  $name"; fi
done
chmod +x "$DEST"/*/scripts/kcli "$DEST"/*/scripts/kpy "$DEST"/*/scripts/kenv_info "$DEST"/*/scripts/*.sh 2>/dev/null || true
echo "check:  $DEST/kicad-pcb-workflow/scripts/kenv_info"
