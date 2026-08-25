<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0f2027,50:203a43,100:2c5364&height=220&section=header&text=RVG%20Gateway&fontSize=60&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=Self-Hosted%20Linux%20Edition&descAlignY=58&descSize=18" width="100%"/>

<a href="#-english"><img src="https://img.shields.io/badge/🇬🇧-English-0f2027?style=for-the-badge" /></a>
<a href="#-فارسی"><img src="https://img.shields.io/badge/🇮🇷-فارسی-203a43?style=for-the-badge" /></a>

<br/>

![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=22&pause=1000&color=2C5364&center=true&vCenter=true&width=640&lines=Self-Hosted+Multi-Protocol+Proxy+Panel;VLESS+%7C+Trojan+%7C+Shadowsocks+%7C+MTProto;One-line+install+on+any+major+Linux;Web-based+setup+wizard+%B7+Port+8080)

<br/>

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Async-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Linux](https://img.shields.io/badge/Linux-Debian%20%7C%20Ubuntu%20%7C%20AlmaLinux-FCC624?style=for-the-badge&logo=linux&logoColor=black)](#-supported-distributions)
[![License](https://img.shields.io/badge/License-Custom-red?style=for-the-badge)](./LICENSE)

![Stars](https://img.shields.io/github/stars/arvin341az-glitch/RVG?style=social)
![Forks](https://img.shields.io/github/forks/arvin341az-glitch/RVG?style=social)
![Last Commit](https://img.shields.io/github/last-commit/arvin341az-glitch/RVG?color=2c5364)
![Repo Size](https://img.shields.io/github/repo-size/arvin341az-glitch/RVG?color=0f2027)

</div>

<br/>

---

<div align="center">
<h1>🇬🇧 English</h1>
</div>

## 📖 Table of Contents

- [Overview](#-overview)
- [Highlights](#-highlights)
- [Supported Distributions](#-supported-distributions)
- [Quick Install](#-quick-install-3-steps)
- [The Setup Wizard](#-the-setup-wizard)
- [Supported Protocols](#-supported-protocols)
- [Complete Usage Guide](#-complete-usage-guide)
  - [Service Management](#1-service-management)
  - [Backup & Restore](#2-backup--restore)
  - [Stopping / Shutting Down](#3-stopping--shutting-down-the-application)
  - [Disabling All Logs](#4-disabling-all-logs)
  - [Updating](#5-updating)
  - [Uninstalling](#6-uninstalling)
- [Configuration Reference](#️-configuration-reference)
- [Project Structure](#-project-structure)
- [Security Notes](#-security-notes)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

<br/>

## 🚀 Overview

**RVG Gateway (Self-Hosted Edition)** is a fast, modern **multi-protocol proxy management panel** designed to run on **your own Linux server** — no cloud platform required.

Install it with one command, open the beautiful web setup wizard on port **8080**, and manage proxy links, traffic quotas, live connections and subscriptions from a polished dashboard.

> 🔒 Fully self-contained: no Railway dependency, no phone-home telemetry (opt-in only), all data stays on your server.

<br/>

## ✨ Highlights

<table>
<tr>
<td width="50%">

### 🖥️ True Self-Hosting
- One-command installer for all major distros
- Modern **web setup wizard** on first run
- systemd service with auto-restart & boot start
- Runs on port **8080** by default
- `rvg` CLI for every operation

</td>
<td width="50%">

### 🛠️ Operations Built-In
- **Backups**: create / list / restore / delete
- **Log kill-switch**: disable *all* logging instantly
- Password reset, port change, host change from CLI
- Firewall helper (ufw / firewalld / iptables)
- Safe updates with automatic pre-update backup

</td>
</tr>
<tr>
<td width="50%">

### 🔌 Multi-Protocol Gateway
- VLESS over WebSocket / xHTTP
- Trojan over WebSocket / xHTTP
- Shadowsocks (AEAD aes-256-gcm)
- MTProxy (official Telegram binary) — direct ports, no TCP-proxy service needed

</td>
<td width="50%">

### 📊 Management Dashboard
- Live traffic charts & connection monitor
- Unlimited links with per-link quotas/expiry
- Subscription groups + public sub pages
- QR export, multi-node linking

</td>
</tr>
</table>

<br/>

## 🐧 Supported Distributions

| Family | Distributions | Package Manager |
|---|---|---|
| Debian-based | Debian 11/12+, Ubuntu 20.04 / 22.04 / 24.04+, Mint, Kali | `apt` |
| RHEL-family | **AlmaLinux 8 / 9 / 10**, Rocky Linux, RHEL, CentOS Stream, Fedora | `dnf` / `yum` |

Any other distribution with Python ≥ 3.10 works too (manual install).

<br/>

## ⚡ Quick Install (3 steps)

```bash
# 1. Get the code
git clone https://github.com/arvin341az-glitch/RVG.git
cd RVG

# 2. Run the installer (as root)
sudo bash install.sh

# 3. Open the setup wizard in your browser
#    http://<server-ip>:8080/setup
```

Installer options:

| Option | Description | Default |
|---|---|---|
| `--port N` | Panel port | `8080` |
| `--host HOST` | Public domain/IP | server IP |
| `--no-firewall` | Skip firewall configuration | — |
| `--force` | Overwrite existing files | — |

Example: `sudo bash install.sh --port 8080 --host panel.example.com`

The installer will:
1. Install system packages (Python 3.10+, git, build tools) using your distro's package manager
2. Create a dedicated `rvg` system user
3. Copy the app to `/opt/rvg`, data to `/var/lib/rvg`
4. Create an isolated virtualenv and install dependencies
5. Register & start the `systemd` service (`rvg.service`)
6. Open ports in `ufw` / `firewalld` automatically

<br/>

## 🪄 The Setup Wizard

On first run you are greeted by a modern, step-by-step web wizard:

```
┌─────────────────────────────────────────────┐
│  🛡 RVG Gateway · راه‌اندازی اولیه           │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━              │
│                                             │
│  Step 1 · Welcome                           │
│  Step 2 · Admin password (strength meter)   │
│  Step 3 · Public host, TLS port, panel port │
│           + optional phone-home toggle      │
│  Done   · Summary + dashboard link          │
└─────────────────────────────────────────────┘
```

Until setup is complete, **every route redirects to `/setup`** and the API refuses logins — there is no default password.

<br/>

## 🌐 Supported Protocols

| Protocol | Transport | Self-hosted notes |
|---|---|---|
| VLESS | WebSocket / xHTTP | Serve behind TLS (nginx/Caddy) on your TLS port |
| Trojan | WebSocket / xHTTP | Same as VLESS |
| Shadowsocks | AEAD (aes-256-gcm) | Same as VLESS |
| MTProto | Official MTProxy binary | Listens on its own TCP port directly (8500–8600 opened by installer) |

> 💡 **TLS tip:** by default the panel itself serves **HTTPS/WSS with a self-signed certificate** on its own port, so all generated configs work out of the box (links include `allowInsecure=1`). If you prefer a real certificate, put [Caddy](https://caddyserver.com) or nginx in front of the panel and run `sudo rvg tls off` — links will then use your TLS port (default `443`) without `allowInsecure`.

<br/>

## 📘 Complete Usage Guide

Everything below is also available offline via `rvg help`.

### 1) Service Management

The application runs as a systemd service named **`rvg`**.

```bash
sudo rvg status          # detailed status
sudo rvg start           # start the panel
sudo rvg stop            # stop the panel
sudo rvg restart         # restart after config changes
sudo rvg logs            # last 100 log lines
sudo rvg logs -f         # live-follow logs
sudo rvg info            # installation summary (paths, version, state)
```

Equivalent raw systemd commands:

```bash
systemctl status rvg
journalctl -u rvg -f
```

### 2) Backup & Restore

Backups archive your full state (links, subs, nodes, admin hash, secrets):

```bash
sudo rvg backup create               # timestamped backup → /var/lib/rvg/backups/
sudo rvg backup create myname        # custom name
sudo rvg backup list                 # list backups (newest first)
sudo rvg backup restore latest       # restore newest backup (asks YES)
sudo rvg backup restore FILE.tar.gz  # restore specific file
sudo rvg backup delete FILE.tar.gz   # delete one backup
```

Notes:
- Updates create an automatic safety backup (`pre-update-*.tar.gz`) first.
- Backups contain secrets — they are stored with mode `600`.
- You can download/import JSON backups from the dashboard too (**Settings → Backup**).

### 3) Stopping / Shutting Down the Application

```bash
sudo rvg stop                 # graceful shutdown (state is flushed to disk)
sudo systemctl stop rvg       # same thing, native systemd
```

To prevent it from starting at boot:

```bash
sudo systemctl disable rvg    # re-enable later: sudo systemctl enable --now rvg
```

Because the service uses `Restart=always`, always use `stop` rather than killing processes manually — systemd will otherwise bring it back within seconds.

### 4) Disabling All Logs

Two levels of silence:

```bash
# A) Application-level: disables ALL app logging, access logs,
#    error buffers and activity recording (zero I/O overhead):
sudo rvg logs-off

# B) Optional: also mute journald capture of the service:
sudo mkdir -p /etc/systemd/system/rvg.service.d
printf '[Service]\nStandardOutput=null\nStandardError=null\n' \
  > /etc/systemd/system/rvg.service.d/silent.conf
sudo systemctl daemon-reload && sudo systemctl restart rvg

# Turn everything back on:
sudo rvg logs-on
```

You can also bake it in from the start with the environment variable:

```bash
# /etc/rvg.conf
RVG_DISABLE_LOGS=1
```

### 5) Updating

```bash
sudo rvg update
```

Creates a pre-update backup → pulls latest code (git checkout) → refreshes dependencies → restarts the service.

### 6) Uninstalling

```bash
sudo rvg uninstall     # asks before deleting your data/backups
```

<br/>

## ⚙️ Configuration Reference

Runtime config lives in **`/etc/rvg.conf`** (managed by `rvg` CLI). Everything can also be changed from the dashboard.

| Variable | Description | Default |
|---|---|---|
| `PORT` | Panel listen port | `8080` |
| `RVG_PUBLIC_HOST` | Public domain/IP used in generated links | set via wizard |
| `PUBLIC_PORT` | Explicit TLS port advertised in links (empty = follow the real panel port when internal TLS is on) | auto |
| `RVG_TLS` | Internal panel TLS: `1` = self-signed HTTPS/WSS served by the panel itself, `0` = external terminator (Caddy/nginx) | `1` |
| `DATA_DIR` | Persistent data directory | `/var/lib/rvg` |
| `ADMIN_PASSWORD` | Pre-set admin password (skips wizard password step) | — |
| `SECRET_KEY` | Fixed internal secret (auto-generated otherwise) | random |
| `RVG_DISABLE_LOGS` | Start with all logging disabled | `0` |
| `RVG_PHONE_HOME` | Opt-in contact with central announcement server | `0` |

CLI shortcuts:

```bash
sudo rvg port 9000          # change panel port
sudo rvg host panel.example.com
sudo rvg public-port 8443   # explicit link port (e.g. behind a TLS terminator)
sudo rvg tls off            # switch to external TLS (Caddy/nginx) + restart
sudo rvg password NewStrongPass
sudo rvg phone-home off     # default: fully private
sudo rvg firewall           # (re-)open required ports
```

<br/>

## 📂 Project Structure

```
RVG/
├── main.py                  # FastAPI app entrypoint (+setup endpoints)
├── appconfig.py             # Shared paths & defaults (self-hosted core)
├── pages.py                 # Login / Setup-wizard / Dashboard HTML
├── central.py               # Optional central-server contact (opt-in)
├── updater.py               # Version/update machinery
├── protocol/                # Per-protocol relays (vless/trojan/ss/mtproto)
├── bin/rvg                  # Management CLI (installed to /usr/local/bin)
├── deploy/rvg.service       # systemd unit template
├── install.sh               # Universal installer (apt/dnf/yum)
├── update.sh                # Update flow (with safety backup)
├── uninstall.sh             # Clean removal
├── requirements.txt
└── version.txt              # Current version manifest
```

<br/>

## 🔐 Security Notes

- No default password exists — the panel is locked until you finish `/setup`.
- Admin sessions use HttpOnly cookies with 7-day expiry.
- Secrets live in `/var/lib/rvg` with restrictive permissions.
- Phone-home telemetry is **off** by default; announcements/support require explicit opt-in.
- For public exposure, we recommend putting Caddy/nginx with a valid certificate in front of the panel.

See [SECURITY.md](./SECURITY.md) and [docs/USAGE.md](./docs/USAGE.md) for details.

<br/>

## 🩺 Troubleshooting

| Symptom | Fix |
|---|---|
| Page doesn't open | `sudo rvg status` · check firewall: `sudo rvg firewall` |
| Port already in use | `sudo rvg port 8090` then restart |
| Forgot admin password | `sudo rvg password NewPass123` |
| Service keeps restarting | `journalctl -u rvg -n 50` |
| MTProto links dead | Open ports 8500–8600 (`sudo rvg firewall`) and check the link's port |
| Wrong address in links | `sudo rvg host your-domain.com` |

<br/>

## 🤝 Contributing

Pull requests are welcome for bug fixes, optimizations, and documentation.
> ⚠️ Please read the [LICENSE](./LICENSE) before contributing.

## 📄 License

This project is distributed under a **custom license**:
✅ Free to use, deploy, and fork
❌ Modifying and redistributing a modified version is **not permitted**

See the full [LICENSE](./LICENSE) file for details.

---

<div align="center">
<h1 dir="rtl">🇮🇷 فارسی</h1>
</div>

## 🚀 معرفی

**RVG Gateway (نسخه سلف‌هاست)** یک پنل مدیریت پروکسی چندپروتکلی، سریع و مدرن است که مستقیماً روی **سرور لینوکسی خودتان** اجرا می‌شود — بدون نیاز به هیچ پلتفرم ابری.

با یک دستور نصب کنید، ویزارد وب زیبای راه‌اندازی را روی پورت **۸۰۸۰** باز کنید و از داشبورد حرفه‌ای، لینک‌ها، محدودیت ترافیک، اتصالات زنده و اشتراک‌ها را مدیریت کنید.

> 🔒 کاملاً مستقل: بدون وابستگی به Railway، بدون ارسال اطلاعات (فقط با اجازه شما)، همه‌ی داده‌ها روی سرور خودتان می‌ماند.

<br/>

## 🐧 توزیع‌های پشتیبانی‌شده

| خانواده | توزیع‌ها |
|---|---|
| دبیان‌بیس | Debian 11/12+، Ubuntu 20.04/22.04/24.04+، Mint، Kali |
| RHEL-بیس | **AlmaLinux 8/9/10**، Rocky، RHEL، CentOS Stream، Fedora |

<br/>

## ⚡ نصب سریع (۳ مرحله)

```bash
git clone https://github.com/arvin341az-glitch/RVG.git
cd RVG
sudo bash install.sh
```

سپس در مرورگر باز کنید: `http://<IP-سرور>:8080/setup`

نصب‌کننده به‌صورت خودکار پایتون، وابستگی‌ها، کاربر سیستمی `rvg`، سرویس systemd و فایروال را تنظیم می‌کند. گزینه‌ها:

| گزینه | توضیح | پیش‌فرض |
|---|---|---|
| `--port N` | پورت پنل | `8080` |
| `--host HOST` | دامنه یا IP عمومی | IP سرور |
| `--no-firewall` | بدون تغییر فایروال | — |

<br/>

## 🪄 ویزارد راه‌اندازی

بار اول که وارد شوید، یک ویزارد مدرن چندمرحله‌ای می‌بینید: تعیین رمز مدیر (با نشانگر قدرت رمز)، آدرس عمومی، پورت TLS و پورت پنل. تا وقتی ویزارد کامل نشود، **هیچ مسیری جز `/setup` در دسترس نیست و هیچ رمز پیش‌فرضی وجود ندارد.**

<br/>

## 📘 راهنمای کامل استفاده

### ۱) مدیریت سرویس

```bash
sudo rvg status          # وضعیت سرویس
sudo rvg start           # روشن کردن
sudo rvg stop            # خاموش کردن
sudo rvg restart         # ری‌استارت
sudo rvg logs -f         # لاگ زنده
sudo rvg info            # خلاصه نصب
```

### ۲) بکاپ و بازیابی

```bash
sudo rvg backup create             # ساخت بکاپ
sudo rvg backup list               # فهرست بکاپ‌ها
sudo rvg backup restore latest     # بازیابی آخرین بکاپ
sudo rvg backup delete FILE        # حذف یک بکاپ
```

بکاپ‌ها شامل تمام لینک‌ها، گروه‌ها، نودها و رمزها هستند و قبل از هر آپدیت هم به‌صورت خودکار یک بکاپ ایمنی گرفته می‌شود.

### ۳) خاموش کردن برنامه

```bash
sudo rvg stop                    # خاموشی کامل (دیتا ذخیره می‌شود)
sudo systemctl disable rvg       # جلوگیری از اجرای خودکار بعد از ریبوت
```

> چون سرویس `Restart=always` دارد، برای خاموش کردن همیشه از `stop` استفاده کنید نه kill دستی.

### ۴) غیرفعال کردن تمام لاگ‌ها

```bash
sudo rvg logs-off      # خاموشی کامل لاگ برنامه (بدون بار I/O)
sudo rvg logs-on       # فعال‌سازی مجدد
```

برای بی‌صدا کردن کامل خروجی journald هم به راهنمای بخش انگلیسی مراجعه کنید.

### ۵) آپدیت و حذف

```bash
sudo rvg update        # آپدیت امن با بکاپ خودکار
sudo rvg uninstall     # حذف کامل (دیتا جداگانه پرسیده می‌شود)
```

<br/>

## ⚙️ متغیرهای پیکربندی

فایل `/etc/rvg.conf` یا دستورات `rvg`:

| متغیر | توضیح | پیش‌فرض |
|---|---|---|
| `PORT` | پورت پنل | `8080` |
| `RVG_PUBLIC_HOST` | دامنه/IP عمومی برای لینک‌ها | با ویزارد |
| `PUBLIC_PORT` | پورت TLS در لینک‌ها | `443` |
| `DATA_DIR` | مسیر داده‌ها | `/var/lib/rvg` |
| `RVG_DISABLE_LOGS` | شروع بدون لاگ | `0` |
| `RVG_PHONE_HOME` | ارتباط با سرور مرکزی | `0` |

<br/>

<div align="center">

**ساخته‌شده با ❤️ توسط [codebox](https://github.com/arvin341az-glitch)**

</div>

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:2c5364,50:203a43,100:0f2027&height=120&section=footer" width="100%"/>
