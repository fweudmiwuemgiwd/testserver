# appconfig.py
# ══════════════════════════════════════════════════════════════════════════════
# Shared runtime paths & defaults for the self-hosted Linux edition.
# Every module (main, updater, mtproto_native) imports from
# here so DATA_DIR / APP_DIR / port defaults stay consistent across the app.
#
# Resolution order for DATA_DIR:
#   1. $DATA_DIR environment variable (set by systemd unit)
#   2. /var/lib/rvg            (standard self-hosted location, if writable)
#   3. ./data                  (development fallback)
# ══════════════════════════════════════════════════════════════════════════════
import os
from pathlib import Path

APP_NAME = "rvg"
DEFAULT_PORT = 8080            # self-hosted default panel port
DEFAULT_PUBLIC_PORT = 443      # TLS port advertised in generated share links
SYSTEM_DATA_DIR = Path("/var/lib/rvg")
LOCAL_DATA_DIR = Path(__file__).resolve().parent / "data"


def _is_writable(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".rvg_write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except Exception:
        return False


def resolve_data_dir() -> Path:
    env = os.environ.get("DATA_DIR", "").strip()
    if env:
        p = Path(env)
        p.mkdir(parents=True, exist_ok=True)
        return p
    if os.name == "posix" and _is_writable(SYSTEM_DATA_DIR):
        return SYSTEM_DATA_DIR
    _is_writable(LOCAL_DATA_DIR)
    return LOCAL_DATA_DIR


def resolve_app_dir() -> Path:
    env = os.environ.get("APP_DIR", "").strip()
    if env:
        return Path(env)
    return Path(__file__).resolve().parent


def backups_dir() -> Path:
    d = resolve_data_dir() / "backups"
    d.mkdir(parents=True, exist_ok=True)
    return d


def tls_dir() -> Path:
    """گواهی self-signed پنل (برای TLS واقعی روی پورت panel در حالت self-hosted).
    این جدا از گواهی Hysteria2 (xcore) هست — این مال خودِ FastAPI/uvicorn است."""
    d = resolve_data_dir() / "tls"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── Public host resolution (replaces Railway's RAILWAY_PUBLIC_DOMAIN) ─────────
def get_env_public_host() -> str:
    for key in ("RVG_PUBLIC_HOST", "PUBLIC_HOST", "RVG_DOMAIN"):
        val = os.environ.get(key, "").strip()
        if val:
            return val
    return ""
