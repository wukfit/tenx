#!/usr/bin/env bash
# TenX deterministic phase gate (Claude Code, Claude desktop agent mode, Codex).
# Thin wrapper around tenx_gate.py. Exit 2 = deny (stderr shown to the model).
# Any failure to run the verifier is itself a denial: an unverified phase entry
# must never be allowed just because the gate could not execute.
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
gate="$here/tenx_gate.py"
payload="$(cat)"

fail_closed() {
  printf 'TenX gate: %s. Refusing to allow an unverified phase entry. A denial is an instruction to run the owning phase, NEVER to create the missing file yourself.\n' "$1" >&2
  exit 2
}

command -v python3 >/dev/null 2>&1 || fail_closed "python3 not found, so records could not be verified"
[ -f "$gate" ] || fail_closed "verifier missing at $gate"

python3 "$gate" "$payload"
status=$?

case "$status" in
  0|2) exit "$status" ;;
  *) fail_closed "verifier exited unexpectedly with status $status" ;;
esac
