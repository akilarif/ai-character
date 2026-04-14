#!/usr/bin/env bash
set -euo pipefail

uv export --format requirements-txt --no-hashes --output-file requirements.txt
echo "Updated requirements.txt from pyproject.toml/uv.lock"
