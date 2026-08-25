# tlscert.py
# ══════════════════════════════════════════════════════════════════════════════
# گواهی TLS خودامضا (self-signed) برای پنل self-hosted.
#
# چرا این فایل وجود دارد؟
#   لینک‌های اشتراک (vless-ws / trojan-ws / xhttp / ss-ws) با security=tls ساخته
#   می‌شوند؛ یعنی کلاینت‌ها انتظار یک listener واقعی TLS دارند. روی Railway زیرساخت
#   خودش TLS را terminate می‌کرد، اما روی سرور شخصی هیچ‌کس روی ۴۴۳ گوش نمی‌دهد.
#   راه‌حل: خود پنل مستقیماً با گواهی self-signed روی همان پورتِ باز HTTPS/WSS سرو
#   می‌کند تا کانفیگ‌ها بدون نیاز به دامنه/سرویس خارجی از همان ابتدا کار کنند.
#
# گواهی در DATA_DIR/tls ذخیره می‌شود و بین ری‌استارت‌ها حفظ می‌ماند؛ فقط اگر موجود
# نباشد، منقضی (یا نزدیک انقضا) باشد، یا آدرس عمومی عوض شده باشد دوباره ساخته می‌شود.
# ══════════════════════════════════════════════════════════════════════════════
import datetime
import ipaddress
import json
import logging

from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from appconfig import resolve_data_dir

logger = logging.getLogger("RVG-Gateway")

CERT_DIR = resolve_data_dir() / "tls"
CERT_PATH = CERT_DIR / "cert.pem"
KEY_PATH = CERT_DIR / "key.pem"
META_PATH = CERT_DIR / "meta.json"

VALID_DAYS = 3650            # ~10 سال — برای گواهی self-signed کافی است
REGENERATE_THRESHOLD = 30    # اگر کمتر از ۳۰ روز به انقضا مانده باشد، تازه‌سازی می‌شود


def _host_is_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def _sans_for(host: str) -> tuple[x509.GeneralName, ...]:
    """SAN ها طوری ساخته می‌شوند که هم آدرس عمومی و هم اتصال محلی پوشش داده شود."""
    names: list[x509.GeneralName] = []
    host = (host or "").strip().lower()
    if host and host != "localhost":
        if _host_is_ip(host):
            names.append(x509.IPAddress(ipaddress.ip_address(host)))
        else:
            names.append(x509.DNSName(host))
    # پوشش اتصال محلی — برای تست و پنل‌های پشت tunnel
    names.extend([
        x509.DNSName("localhost"),
        x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
        x509.IPAddress(ipaddress.ip_address("::1")),
    ])
    return tuple(names)


def _read_meta() -> dict:
    try:
        return json.loads(META_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def needs_regeneration(host: str) -> bool:
    if not CERT_PATH.exists() or not KEY_PATH.exists():
        return True
    meta = _read_meta()
    if meta.get("host") != (host or "").strip().lower():
        return True
    try:
        cert = x509.load_pem_x509_certificate(CERT_PATH.read_bytes())
        remaining = cert.not_valid_after_utc - datetime.datetime.now(datetime.timezone.utc)
        return remaining.days < REGENERATE_THRESHOLD
    except Exception:
        return True


def generate_cert(host: str) -> None:
    CERT_DIR.mkdir(parents=True, exist_ok=True)
    key = ec.generate_private_key(ec.SECP256R1())
    now = datetime.datetime.now(datetime.timezone.utc)
    subject = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, (host or "localhost").strip()[:64] or "localhost"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "RVG Gateway"),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)  # self-signed: issuer == subject
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=VALID_DAYS))
        .add_extension(
            x509.SubjectAlternativeName(list(_sans_for(host))),
            critical=False,
        )
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True, key_encipherment=True,
                content_commitment=False, data_encipherment=False,
                key_agreement=True, key_cert_sign=False, crl_sign=False,
                encipher_only=False, decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    tmp_cert, tmp_key = CERT_PATH.with_suffix(".tmp"), KEY_PATH.with_suffix(".tmp")
    tmp_cert.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    tmp_key.write_bytes(key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    ))
    tmp_cert.replace(CERT_PATH)
    tmp_key.replace(KEY_PATH)
    META_PATH.write_text(
        json.dumps({
            "host": (host or "").strip().lower(),
            "created_at": now.isoformat(),
            "valid_days": VALID_DAYS,
        }, ensure_ascii=False),
        encoding="utf-8",
    )
    try:
        KEY_PATH.chmod(0o600)
    except Exception:
        pass


def ensure_panel_cert(host: str) -> tuple[Path, Path]:
    """گواهی معتبر برای `host` برمی‌گرداند — در صورت نیاز می‌سازد/به‌روزرسانی می‌کند."""
    if needs_regeneration(host):
        generate_cert(host)
        logger.info(f"TLS: گواهی self-signed برای «{host or 'localhost'}» ساخته شد ({CERT_PATH})")
    return CERT_PATH, KEY_PATH


def cert_der_base64() -> str:
    """DER گواهی به base64 استاندارد — برای plugin-opts گزینه‌ی certRaw در v2ray-plugin
    (کلاینت‌های shadowsocks نمی‌توانند allowInsecure بگیرند، باید گواهی pin شود)."""
    import base64
    return base64.b64encode(x509.load_pem_x509_certificate(CERT_PATH.read_bytes()).public_bytes(serialization.Encoding.DER)).decode()
