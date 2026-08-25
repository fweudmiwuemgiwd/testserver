#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# RVG Gateway — uninstall script (self-hosted Linux edition)
#
# Stops and disables the service, removes the app directory, systemd unit,
# CLI binary and config. Data/backups are KEPT unless you answer "delete".
#
# Usage: sudo rvg uninstall   (or: sudo bash uninstall.sh)
# ══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

SERVICE_NAME="rvg"
APP_DIR="${RVG_APP_DIR:-/opt/rvg}"
DATA_DIR="${DATA_DIR:-/var/lib/rvg}"
CONF_FILE="/etc/rvg.conf"
SVC_USER="rvg"

c_yellow='\033[1;33m'; c_red='\033[0;31m'; c_green='\033[0;32m'; c_off='\033[0m'
ok()   { echo -e "${c_green}[ OK ]${c_off} $*"; }
warn() { echo -e "${c_yellow}[WARN]${c_off} $*"; }
die()  { echo -e "${c_red}[FAIL]${c_off} $*" >&2; exit 1; }

[[ "$(id -u)" -eq 0 ]] || die "Run as root: sudo rvg uninstall"
[[ -f "$CONF_FILE" ]] && . "$CONF_FILE"

echo ""
echo -e "${c_red}This will remove RVG Gateway from this machine.${c_off}"
read -r -p "Type YES to continue: " ans
[[ "$ans" == "YES" ]] || { echo "Aborted."; exit 0; }

systemctl stop "${SERVICE_NAME}.service" 2>/dev/null || true
systemctl disable "${SERVICE_NAME}.service" 2>/dev/null || true
rm -f /etc/systemd/system/${SERVICE_NAME}.service
rm -rf "/etc/systemd/system/${SERVICE_NAME}.service.d"
rm -f /usr/local/bin/rvg
rm -f "$CONF_FILE"
rm -rf "$APP_DIR"
systemctl daemon-reload
ok "Service, app files and CLI removed."

read -r -p "Delete data, links and backups at $DATA_DIR too? [y/N]: " del
if [[ "$del" =~ ^[Yy]$ ]]; then
  rm -rf "$DATA_DIR"
  ok "Data directory deleted."
else
  warn "Kept $DATA_DIR (contains your state + backups)."
fi

id "$SVC_USER" &>/dev/null && { userdel "$SVC_USER" 2>/dev/null || true; ok "System user '$SVC_USER' removed."; }
echo ""
echo "RVG Gateway uninstalled."
