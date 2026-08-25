# RVG Gateway — Complete Usage Guide (Self-Hosted Linux)

This guide covers day-2 operations: service management, configuration, backups,
stopping the application, disabling logs, updating and troubleshooting.

> Install first? See the [README](../README.md) — `sudo bash install.sh`, then open
> `http://<server-ip>:8080/setup`.

---

## Table of Contents

1. [First-run Setup Wizard](#1-first-run-setup-wizard)
2. [Service Management](#2-service-management)
3. [Configuration](#3-configuration)
4. [Backup Management](#4-backup-management)
5. [Stopping / Shutting Down](#5-stopping--shutting-down)
6. [Disabling All Logs](#6-disabling-all-logs)
7. [Updating](#7-updating)
8. [Uninstalling](#8-uninstalling)
9. [Firewall & Ports](#9-firewall--ports)
10. [TLS / Reverse Proxy (recommended)](#10-tls--reverse-proxy-recommended)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. First-run Setup Wizard

Until the wizard is completed the panel is **locked**: all pages redirect to
`/setup` and login APIs return `SETUP_REQUIRED`. There is no default password.

The wizard collects:

| Field | Meaning | Default |
|---|---|---|
| Admin password | Dashboard login (min 6 chars, strength meter shown) | — |
| Public host | Domain or IP used inside generated proxy links | server IP |
| Config port | Port advertised in links — auto-synced to the panel port (internal TLS) or your terminator's port (external TLS) | panel port |
| Panel port | HTTPS port of this app (**requires service restart**) | 8080 |
| Phone-home | Optional announcements/support contact — off = fully private | off |

Everything can be changed later from the dashboard or CLI.

---

## 2. Service Management

The app runs as a systemd unit: `rvg.service`.

```bash
sudo rvg status                 # human-friendly status
sudo rvg start | stop | restart
sudo rvg logs                   # last 100 lines
sudo rvg logs -f                # follow
sudo rvg logs -f 500            # follow, starting with last 500 lines
sudo rvg info                   # paths, version, state summary
```

Native systemd equivalents:

```bash
systemctl status rvg
systemctl cat rvg               # view the unit
journalctl -u rvg -f            # raw logs
```

The service:

- starts on boot (`WantedBy=multi-user.target`)
- restarts automatically on crash (`Restart=always`, 3s delay)
- runs as unprivileged user `rvg`
- keeps data in `/var/lib/rvg` and code in `/opt/rvg`

---

## 3. Configuration

Two layers:

1. **`/etc/rvg.conf`** — environment for the service (`PORT`, `DATA_DIR`,
   `RVG_PUBLIC_HOST`, ...). Managed by the CLI; survives updates.
2. **State file** `/var/lib/rvg/rvg_state.json` — links, subs, nodes, admin
   hash, wizard choices. Edited via dashboard/API/CLI, never by hand while running.

Common tasks:

```bash
sudo rvg port 9000              # change panel port + restart
sudo rvg host panel.example.com # change public address + restart
sudo rvg public-port 8443       # explicit TLS port in links (empty = follow panel port)
sudo rvg tls off                # disable internal self-signed TLS (Caddy/nginx in front)
sudo rvg password NewPass123    # reset admin password (kills sessions)
sudo rvg phone-home off         # disable any central-server contact (default)
```

Environment variables understood by the app itself:

| Variable | Effect |
|---|---|
| `PORT` | Panel listen port (wins over state file) |
| `RVG_PUBLIC_HOST` | Public host (wins over state file) |
| `PUBLIC_PORT` | Explicit TLS port in links |
| `RVG_TLS=0` | Disable internal self-signed TLS — external terminator expected |
| `ADMIN_PASSWORD` | Pre-set admin password at first run |
| `SECRET_KEY` | Fixed internal secret instead of per-install random |
| `RVG_DISABLE_LOGS=1` | Start with logging disabled |
| `RVG_PHONE_HOME=1` | Force-enable central contact |
| `DATA_DIR` | Data directory override |

---

## 4. Backup Management

### CLI archives

```bash
sudo rvg backup create [name]   # → /var/lib/rvg/backups/rvg-backup-[name-]YYYYmmdd-HHMMSS.tar.gz
sudo rvg backup list
sudo rvg backup restore latest
sudo rvg backup restore /path/to/file.tar.gz
sudo rvg backup delete <file>
```

Each archive contains: `rvg_state.json` (links/subs/nodes/admin hash/settings),
`.rvg_secret` (crypto secret), update history and optional bot token.

### Restoring manually

```bash
sudo systemctl stop rvg
sudo tar xzf backup.tar.gz -C /var/lib/rvg
sudo chown rvg:rvg /var/lib/rvg/.rvg_secret && sudo chmod 600 /var/lib/rvg/.rvg_secret
sudo systemctl start rvg
```

### JSON export/import (dashboard)

Dashboard → Settings → Backup lets you download a portable JSON of all links &
subs and re-import it later — handy when migrating between panels.
A safety `pre-update-*.tar.gz` is created automatically before every update.

**Keep backups private** — they contain secrets (stored mode `600`).

---

## 5. Stopping / Shutting Down

```bash
sudo rvg stop                  # graceful: state flushed to disk, ports closed
```

Prevent autostart after reboot:

```bash
sudo systemctl disable rvg     # enable again with: sudo systemctl enable --now rvg
```

> ⚠️ The unit has `Restart=always`: killing processes manually or using
> `kill -9` will not keep it down — systemd revives it within seconds.
> Always use `stop`.

To verify it is fully offline:

```bash
systemctl is-active rvg        # should print: inactive
curl -m 2 http://127.0.0.1:8080/health || echo "offline"
```

---

## 6. Disabling All Logs

Level A — application silence (recommended):

```bash
sudo rvg logs-off
```

This disables Python loggers (app, uvicorn access/error), error-log buffers and
activity recording. With logging disabled the app skips formatting/I-O entirely,
which also slightly improves throughput. Persisted across restarts.

Optional Level B — mute journald capture too:

```bash
sudo mkdir -p /etc/systemd/system/rvg.service.d
printf '[Service]\nStandardOutput=null\nStandardError=null\n' \
  > /etc/systemd/system/rvg.service.d/silent.conf
sudo systemctl daemon-reload
sudo systemctl restart rvg
```

Re-enable everything:

```bash
sudo rm /etc/systemd/system/rvg.service.d/silent.conf
sudo systemctl daemon-reload
sudo rvg logs-on
```

Or start silenced via env: add `RVG_DISABLE_LOGS=1` to `/etc/rvg.conf`.

---

## 7. Updating

```bash
sudo rvg update
```

Flow: pre-update backup → `git pull` (if git checkout) → `pip install -r requirements.txt` → restart.
If the folder is not a git checkout, download a new release, extract over
`/opt/rvg` and run `sudo bash install.sh --force`.

---

## 8. Uninstalling

```bash
sudo rvg uninstall
```

Removes service, code, CLI and config. Your data directory
(`/var/lib/rvg`) is only deleted after an extra confirmation.

---

## 9. Firewall & Ports

| Ports | Purpose |
|---|---|
| `8080/tcp` (or custom) | Panel web UI + VLESS/Trojan/SS WebSocket endpoints behind TLS terminator |
| `8500–8600/tcp` | MTProto instances (one port per MTProto link) |

Open them automatically:

```bash
sudo rvg firewall
```

Supports `ufw` (Debian/Ubuntu family) and `firewalld` (AlmaLinux/Rocky/RHEL/Fedora).

Check listeners:

```bash
ss -tlnp | grep -E '8080|mtproto'
```

---

## 10. TLS / Reverse Proxy (optional)

By default the panel serves **HTTPS/WSS itself with a self-signed certificate** on
its own port, so generated links work out of the box (clients need
`allowInsecure=1`, which the panel adds automatically).

If you want a real/trusted certificate, terminate TLS in front of the panel and
switch the panel to external-TLS mode:

```bash
sudo rvg tls off && sudo rvg host panel.example.com && sudo rvg public-port 443
```

### Caddy (automatic certificates) — recommended

```
panel.example.com {
    reverse_proxy 127.0.0.1:8080
}
```

### nginx

```nginx
server {
    listen 443 ssl http2;
    server_name panel.example.com;
    ssl_certificate     /etc/letsencrypt/live/panel.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/panel.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
    }
}
```

MTProto ports are raw TCP — they must be reachable directly (no proxy needed).

---

## 11. Troubleshooting

| Symptom | Cause / Fix |
|---|---|
| Browser can't connect | Service down? `sudo rvg status`. Firewall? `sudo rvg firewall`. Cloud provider security group must allow the port too. With the default internal TLS the browser shows a self-signed warning once — accept it. |
| `Address already in use` | Another app owns 8080 → `sudo rvg port 9090` |
| Locked out / forgot password | `sudo rvg password NewStrongPass` |
| Links show wrong domain/IP | `sudo rvg host your-domain.com` |
| Links use wrong port | Internal TLS (default): links follow the real panel port automatically. Behind Caddy/nginx: `sudo rvg tls off && sudo rvg public-port 443` |
| MTProto link dead | Instance port blocked → `sudo rvg firewall`; check link's port in dashboard |
| Service flapping | `journalctl -u rvg -n 100 --no-pager` |
| Update failed mid-way | Restore newest `pre-update-*.tar.gz` (see §4) |
| Disk full | Check `/var/lib/rvg/backups` and journal size |

Still stuck? Run `sudo rvg info` and include its output plus recent logs when opening an issue.
