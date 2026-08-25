#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# RVG Gateway — Self-Hosted Linux Installer
#
# Supports:
#   • Debian 11/12+, Ubuntu 20.04/22.04/24.04+ and every apt-based distro
#   • AlmaLinux 8/9/10, Rocky Linux, RHEL, CentOS Stream, Fedora (dnf/yum)
#
# What it does:
#   1. Installs system dependencies (Python 3.10+, git, build tools)
#   2. Creates a dedicated 'rvg' system user
#   3. Copies the application to /opt/rvg
#   4. Creates a virtualenv and installs Python dependencies
#   5. Sets up persistent data directory at /var/lib/rvg
#   6. Installs and starts a systemd service (auto-start on boot)
#   7. Opens the panel port in ufw / firewalld (when present)
#   8. Prints the URL of the web setup wizard
#
# Usage:
#   sudo bash install.sh [options]
# Options:
#   --port N          Panel port            (default: 8080)
#   --host HOST       Public host/domain    (default: server IP, can be set later in web UI)
#   --no-firewall     Do not touch firewall rules
#   --force           Overwrite existing installation files
# ══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
APP_PORT=8080
PUBLIC_HOST=""
NO_FIREWALL=0
FORCE=0
APP_DIR="/opt/rvg"
DATA_DIR="/var/lib/rvg"
SERVICE_NAME="rvg"
SERVICE_USER="rvg"

c_green='\033[0;32m'; c_blue='\033[0;34m'; c_yellow='\033[1;33m'; c_red='\033[0;31m'; c_off='\033[0m'
info()  { echo -e "${c_blue}[INFO]${c_off} $*"; }
ok()    { echo -e "${c_green}[ OK ]${c_off} $*"; }
warn()  { echo -e "${c_yellow}[WARN]${c_off} $*"; }
die()   { echo -e "${c_red}[FAIL]${c_off} $*" >&2; exit 1; }

# ── Parse args ────────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --port)       APP_PORT="$2"; shift 2 ;;
    --host)       PUBLIC_HOST="$2"; shift 2 ;;
    --no-firewall) NO_FIREWALL=1; shift ;;
    --force)      FORCE=1; shift ;;
    -h|--help)    grep '^#' "$0" | sed 's/^# \{0,1\}//' | head -40; exit 0 ;;
    *) die "Unknown option: $1 (see --help)" ;;
  esac
done

[[ "$(id -u)" -eq 0 ]] || die "Please run as root: sudo bash install.sh"

echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║        RVG Gateway · Self-Hosted         ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""

# ── Detect package manager / distro ───────────────────────────────────────────
PKG=""
if command -v apt-get >/dev/null 2>&1; then PKG="apt";
elif command -v dnf >/dev/null 2>&1; then PKG="dnf";
elif command -v yum >/dev/null 2>&1; then PKG="yum";
else die "Unsupported distribution: no apt-get/dnf/yum found."
fi

. /etc/os-release 2>/dev/null || true
DISTRO="${ID:-unknown}"
info "Detected: ${PRETTY_NAME:-$DISTRO} (pkg: $PKG)"

pkg_install() {
  case "$PKG" in
    apt) DEBIAN_FRONTEND=noninteractive apt-get install -y "$@" >/dev/null ;;
    dnf) dnf install -y "$@" >/dev/null ;;
    yum) yum install -y "$@" >/dev/null ;;
  esac
}

pkg_refresh() {
  case "$PKG" in
    apt) apt-get update -qq >/dev/null ;;
    dnf) dnf makecache -q >/dev/null 2>&1 || true ;;
    yum) yum makecache -q  >/dev/null 2>&1 || true ;;
  esac
}

# ── 1. System dependencies ────────────────────────────────────────────────────
info "Installing base packages..."
pkg_refresh
case "$PKG" in
  apt) pkg_install ca-certificates curl git python3 python3-venv python3-pip \
                 build-essential libssl-dev zlib1g-dev || true ;;
  dnf|yum) pkg_install ca-certificates curl git python3 python3-pip \
                  gcc make openssl-devel zlib-devel libffi-devel || true ;;
esac
ok "Base packages installed"

# ── 2. Ensure a modern Python (>= 3.10) ───────────────────────────────────────
PY=""
for cand in python3.13 python3.12 python3.11 python3; do
  if command -v "$cand" >/dev/null 2>&1; then
    if "$cand" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null; then
      PY="$(command -v "$cand")"; break
    fi
  fi
done

if [[ -z "$PY" ]]; then
  warn "Python >= 3.10 not found — trying versioned packages..."
  case "$PKG" in
    apt)
      pkg_install software-properties-common || true
      add-apt-repository -y ppa:deadsnakes/ppa >/dev/null 2>&1 || true
      pkg_refresh
      pkg_install python3.11 python3.11-venv || true
      command -v python3.11 >/dev/null 2>&1 && PY="$(command -v python3.11)"
      ;;
    dnf|yum)
      pkg_install python3.11 python3.11-pip || true
      command -v python3.11 >/dev/null 2>&1 && PY="$(command -v python3.11)"
      if [[ -z "$PY" ]]; then
        pkg_install python3.12 python3.12-pip || true
        command -v python3.12 >/dev/null 2>&1 && PY="$(command -v python3.12)"
      fi
      ;;
  esac
fi

[[ -n "$PY" ]] || die "Python >= 3.10 is required but could not be installed automatically.
       Install it manually (e.g. 'dnf install python3.11' or from python.org) and re-run."
ok "Using Python: $($PY --version 2>&1) ($PY)"

# venv module check
if ! "$PY" -m venv --help >/dev/null 2>&1; then
  info "Installing python venv support..."
  PY_MINOR="$($PY -c 'import sys; print(sys.version_info.minor)')"
  case "$PKG" in
    apt)
      pkg_install python3-venv || pkg_install "python3.${PY_MINOR}-venv" || true
      ;;
    dnf|yum)
      pkg_install python3-pip || true
      ;;
  esac
fi

# ── 3. Dedicated system user ──────────────────────────────────────────────────
if id "$SERVICE_USER" &>/dev/null; then
  ok "System user '$SERVICE_USER' already exists"
else
  useradd --system --home-dir "$APP_DIR" --shell /usr/sbin/nologin "$SERVICE_USER" 2>/dev/null \
    || useradd --system --home-dir "$APP_DIR" --shell /sbin/nologin "$SERVICE_USER"
  ok "Created system user '$SERVICE_USER'"
fi

# ── 4. Install application files ──────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -f "$SCRIPT_DIR/main.py" ]]; then
  die "main.py not found next to install.sh — run this script from the extracted repository folder."
fi

if [[ "$(realpath "$SCRIPT_DIR")" == "$(realpath "$APP_DIR")" ]]; then
  info "Running from installation directory ($APP_DIR) — skipping file copy."
else
  mkdir -p "$APP_DIR"
  cp -r "$SCRIPT_DIR"/. "$APP_DIR"/
  rm -rf "$APP_DIR/venv" "$APP_DIR/data" "$APP_DIR/.git"
  ok "Application copied to $APP_DIR"
fi

# ── 5. Python virtualenv + dependencies ───────────────────────────────────────
info "Creating virtualenv and installing dependencies (this may take a minute)..."
"$PY" -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --upgrade pip setuptools wheel >/dev/null
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt" >/dev/null
ok "Python dependencies installed"

# ── 6. Data directory ────────────────────────────────────────────────────────
mkdir -p "$DATA_DIR/backups"
chown -R "$SERVICE_USER:$SERVICE_USER" "$DATA_DIR" "$APP_DIR"
chmod 750 "$DATA_DIR"
ok "Persistent data directory ready: $DATA_DIR"

# ── 7. Config file + systemd service ─────────────────────────────────────────
info "Installing configuration and systemd service..."
cat > /etc/rvg.conf <<EOF
# RVG Gateway runtime configuration (managed by 'rvg' CLI)
PORT=$APP_PORT
DATA_DIR=$DATA_DIR
EOF
[[ -n "$PUBLIC_HOST" ]] && echo "RVG_PUBLIC_HOST=$PUBLIC_HOST" >> /etc/rvg.conf
chmod 640 /etc/rvg.conf
chown root:$SERVICE_USER /etc/rvg.conf

install -m 755 "$APP_DIR/bin/rvg" /usr/local/bin/rvg

sed -e "s|^Environment=DATA_DIR=.*|Environment=DATA_DIR=$DATA_DIR|" \
    "$APP_DIR/deploy/rvg.service" > /etc/systemd/system/${SERVICE_NAME}.service
systemctl daemon-reload
systemctl enable ${SERVICE_NAME}.service >/dev/null 2>&1
ok "Service '$SERVICE_NAME' installed and enabled (starts on boot)"

# ── 8. Firewall ──────────────────────────────────────────────────────────────
if [[ "$NO_FIREWALL" != "1" ]]; then
  opened=""
  if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -qi active; then
    ufw allow "${APP_PORT}/tcp" comment 'RVG Gateway' >/dev/null 2>&1 && opened="ufw:${APP_PORT}/tcp"
  elif command -v firewall-cmd >/dev/null 2>&1 && firewall-cmd --state >/dev/null 2>&1; then
    firewall-cmd --permanent --add-port="${APP_PORT}/tcp" >/dev/null 2>&1
    # MTProto instances use ports in this range by default
    firewall-cmd --permanent --add-port=8500-8600/tcp >/dev/null 2>&1
    firewall-cmd --reload >/dev/null 2>&1
    opened="firewalld:${APP_PORT}/tcp + mtproto 8500-8600/tcp"
  elif command -v iptables >/dev/null 2>&1; then
    iptables -C INPUT -p tcp --dport "$APP_PORT" -j ACCEPT 2>/dev/null || \
      iptables -I INPUT -p tcp --dport "$APP_PORT" -j ACCEPT 2>/dev/null && opened="iptables:${APP_PORT}/tcp (not persistent)"
  fi
  [[ -n "$opened" ]] && ok "Firewall rule added: $opened" || warn "No active firewall detected — make sure port ${APP_PORT} is reachable."
else
  warn "Skipping firewall configuration (--no-firewall)"
fi

# Also open MTProto range on ufw for proxy links
if [[ "$NO_FIREWALL" != "1" ]] && command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -qi active; then
  ufw allow 8500:8600/tcp comment 'RVG MTProto' >/dev/null 2>&1 || true
fi

# ── 9. Start service ─────────────────────────────────────────────────────────
info "Starting RVG Gateway service..."
systemctl restart ${SERVICE_NAME}.service
sleep 2
if systemctl is-active --quiet ${SERVICE_NAME}.service; then
  ok "Service is running"
else
  warn "Service did not report healthy yet — check: journalctl -u ${SERVICE_NAME} -f"
fi

# ── Detect primary IP for final message ──────────────────────────────────────
SERVER_IP=$(ip route get 1.1.1.1 2>/dev/null | awk '{print $NF; exit}') || SERVER_IP=""
[[ -z "$SERVER_IP" ]] && SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
[[ -z "$SERVER_IP" ]] && SERVER_IP="<server-ip>"
DISPLAY_HOST="${PUBLIC_HOST:-$SERVER_IP}"

echo ""
echo "  ══════════════════════════════════════════════════════════════"
echo -e "  ${c_green}✔ Installation complete!${c_off}"
echo ""
echo "   ➜ Open the setup wizard:"
echo -e "     ${c_blue}http://${DISPLAY_HOST}:${APP_PORT}/setup${c_off}"
echo ""
echo "   Service management (CLI):"
echo "     rvg status | rvg restart | rvg logs -f | rvg backup create"
echo ""
echo "   systemd equivalent:"
echo "     systemctl status ${SERVICE_NAME}  ·  journalctl -u ${SERVICE_NAME} -f"
echo "  ══════════════════════════════════════════════════════════════"
echo ""
