#!/usr/bin/env bash
# Certwatch uninstall. By default it preserves configuration, state and logs.
set -euo pipefail
INSTALL_DIR="${CERTWATCH_INSTALL_DIR:-/opt/certwatch}"
CONFIG_DIR="${CERTWATCH_CONFIG_DIR:-/etc/certwatch}"
BIN_DIR="${CERTWATCH_BIN_DIR:-/usr/local/bin}"
PURGE=false; YES=false
for arg in "$@"; do case "$arg" in --purge-data) PURGE=true;; --yes) YES=true;; *) printf 'usage: %s [--yes] [--purge-data]\n' "$0" >&2; exit 64;; esac; done
action='remove binaries and installation only'; "$PURGE" && action='remove binaries, installation, configuration, state and logs'
[[ "$YES" == true ]] || { printf 'About to %s. Re-run with --yes to continue.\n' "$action"; exit 0; }
[[ "$EUID" -eq 0 ]] || { printf 'certwatch uninstall: run as root\n' >&2; exit 1; }
systemctl disable --now certwatch.timer certwatch-agent.service 2>/dev/null || true
rm -f "$BIN_DIR/certwatch" "$BIN_DIR/certwatch-agent"
rm -rf "$INSTALL_DIR"
if "$PURGE"; then rm -rf "$CONFIG_DIR" /var/lib/certwatch /var/lib/certwatch-agent /var/log/certwatch; else printf 'Preserved %s and runtime state/logs.\n' "$CONFIG_DIR"; fi
printf 'Certwatch uninstall completed.\n'
