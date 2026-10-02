#!/usr/bin/env bash
# Cloud environment setup script for motion/frontend work.
# Paste into: claude.ai/code -> environment menu -> Edit -> Setup script.
# Runs before Claude starts; finishes well under the ~5 min cache limit.
# Already in the base image: node 22 + nvm, bun, uv, python 3.11, rust/cargo,
# go, docker, ffmpeg, gh, Chromium for Playwright (/opt/pw-browsers).
set -euo pipefail

BIN=/usr/local/bin

# fnm: fast Node version manager (per-project .node-version / .nvmrc)
# (fnm.vercel.app isn't on the Trusted allowlist; GitHub releases are.)
( curl -fsSL -o /tmp/fnm.zip https://github.com/Schniz/fnm/releases/latest/download/fnm-linux.zip \
  && python3 -m zipfile -e /tmp/fnm.zip $BIN && chmod +x $BIN/fnm \
  && echo 'eval "$(fnm env --use-on-cd --shell bash)"' >> /etc/bash.bashrc ) &

# cloudflared: Cloudflare CLI. Note: quick tunnels (inbound access to the VM) are
# blocked by Claude Code's auto-mode safety check unless you allow them yourself.
( curl -fsSL -o $BIN/cloudflared \
    https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
  && chmod +x $BIN/cloudflared ) &

# Global JS tooling: deploy previews, render pipelines, Playwright matching the
# preinstalled Chromium build (1.56.x -> chromium-1194, no browser download).
( PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm install -g --no-fund --no-audit \
    wrangler hyperframes playwright@1.56.1 serve ) &

# Python tools via uv (isolated, cached in the snapshot)
( uv tool install ruff && uv tool install httpie ) &

wait
echo "setup done: $(fnm --version) | $(cloudflared --version | head -1) | wrangler $(wrangler --version 2>/dev/null | tail -1)"
