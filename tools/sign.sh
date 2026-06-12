#!/usr/bin/env bash
# sign.sh — minimal wrapper over Apple's `shortcuts sign`.
#
# Signs a composed .shortcut so it can be imported. Output goes to signed/<name>
# unless a second argument is given. macOS only (shortcuts CLI is Apple's).
#
#   ./tools/sign.sh "Car Mode.shortcut"
#   ./tools/sign.sh "Car Mode.shortcut" "/tmp/out.shortcut"
#
# Then: open "signed/Car Mode.shortcut"  (one-click import; iCloud syncs it).

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "usage: $0 <input.shortcut> [output.shortcut]" >&2
  exit 2
fi

input="$1"
output="${2:-signed/$(basename "$input")}"

if ! command -v shortcuts >/dev/null 2>&1; then
  echo "error: 'shortcuts' CLI not found (macOS only)" >&2
  exit 1
fi

mkdir -p "$(dirname "$output")"
shortcuts sign --mode anyone --input "$input" --output "$output"
echo "signed -> $output"
echo "import with: open \"$output\""
