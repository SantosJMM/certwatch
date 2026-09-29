#!/usr/bin/env bash
# Certwatch installer. Inspect this script before running it with sudo.
set -euo pipefail

INSTALL_DIR="${CERTWATCH_INSTALL_DIR:-/opt/certwatch}"
CONFIG_DIR="${CERTWATCH_CONFIG_DIR:-/etc/certwatch}"
BIN_DIR="${CERTWATCH_BIN_DIR:-/usr/local/bin}"
VERSION="${CERTWATCH_VERSION:-v0.1.0}"
REPOSITORY="${CERTWATCH_REPOSITORY:-SantosJMM/certwatch}"
SOURCE_URL="${CERTWATCH_SOURCE_URL:-}"
DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

fail() { printf 'certwatch installer: %s\n' "$*" >&2; exit 1; }
run() { if "$DRY_RUN"; then printf '+ '; printf '%q ' "$@"; printf '\n'; else "$@"; fi; }
[[ "${EUID}" -eq 0 || "$DRY_RUN" == true ]] || fail 'run as root (for example: sudo bash install.sh)'
command -v uv >/dev/null || fail 'uv is required; install uv first from https://docs.astral.sh/uv/'
command -v tar >/dev/null || fail 'tar is required'
if [[ -z "$SOURCE_URL" ]]; then
  [[ "$REPOSITORY" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] || fail 'set CERTWATCH_REPOSITORY=OWNER/REPOSITORY or CERTWATCH_SOURCE_URL=https://...tar.gz'
  SOURCE_URL="https://github.com/${REPOSITORY}/archive/refs/tags/${VERSION}.tar.gz"
fi
[[ "$SOURCE_URL" =~ ^https:// ]] || fail 'CERTWATCH_SOURCE_URL must use HTTPS'
if ! "$DRY_RUN"; then command -v curl >/dev/null || command -v wget >/dev/null || fail 'curl or wget is required'; fi
printf 'Certwatch source: %s\nVersion: %s\nInstall dir: %s\n' "$SOURCE_URL" "$VERSION" "$INSTALL_DIR"
"$DRY_RUN" && exit 0
workdir=$(mktemp -d); trap 'rm -rf "$workdir"' EXIT
archive="$workdir/source.tar.gz"
if command -v curl >/dev/null; then curl -fsSL --proto '=https' --tlsv1.2 "$SOURCE_URL" -o "$archive"; else wget -q --https-only "$SOURCE_URL" -O "$archive"; fi
tar -xzf "$archive" -C "$workdir"
source_dir=$(find "$workdir" -mindepth 1 -maxdepth 1 -type d -name 'certwatch-*' | head -n1)
[[ -n "$source_dir" && -f "$source_dir/pyproject.toml" ]] || fail 'archive does not contain a Certwatch Python project'
run install -d -m 0755 "$INSTALL_DIR"
run uv venv "$INSTALL_DIR/venv" --python python3
run uv pip install --python "$INSTALL_DIR/venv/bin/python" "$source_dir"
run install -d -m 0750 "$CONFIG_DIR"
[[ -f "$CONFIG_DIR/certwatch.env" ]] || run install -m 0600 "$source_dir/.env.example" "$CONFIG_DIR/certwatch.env"
run ln -sfn "$INSTALL_DIR/venv/bin/certwatch" "$BIN_DIR/certwatch"
run ln -sfn "$INSTALL_DIR/venv/bin/certwatch-agent" "$BIN_DIR/certwatch-agent"
printf 'Installed. Edit %s/certwatch.env before enabling any service.\n' "$CONFIG_DIR"
