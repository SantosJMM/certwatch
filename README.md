# Certwatch

A dependency-light, dynamic Certbot certificate monitor with a deliberately narrow, optional Telegram command boundary. It discovers every lineage beneath `CERTBOT_LIVE_DIR`; it does not hard-code domains.

## Quick start

```bash
uv sync --group dev
cp .env.example certwatch.env
# set CERTBOT_LIVE_DIR to a test directory or a readable Certbot live directory
CERTWATCH_CONFIG_PATH=$PWD/certwatch.env uv run certwatch --dry-run
uv run pytest
```

## What is included

| Area | Behaviour |
|---|---|
| Discovery | Follows `fullchain.pem` links; reports lineage, SANs, issuer, expiry, days, file state and renewal config. |
| Filters | `CERT_INCLUDE` and `CERT_EXCLUDE` accept comma-separated glob patterns. |
| Read-only helper | The agent calls a fixed argv: `sudo -n <helper> read certs`. The helper accepts exactly that pair and runs only `certwatch --dry-run`. |
| Secrets | `.env.example` contains placeholders only; `.gitignore` excludes real dotenv files and logs. |

## Install (Linux/systemd template)

These commands are intentionally explicit; review paths and service-account names before use.

```bash
uv build
sudo install -m 0755 .venv/bin/certwatch /usr/local/bin/certwatch
sudo install -m 0755 .venv/bin/certwatch-agent /usr/local/bin/certwatch-agent
sudo install -d -m 0750 /etc/certwatch /var/lib/certwatch /var/lib/certwatch-agent
sudo install -m 0640 -o root -g certwatch-agent certwatch.env /etc/certwatch/certwatch.env
sudo install -m 0750 -o root -g root deploy/libexec/certwatch-action /usr/local/libexec/certwatch-action
sudo install -m 0440 -o root -g root deploy/sudoers/certwatch-agent /etc/sudoers.d/certwatch-agent
sudo install -m 0644 deploy/systemd/certwatch.service deploy/systemd/certwatch.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now certwatch.timer
```

## Uninstall

```bash
sudo systemctl disable --now certwatch.timer
sudo rm -f /etc/systemd/system/certwatch.service /etc/systemd/system/certwatch.timer
sudo rm -f /etc/sudoers.d/certwatch-agent /usr/local/libexec/certwatch-action /usr/local/bin/certwatch /usr/local/bin/certwatch-agent
sudo systemctl daemon-reload
# Keep /etc/certwatch and /var/lib/certwatch until configuration and audit retention are reviewed.
```

## Security model

The optional command-agent primitives must run as a non-root account. This public extraction deliberately ships no polling systemd unit: review and implement your organisation's Telegram operation policy before exposing remote control. The public helper template exposes only `read certs`; it rejects every other verb or argument count. Production deployments may add renewal/restart verbs only with separate allowlist entries and helper-side validation. Never source dotenv files, expose a webhook, or grant unrestricted `sudo`.

## Development

```bash
uv sync --group dev
uv run pytest
uv run python -m compileall -q src
```

## License

Apache-2.0. This is an explicit project assumption for the extracted public code; confirm organisational ownership before publishing.

## Remote installer

Prerequisites: Linux, `bash`, `python3`, `uv`, `tar`, and either `curl` or `wget`. Read the installer before using sudo. The planned repository is `https://github.com/SantosJMM/certwatch`. Remote installation works only after that repository and the requested tag (for example `v0.1.0`) exist.

```bash
# Inspect first (recommended)
curl -fsSL https://raw.githubusercontent.com/SantosJMM/certwatch/main/install.sh -o install.sh
less install.sh
sudo CERTWATCH_REPOSITORY=SantosJMM/certwatch CERTWATCH_VERSION=v0.1.0 bash install.sh

# Pipe form, only after inspection. The installer downloads the source archive to a temporary file; it never pipes source into a shell.
curl -fsSL https://raw.githubusercontent.com/SantosJMM/certwatch/main/install.sh | sudo env CERTWATCH_REPOSITORY=SantosJMM/certwatch CERTWATCH_VERSION=v0.1.0 bash

# wget equivalent
wget -qO- https://raw.githubusercontent.com/SantosJMM/certwatch/main/install.sh | sudo env CERTWATCH_REPOSITORY=SantosJMM/certwatch CERTWATCH_VERSION=v0.1.0 bash
```

Alternatively set `CERTWATCH_SOURCE_URL=https://host.example/certwatch-v0.1.0.tar.gz`; it must be HTTPS. `CERTWATCH_INSTALL_DIR`, `CERTWATCH_CONFIG_DIR`, and `CERTWATCH_BIN_DIR` are optional overrides. Validate planning without downloading with:

```bash
CERTWATCH_REPOSITORY=SantosJMM/certwatch ./install.sh --dry-run
```

Uninstall is confirmation-safe and preserves configuration/state/logs by default:

```bash
curl -fsSL https://raw.githubusercontent.com/SantosJMM/certwatch/main/uninstall.sh -o uninstall.sh
less uninstall.sh
sudo bash uninstall.sh --yes
# Explicitly destructive, only if retention is no longer required:
sudo bash uninstall.sh --yes --purge-data
```

## Diagnostic privacy

Read-only helper failures report only the bounded stage and exit status. Helper stderr is intentionally not relayed to Telegram because it may contain local paths or provider output.

### systemd privilege note

The public repository intentionally does not ship a `certwatch-agent.service` template. The agent's narrow `sudo -n` helper requires the service process to retain the ability to acquire the explicitly allowlisted root privilege.

On the production host, isolated `systemd-run` tests showed that `PrivateDevices=true`, `ProtectKernelTunables=true`, and `ProtectKernelModules=true` each caused the non-root service process to run with kernel `NoNewPrivs: 1`, even when the unit explicitly set `NoNewPrivileges=false`. That prevents `sudo` from elevating to the allowlisted helper. `PrivateTmp=true`, `ProtectHome=true`, `ProtectSystem=strict`, and `ProtectControlGroups=true` did not set `NoNewPrivs` in the same tests.

For deployments that use the helper, keep `NoNewPrivileges=false` and do not enable hardening directives that implicitly force `no_new_privileges` without testing the effective process state. Verify after deployment with:

```bash
PID=$(systemctl show -p MainPID --value certwatch-agent)
grep NoNewPrivs /proc/$PID/status
```

The expected value is `NoNewPrivs: 0`. Keep the service account out of the general `sudo` group and grant only the explicit commands required through `/etc/sudoers.d/certwatch-agent`.
