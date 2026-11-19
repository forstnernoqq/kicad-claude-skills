#!/bin/sh
# run.sh script.py args...  -- KiCad python (pcbnew) via the platform layer (kenv.sh / kicad-env-* skill)
exec "$(cd "$(dirname "$0")" && pwd)/kpy" "$@"
