#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# RVG Gateway — update script (self-hosted Linux edition)
# Pulls the latest code from git (if this is a git checkout), refreshes Python
# dependencies, creates a safety backup first, then restarts the service.
#
# Usage: sudo rvg update     (or: sudo bash update.sh)
# ══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

SERVICE_NAME="rvg"
APP_DIR="${RVG_APP_DIR:-/opt/rvg}"
CONF_FILE="/etc/rvg.conf"
DATA_DIR="${DATA_DIR:-/var/lib/rvg}"

c_green='\033[0;32m'; c_blue='\033[0;34m'; c_yellow='\033[1;33m'; c_red='\033[0;31m'; c_off='\033[0m'
ok()   { echo -e "${c_green}[ OK ]${c_off} $*"; }
info() { echo -e "${c_blue}[INFO]${c_off} $*"; }
warn() { echo -e "${c_yellow}[WARN]${c_off} $*"; }
die()  { echo -e "${c_red}[FAIL]${c_off} $*" >&2; exit 1; }

[[ "$(id -u)" -eq 0 ]] || die "Run as root: sudo rvg update"
[[ -f "$CONF_FILE" ]] && . "$CONF_FILE"

echo ""
info "RVG Gateway update starting..."

# ── 1. Safety backup ─────────────────────────────────────────────────────────
mkdir -p "$DATA_DIR/backups"
ts="$(date +%Y%m%d-%H%M%S)"
args=()
for f in rvg_state.json .rvg_secret update_history.json .bot_tcp_proxy_token; do
  [[ -f "$DATA_DIR/$f" ]] && args+=( -C "$DATA_DIR" "$f" )
done
if ((${#args[@]})); then
  tar czf "$DATA_DIR/backups/pre-update-$ts.tar.gz" "${args[@]}" 2>/dev/null \
    && ok "Safety backup created: pre-update-$ts.tar.gz"
fi

# ── 2. Pull latest code ──────────────────────────────────────────────────────
cd "$APP_DIR"
if [[ -d .git ]]; then
  info "Pulling latest code from git..."
  git fetch --all -q 2>/dev/null || warn "git fetch failed (offline?)"
  branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo main)"
  git reset --hard "origin/${branch}" -q || git pull -q || warn "git pull failed — using existing files"
else
  warn "$APP_DIR is not a git checkout — skipping code pull."
  warn "Download a new release and re-run install.sh --force to update files manually."
fi

# ── 3. Refresh dependencies ──────────────────────────────────────────────────
if [[ -f requirements.txt && -x venv/bin/pip ]]; then
  info "Refreshing Python dependencies..."
  venv/bin/pip install -q -r requirements.txt && ok "Dependencies up to date"
else
  warn "venv/requirements.txt missing — run install.sh --force instead."
fi

SVC_USER="$(grep '^User=' /etc/systemd/system/${SERVICE_NAME}.service 2>/dev/null | cut -d= -f2)"
[[ -n "$SVC_USER" ]] && chown -R "$SVC_USER:$SVC_USER" "$APP_DIR" 2>/dev/null || true

# ── 4. Restart ───────────────────────────────────────────────────────────────
systemctl daemon-reload 2>/dev/null || true
systemctl restart "${SERVICE_NAME}.service"
sleep 2
systemctl is-active --quiet "${SERVICE_NAME}.service" \
  && ok "Update complete — service is running." \
  || { warn "Service not healthy yet — check logs:"; echo "       journalctl -u ${SERVICE_NAME} -n 50"; }
echo ""
