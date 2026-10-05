#!/usr/bin/env bash
set -euo pipefail

# Submit bounded prime workloads and verify every returned task completes.
# Workers run during submission, so this measures end-to-end HTTP execution,
# rather than the drain time of a prefilled queue.
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$script_dir/scripts/check_primes.py" \
  --tasks "${TASKS:-100}" \
  --concurrency "${CONCURRENCY:-4}" \
  --limit "${LIMIT:-1000000}" \
  --timeout "${TIMEOUT:-120}" \
  "$@"
