#!/bin/sh
# py.sh script.py ARGS... : KiCad python via the platform layer (kept for the chain/pipe scripts)
exec "$(cd "$(dirname "$0")" && pwd)/../kpy" "$@"
