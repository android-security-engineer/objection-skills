#!/usr/bin/env bash
# objection_agent.sh — thin wrapper for AI Agents to call objection's agent CLI.
#
# Usage:
#   objection_agent.sh <package> exec '<command>'
#   objection_agent.sh <package> state
#   objection_agent.sh <package> rpc <method> '[args json array]'
#   objection_agent.sh capabilities
#
# Always emits JSON on stdout (objection's agent subcommands force JSON).
# Exit code is non-zero on connection/agent failure.
#
# Example:
#   objection_agent.sh com.example.app exec 'android hooking list classes'
#   objection_agent.sh com.example.app state
#   objection_agent.sh capabilities

set -euo pipefail

OBJECTION="${OBJECTION:-objection}"

if [[ $# -lt 1 ]]; then
  echo '{"status":"error","command":"objection_agent.sh","result":{"error":"missing arguments; see header"},"jobs_created":[],"warnings":[]}' >&2
  exit 2
fi

target="$1"; shift

case "${1:-}" in
  exec)
    shift
    if [[ $# -lt 1 ]]; then
      echo '{"status":"error","command":"exec","result":{"error":"missing command string"},"jobs_created":[],"warnings":[]}' >&2
      exit 2
    fi
    exec "$OBJECTION" -g "$target" agent exec "$@"
    ;;
  state)
    exec "$OBJECTION" -g "$target" agent state
    ;;
  rpc)
    shift
    method="${1:?missing method}"; shift
    if [[ $# -ge 1 ]]; then
      exec "$OBJECTION" -g "$target" agent rpc "$method" --args "$1"
    else
      exec "$OBJECTION" -g "$target" agent rpc "$method"
    fi
    ;;
  *)
    # No target needed for capabilities, but accept it for symmetry.
    if [[ "$target" == "capabilities" ]]; then
      exec "$OBJECTION" agent capabilities
    fi
    echo "unknown subcommand: ${1:-}" >&2
    exit 2
    ;;
esac
