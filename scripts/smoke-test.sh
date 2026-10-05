#!/bin/bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$script_dir/check_primes.py" \
  --tasks 1 --concurrency 1 --limit 1000000 --timeout 120 "$@"
