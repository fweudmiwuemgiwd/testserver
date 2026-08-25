# xcore.py
# ══════════════════════════════════════════════════════════════════════════════
# بک‌اند یکپارچه — یک باینری رسمی (SagerNet/sing-box) که تمام پروتکل‌های
# «سنگین‌کریپتو» رو مدیریت می‌کنه: VLESS+REALITY، Trojan+REALITY، Shadowsocks،
# Hysteria2 و WireGuard. دلیل استفاده از sing-box به‌جای پیاده‌سازی دستی این
# پروتکل‌ها دقیقاً همون فلسفه‌ی مورد استفاده در mtproto_native.py هست: این‌ها
# پروتکل‌های حساس امنیتی/کریپتوگرافی‌ان که پیاده‌سازی دستی‌شون یا ناامنه یا با
# کلاینت‌های واقعی (v2rayNG, NekoBox, Hiddify, ...) سازگار نیست. با sing-box،
# هم REALITY واقعی داریم (سازگار صددرصد با اکوسیستم استاندارد)، هم Hysteria2
# و WireGuard که اصلاً معادل خالص‌پایتونی معقولی ندارن.
#
# چرا یک باینری برای همه؟ چون sing-box (بر خلاف Xray-core) هم Hysteria2 و هم
# WireGuard رو به‌عنوان inbound/endpoint پشتیبانی می‌کنه، پس به‌جای دو باینری
# جدا (Xray برای Reality + یه چیز دیگه برای Hysteria2/WireGuard)، یک پروسه‌ی
# مشترک با یک کانفیگ JSON کل این پنج پروتکل رو پوشش می‌ده.
#
# معماری مدیریت پروسه دقیقاً مثل reality.py قبلی: یک پروسه‌ی مشترک، به‌ازای
# هر لینک یک inbound/endpoint جدا با پورت اختصاصی خودش؛ با هر افزودن/حذف
# لینک، کانفیگ بازنویسی و پروسه graceful ری‌استارت می‌شه.
# ══════════════════════════════════════════════════════════════════════════════

import asyncio
import base64
import datetime
import ipaddress
import json
import logging
import os
import platform
import secrets
import tarfile
from collections import deque
from pathlib import Path
from typing import Optional

import httpx
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.x509.oid import NameOID

logger = logging.getLogger("RVG-Gateway")

from appconfig import resolve_data_dir

DATA_DIR = resolve_data_dir()
SB_DIR = DATA_DIR / "singbox"
BIN_PATH = SB_DIR / "sing-box"
CONFIG_PATH = SB_DIR / "config.json"
CERT_PATH = SB_DIR / "cert.pem"
KEY_PATH = SB_DIR / "key.pem"

SB_VERSION = "1.11.0"  # نسخه‌ی شناخته‌شده و تست‌شده — از GitHub API عبور می‌کنیم
                        # که با ریت‌لیمیت مشکل نداشته باشیم (تجربه‌ی reality.py قبلی)

DEFAULT_REALITY_DEST = "www.microsoft.com:443"
DEFAULT_REALITY_SNI = ["www.microsoft.com"]

MAX_LOG_LINES = 300
_log: deque = deque(maxlen=MAX_LOG_LINES)

_proc: Optional[asyncio.subprocess.Process] = None
_proc_lock = asyncio.Lock()
_reader_task: Optional[asyncio.Task] = None

# لینک‌های فعال: uid -> {kind, port, ...پارامترهای خاص هر kind}
# kind یکی از: vless-reality | trojan-reality | shadowsocks-xray | hysteria2 | wireguard
_links: dict[str, dict] = {}
_links_lock = asyncio.Lock()


def _log_line(msg: str):
    _log.append({"time": datetime.datetime.now().isoformat(), "msg": msg})
    logger.info(f"xcore/sing-box: {msg}")


# ══════════════════════════════════════════════════════════════════════════════
# دانلود باینری رسمی sing-box
# ══════════════════════════════════════════════════════════════════════════════

def _asset_name_for_platform() -> str:
    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        arch = "amd64"
    elif machine in ("aarch64", "arm64"):
        arch = "arm64"
    elif machine.startswith("armv7") or machine == "armhf":
        arch = "armv7"
    else:
        raise RuntimeError(f"معماری پشتیبانی‌نشده برای دانلود sing-box: {machine}")
    return f"sing-box-{SB_VERSION}-linux-{arch}.tar.gz", f"sing-box-{SB_VERSION}-linux-{arch}"


async def ensure_binary() -> Path:
    if BIN_PATH.exists() and os.access(BIN_PATH, os.X_OK):
        return BIN_PATH

    SB_DIR.mkdir(parents=True, exist_ok=True)
    asset_file, inner_dir = _asset_name_for_platform()
    url = f"https://github.com/SagerNet/sing-box/releases/download/v{SB_VERSION}/{asset_file}"
    _log_line(f"دانلود sing-box v{SB_VERSION} از {url}")

    tar_path = SB_DIR / "singbox.tar.gz"
    async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
        async with client.stream("GET", url) as resp:
            resp.raise_for_status()
            with open(tar_path, "wb") as f:
                async for chunk in resp.aiter_bytes(1024 * 256):
                    f.write(chunk)

    with tarfile.open(tar_path) as tf:
        member = tf.getmember(f"{inner_dir}/sing-box")
        member.name = "sing-box"
        tf.extract(member, path=SB_DIR)
    tar_path.unlink(missing_ok=True)
    BIN_PATH.chmod(0o755)
    _log_line(f"sing-box v{SB_VERSION} با موفقیت نصب شد ({BIN_PATH})")
    return BIN_PATH


# ══════════════════════════════════════════════════════════════════════════════
# کریپتو: X25519 (REALITY) و گواهی self-signed (Hysteria2)
# ══════════════════════════════════════════════════════════════════════════════

def _b64url_nopad(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def generate_x25519_keypair() -> tuple[str, str]:
    """برای REALITY — همون فرمت خروجی `sing-box generate reality-keypair`."""
    priv = X25519PrivateKey.generate()
    pub = priv.public_key()
    return _b64url_nopad(priv.private_bytes_raw()), _b64url_nopad(pub.public_bytes_raw())


def generate_wg_keypair() -> tuple[str, str]:
    """برای WireGuard — فرمت base64 استاندارد wg (نه urlsafe/nopad)."""
    priv = X25519PrivateKey.generate()
    pub = priv.public_key()
    priv_b64 = base64.b64encode(priv.private_bytes_raw()).decode()
    pub_b64 = base64.b64encode(pub.public_bytes_raw()).decode()
    return priv_b64, pub_b64


def generate_short_id() -> str:
    return secrets.token_hex(4)


def ensure_self_signed_cert():
    """یک گواهی TLS self-signed برای Hysteria2 می‌سازه (فقط یک‌بار)."""
    if CERT_PATH.exists() and KEY_PATH.exists():
        return
    SB_DIR.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "bing.com")])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name).issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=3650))
        .sign(key, hashes.SHA256())
    )
    CERT_PATH.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    KEY_PATH.write_bytes(key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    ))
    _log_line("گواهی self-signed برای Hysteria2 ساخته شد")


# ══════════════════════════════════════════════════════════════════════════════
# ساخت کانفیگ JSON مشترک — یک inbound/endpoint به‌ازای هر لینک
# ══════════════════════════════════════════════════════════════════════════════

def _wg_next_client_ip(used: set[str]) -> str:
    for i in range(2, 254):
        ip = f"10.90.90.{i}/32"
        if ip not in used:
            return ip
    raise RuntimeError("ظرفیت آدرس‌های داخلی WireGuard تمام شده")


def _build_config() -> dict:
    inbounds, endpoints = [], []

    for uid, d in _links.items():
        kind = d["kind"]

        if kind == "vless-reality":
            inbounds.append({
                "type": "vless", "tag": f"vr-{uid}",
                "listen": "::", "listen_port": d["port"],
                "users": [{"uuid": d["uuid"], "flow": d.get("flow", "xtls-rprx-vision")}],
                "tls": {
                    "enabled": True, "server_name": d["server_names"][0],
                    "reality": {
                        "enabled": True,
                        "handshake": {"server": d["server_names"][0], "server_port": d["dest_port"]},
                        "private_key": d["private_key"],
                        "short_id": d["short_ids"],
                    },
                },
            })

        elif kind == "trojan-reality":
            inbounds.append({
                "type": "trojan", "tag": f"tr-{uid}",
                "listen": "::", "listen_port": d["port"],
                "users": [{"password": d["password"]}],
                "tls": {
                    "enabled": True, "server_name": d["server_names"][0],
                    "reality": {
                        "enabled": True,
                        "handshake": {"server": d["server_names"][0], "server_port": d["dest_port"]},
                        "private_key": d["private_key"],
                        "short_id": d["short_ids"],
                    },
                },
            })

        elif kind == "shadowsocks-xray":
            inbounds.append({
                "type": "shadowsocks", "tag": f"ss-{uid}",
                "listen": "::", "listen_port": d["port"],
                "method": d["method"], "password": d["password"],
            })

        elif kind == "hysteria2":
            inbounds.append({
                "type": "hysteria2", "tag": f"hy2-{uid}",
                "listen": "::", "listen_port": d["port"],
                "users": [{"password": d["password"]}],
                "tls": {
                    "enabled": True, "alpn": ["h3"],
                    "certificate_path": str(CERT_PATH), "key_path": str(KEY_PATH),
                },
            })

        elif kind == "wireguard":
            endpoints.append({
                "type": "wireguard", "tag": f"wg-{uid}",
                "system": False,
                "listen_port": d["port"],
                "private_key": d["server_private_key"],
                "address": [d["server_ip_cidr"]],
                "peers": [{
                    "public_key": d["client_public_key"],
                    "allowed_ips": [d["client_ip_cidr"]],
                }],
                "mtu": 1408,
            })

    cfg = {
        "log": {"level": "warn"},
        "inbounds": inbounds,
        "outbounds": [{"type": "direct", "tag": "direct"}],
    }
    if endpoints:
        cfg["endpoints"] = endpoints
    return cfg


async def _write_config():
    SB_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(_build_config(), ensure_ascii=False, indent=2), encoding="utf-8")


async def _read_stderr(proc: asyncio.subprocess.Process):
    try:
        while True:
            line = await proc.stderr.readline()
            if not line:
                break
            _log_line(line.decode(errors="ignore").rstrip())
    except Exception:
        pass


async def _start_process():
    global _proc, _reader_task
    bin_path = await ensure_binary()
    ensure_self_signed_cert()
    await _write_config()
    _proc = await asyncio.create_subprocess_exec(
        str(bin_path), "run", "-c", str(CONFIG_PATH),
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    _reader_task = asyncio.create_task(_read_stderr(_proc))
    _log_line(f"پروسه‌ی sing-box بالا اومد (pid={_proc.pid}, {len(_links)} سرویس)")


async def _stop_process():
    global _proc, _reader_task
    if _proc is not None:
        try:
            _proc.terminate()
            await asyncio.wait_for(_proc.wait(), timeout=5.0)
        except Exception:
            try:
                _proc.kill()
            except Exception:
                pass
        _proc = None
    if _reader_task is not None:
        _reader_task.cancel()
        _reader_task = None


async def _restart_if_needed():
    async with _proc_lock:
        await _stop_process()
        if _links:
            try:
                await _start_process()
            except Exception as exc:
                logger.error(f"xcore/sing-box: راه‌اندازی ناموفق بود: {exc}")
                raise


# ══════════════════════════════════════════════════════════════════════════════
# API سطح بالا — افزودن/حذف لینک به‌ازای هر پروتکل
# ══════════════════════════════════════════════════════════════════════════════

async def add_vless_reality(uid: str, uuid_: str, port: int, dest: str = None,
                             flow: str = "xtls-rprx-vision") -> dict:
    dest = dest or DEFAULT_REALITY_DEST
    host, _, dport = dest.partition(":")
    priv, pub = generate_x25519_keypair()
    sid = generate_short_id()
    async with _links_lock:
        _links[uid] = {
            "kind": "vless-reality", "uuid": uuid_, "port": port,
            "server_names": [host], "dest_port": int(dport or 443),
            "private_key": priv, "short_ids": [sid], "flow": flow,
        }
    await _restart_if_needed()
    return {"public_key": pub, "short_id": sid, "server_name": host, "private_key": priv}


async def add_trojan_reality(uid: str, port: int, dest: str = None) -> dict:
    dest = dest or DEFAULT_REALITY_DEST
    host, _, dport = dest.partition(":")
    priv, pub = generate_x25519_keypair()
    sid = generate_short_id()
    password = secrets.token_urlsafe(16)
    async with _links_lock:
        _links[uid] = {
            "kind": "trojan-reality", "port": port,
            "server_names": [host], "dest_port": int(dport or 443),
            "private_key": priv, "short_ids": [sid], "password": password,
        }
    await _restart_if_needed()
    return {"public_key": pub, "short_id": sid, "server_name": host,
            "private_key": priv, "password": password}


async def add_shadowsocks_xray(uid: str, port: int, method: str = "chacha20-ietf-poly1305") -> dict:
    password = secrets.token_urlsafe(16)
    async with _links_lock:
        _links[uid] = {"kind": "shadowsocks-xray", "port": port, "method": method, "password": password}
    await _restart_if_needed()
    return {"password": password, "method": method}


async def add_hysteria2(uid: str, port: int) -> dict:
    password = secrets.token_urlsafe(16)
    async with _links_lock:
        _links[uid] = {"kind": "hysteria2", "port": port, "password": password}
    await _restart_if_needed()
    return {"password": password}


async def add_wireguard(uid: str, port: int) -> dict:
    server_priv, server_pub = generate_wg_keypair()
    client_priv, client_pub = generate_wg_keypair()
    async with _links_lock:
        used_ips = {d.get("client_ip_cidr") for d in _links.values() if d.get("kind") == "wireguard"}
        client_ip = _wg_next_client_ip(used_ips)
        _links[uid] = {
            "kind": "wireguard", "port": port,
            "server_private_key": server_priv, "server_public_key": server_pub,
            "server_ip_cidr": "10.90.90.1/24",
            "client_private_key": client_priv, "client_public_key": client_pub,
            "client_ip_cidr": client_ip,
        }
    await _restart_if_needed()
    return {
        "server_public_key": server_pub, "client_private_key": client_priv,
        "client_public_key": client_pub, "client_ip_cidr": client_ip,
    }


async def remove_link(uid: str):
    async with _links_lock:
        _links.pop(uid, None)
    await _restart_if_needed()


def get_link_meta(uid: str) -> Optional[dict]:
    return _links.get(uid)


def is_running() -> bool:
    return _proc is not None and _proc.returncode is None


def get_status() -> dict:
    by_kind = {}
    for d in _links.values():
        by_kind[d["kind"]] = by_kind.get(d["kind"], 0) + 1
    return {
        "running": is_running(), "links_count": len(_links), "by_kind": by_kind,
        "version": SB_VERSION, "binary_installed": BIN_PATH.exists(),
        "logs": list(_log)[-100:],
    }


async def restore_links(saved: dict[str, dict]):
    """بعد از ری‌استارت پنل، همه‌ی لینک‌های sing-box (از هر نوع) رو با همون
    کلید/پسورد قبلی دوباره بالا می‌آره — کلیدها هرگز عوض نمی‌شن."""
    async with _links_lock:
        _links.update(saved)
    if _links:
        await _restart_if_needed()
