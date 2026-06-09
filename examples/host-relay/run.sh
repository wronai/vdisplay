#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

_resolve_host_display() {
  local candidate=""
  if [[ -n "${DISPLAY:-}" ]] && [[ "${DISPLAY}" =~ ^:[0-9]+$ ]] && [[ "${DISPLAY#:}" -ge 10 ]]; then
    if [[ -S /tmp/.X11-unix/X0 ]]; then
      echo "note: ignoring DISPLAY=${DISPLAY}, using :0" >&2
      candidate=":0"
    fi
  fi
  if [[ -z "${candidate}" ]]; then
    candidate="${HOST_DISPLAY:-${DISPLAY:-:0}}"
  fi
  if [[ -z "${candidate}" ]]; then
    candidate=":0"
  fi
  if ! [[ -S "/tmp/.X11-unix/X${candidate#:}" ]]; then
    for fallback in :0 :1; do
      if [[ -S "/tmp/.X11-unix/X${fallback#:}" ]]; then
        echo "note: using fallback display ${fallback}" >&2
        candidate="${fallback}"
        break
      fi
    done
  fi
  printf '%s' "${candidate}"
}

export HOST_DISPLAY="$(_resolve_host_display)"
export DISPLAY="${HOST_DISPLAY}"
export XAUTHORITY="${XAUTHORITY:-${HOME}/.Xauthority}"

if ! [[ -S "/tmp/.X11-unix/X${HOST_DISPLAY#:}" ]]; then
  echo "error: X11 socket missing for DISPLAY=${HOST_DISPLAY}" >&2
  exit 1
fi

echo "using DISPLAY=${DISPLAY} XAUTHORITY=${XAUTHORITY}"

xhost +local:docker
trap 'DISPLAY="${HOST_DISPLAY}" xhost -local:docker' EXIT

docker compose up --build "$@"
