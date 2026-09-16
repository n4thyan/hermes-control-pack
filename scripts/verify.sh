#!/usr/bin/env bash
set -euo pipefail
python -m compileall -q src/hermes_control_pack
python -m unittest discover -s tests -v
hcp --version
