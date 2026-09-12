#!/bin/sh
# Hooks run with cwd=workspace; locate the shared script via our own (runtime-resolved) path.
DIR=$(dirname "$0")
case "$DIR" in
  /*) ;;
  *) DIR="$(pwd)/$DIR";;
esac
exec python3 "$DIR/title-status.py" '✅' || exit 0
