"""
VAPID anahtar yönetimi, abonelik depolama, push gönderimi.
Tek kullanıcı için hafıza dosyası yeterli (DB gereksiz).
"""
import base64
import json
import os
from typing import Optional

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
_SUBS_PATH   = os.path.join(os.path.dirname(__file__), "..", "memory", "push_subscriptions.json")


# ── Config yardımcıları ───────────────────────────────────────────────

def _load_cfg() -> dict:
    if os.path.exists(_CONFIG_PATH):
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cfg(cfg: dict) -> None:
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


# ── VAPID ─────────────────────────────────────────────────────────────

def get_or_create_vapid_keys() -> tuple[str, str]:
    """(public_key_b64url, private_pem_str) döner; yoksa üretir + config.json'a kaydeder."""
    cfg = _load_cfg()
    if cfg.get("vapid_public_key") and cfg.get("vapid_private_key"):
        return cfg["vapid_public_key"], cfg["vapid_private_key"]

    from py_vapid import Vapid01
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

    v = Vapid01()
    v.generate_keys()

    # Tarayıcı için uncompressed point (04 + X + Y) — URL-safe base64url
    raw = v.public_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
    pub_b64 = base64.urlsafe_b64encode(raw).rstrip(b"=").decode()
    priv_pem = v.private_pem().decode()

    cfg["vapid_public_key"]  = pub_b64
    cfg["vapid_private_key"] = priv_pem
    _save_cfg(cfg)
    return pub_b64, priv_pem


# ── Abonelik depolama ─────────────────────────────────────────────────

def load_subs() -> list[dict]:
    if not os.path.exists(_SUBS_PATH):
        return []
    with open(_SUBS_PATH, encoding="utf-8") as f:
        return json.load(f)


def _save_subs(subs: list[dict]) -> None:
    os.makedirs(os.path.dirname(_SUBS_PATH), exist_ok=True)
    with open(_SUBS_PATH, "w", encoding="utf-8") as f:
        json.dump(subs, f, indent=2, ensure_ascii=False)


def add_subscription(sub: dict) -> int:
    subs = load_subs()
    subs = [s for s in subs if s.get("endpoint") != sub.get("endpoint")]
    subs.append(sub)
    _save_subs(subs)
    return len(subs)


def remove_subscription(endpoint: str) -> bool:
    subs = load_subs()
    new  = [s for s in subs if s.get("endpoint") != endpoint]
    if len(new) == len(subs):
        return False
    _save_subs(new)
    return True


# ── Push gönderimi ────────────────────────────────────────────────────

def send_push(
    title: str,
    body: str,
    url: str = "/",
    icon: str = "/icons/icon-192.png",
) -> dict:
    """Tüm abonelere push gönder. {sent, failed, total} döner."""
    from pywebpush import webpush, WebPushException

    _, priv_pem = get_or_create_vapid_keys()
    subs = load_subs()
    if not subs:
        return {"sent": 0, "failed": 0, "total": 0}

    payload = json.dumps({"title": title, "body": body, "url": url, "icon": icon})
    dead: list[str] = []
    sent = failed = 0

    for sub in subs:
        try:
            webpush(
                subscription_info=sub,
                data=payload,
                vapid_private_key=priv_pem,
                vapid_claims={"sub": "mailto:kurowatch@localhost"},
                ttl=86400,
            )
            sent += 1
        except WebPushException as exc:
            resp = exc.response
            if resp is not None and resp.status_code in (404, 410):
                dead.append(sub.get("endpoint", ""))
            failed += 1
        except Exception:
            failed += 1

    if dead:
        _save_subs([s for s in load_subs() if s.get("endpoint") not in dead])

    return {"sent": sent, "failed": failed, "total": len(subs)}
