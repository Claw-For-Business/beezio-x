#!/bin/sh
# Run main.py using the project venv (so requests is available).
# First time: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  echo "Creating .venv..."
  python3 -m venv .venv
fi
.venv/bin/pip install -q -r requirements.txt
exec .venv/bin/python3 main.py "$@"
