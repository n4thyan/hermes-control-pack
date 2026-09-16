#!/usr/bin/env bash
set -euo pipefail
ZIP=${1:?usage: scripts/build_from_zip.sh /path/to/corpus.zip [output]}
OUT=${2:-build/hcp}
python -m pip install -e . --no-build-isolation
hcp build "$ZIP" --out "$OUT"
echo "Built Hermes Control Pack at $OUT"
