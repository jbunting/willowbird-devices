#!/usr/bin/env bash
#
# Manual push helper for willowbird-devices (issue #4).
#
# Wraps ESPHome for local/dev flashing and provisions WiFi at bootstrap over
# Improv Serial, pulling credentials from Bitwarden via rbw (issue #6).
# Credentials are NEVER baked into firmware images (enforced by the no-!secret
# lint) — they are sent to the device at bootstrap and stored in its flash.
#
# Builds are dev builds: version stays "dev" and auto_update defaults to false,
# so a manually-pushed device never self-updates from the GitHub `latest`
# release (issue #5). Mainline builds only ever come from CI.
#
# Usage:
#   scripts/push.sh flash <device> [target]     Compile + upload (USB or OTA)
#   scripts/push.sh ota <device> <target>       Upload over the network to <target>
#   scripts/push.sh bootstrap <device> [port]   First USB flash + WiFi provisioning
#   scripts/push.sh provision [port]            Provision WiFi over Improv Serial only
#   scripts/push.sh logs <device> [target]      Stream logs from a device
#
# <device> is a config basename (e.g. bluetooth-proxy) or a path to a .yaml.
# <target> is a serial port (/dev/tty.*) or a network host/IP; omit to let
# ESPHome prompt. <port> is the USB serial port (autodetected if omitted).
#
# Env:
#   WILLOWBIRD_BW_ITEM   Bitwarden item holding the WiFi fields
#                        (default: willowbird-devices)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEVICES_DIR="$REPO_ROOT/devices"
BW_ITEM="${WILLOWBIRD_BW_ITEM:-willowbird-devices}"

die() { echo "error: $*" >&2; exit 1; }

require() { command -v "$1" >/dev/null 2>&1 || die "'$1' not found on PATH"; }

usage() { sed -n '2,/^set -euo/p' "$0" | sed 's/^# \{0,1\}//; /^set -euo/d'; }

# Resolve a device argument to a config path.
resolve_config() {
  local arg="$1"
  if [ -f "$arg" ]; then echo "$arg"; return; fi
  local c
  for c in "$DEVICES_DIR/$arg.yaml" "$REPO_ROOT/prototypes/$arg.yaml"; do
    [ -f "$c" ] && { echo "$c"; return; }
  done
  die "no config found for '$arg' (looked in devices/ and prototypes/)"
}

# Pull WiFi credentials from Bitwarden and hand them to the Improv provisioner
# via the environment (never argv, so they don't show up in `ps`).
provision_wifi() {
  local port="${1:-}"
  require rbw
  require python3
  rbw unlock
  local ssid pass
  ssid="$(rbw get --field wifi_ssid "$BW_ITEM" 2>/dev/null || true)"
  pass="$(rbw get --field wifi_password "$BW_ITEM" 2>/dev/null || true)"
  [ -n "$ssid" ] || die "wifi_ssid not found in Bitwarden item '$BW_ITEM'"
  IMPROV_SSID="$ssid" IMPROV_PASSWORD="$pass" \
    python3 "$SCRIPT_DIR/improv_provision.py" ${port:+--port "$port"}
}

cmd_flash() {
  local device="${1:-}"; [ -n "$device" ] || die "usage: $0 flash <device> [target]"
  local target="${2:-}"
  require esphome
  local cfg; cfg="$(resolve_config "$device")"
  # Dev build: version=dev, auto_update=false are the config defaults.
  if [ -n "$target" ]; then
    esphome run "$cfg" --device "$target"
  else
    esphome run "$cfg"
  fi
}

cmd_ota() {
  local device="${1:-}" target="${2:-}"
  [ -n "$device" ] && [ -n "$target" ] || die "usage: $0 ota <device> <target>"
  require esphome
  local cfg; cfg="$(resolve_config "$device")"
  esphome run "$cfg" --device "$target"
}

cmd_provision() {
  provision_wifi "${1:-}"
}

cmd_bootstrap() {
  local device="${1:-}"; [ -n "$device" ] || die "usage: $0 bootstrap <device> [port]"
  local port="${2:-}"
  require esphome
  local cfg; cfg="$(resolve_config "$device")"
  # First flash must go over USB serial — a fresh device has no network.
  if [ -n "$port" ]; then
    esphome run "$cfg" --device "$port"
  else
    echo "No port given — ESPHome will prompt. Pick the USB serial device."
    esphome run "$cfg"
  fi
  # Then send WiFi over Improv so it lands in flash, not in the image.
  echo "Flash complete — provisioning WiFi over Improv Serial ..."
  provision_wifi "$port"
}

cmd_logs() {
  local device="${1:-}"; [ -n "$device" ] || die "usage: $0 logs <device> [target]"
  local target="${2:-}"
  require esphome
  local cfg; cfg="$(resolve_config "$device")"
  if [ -n "$target" ]; then
    esphome logs "$cfg" --device "$target"
  else
    esphome logs "$cfg"
  fi
}

main() {
  local sub="${1:-}"; shift || true
  case "$sub" in
    flash)     cmd_flash "$@" ;;
    ota)       cmd_ota "$@" ;;
    provision) cmd_provision "$@" ;;
    bootstrap) cmd_bootstrap "$@" ;;
    logs)      cmd_logs "$@" ;;
    ""|-h|--help|help) usage ;;
    *) die "unknown command '$sub' (try: $0 --help)" ;;
  esac
}

main "$@"
