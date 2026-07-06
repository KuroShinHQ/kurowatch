import asyncio
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from urllib.parse import urlparse

import httpx


PING_RESULT = Enum("PING_RESULT", [
    "OK",           # HTTP 200/206 — erişilebilir
    "CHALLENGE",    # HTTP 202 — kabul edildi ama JS PoW/CF challenge gerekli
    "CF_BLOCKED",   # HTTP 403 + Server: cloudflare
    "SITE_YOK",     # HTTP 404 — sayfa mevcut değil
    "OFFLINE",      # HTTP 502/503 — sunucu hatası
    "SSL_HATASI",   # HTTP 525 — Cloudflare SSL handshake
    "DNS_FAIL",     # DNS çözümlemesi başarısız
    "TIMEOUT",      # 5sn içinde yanıt yok
    "CONN_REFUSED", # Bağlantı reddedildi
    "PARSE_HATASI", # HTML alındı ama beklenen içerik yok
    "HATA",         # Diğer hatalar
])


@dataclass
class PingResult:
    status: str           # PING_RESULT adı
    code: int             # HTTP status code (0 = ulaşılamadı)
    detail: str           # Kısa açıklama
    headers: dict         # Response headers (ilk 10)
    body_preview: str     # İlk 200 karakter
    host: str             # Domain
    elapsed_ms: int       # Geçen süre

    def is_ok(self) -> bool:
        return self.status in ("OK", "CHALLENGE")

    def is_dead(self) -> bool:
        return self.status in ("SITE_YOK", "OFFLINE", "SSL_HATASI",
                               "DNS_FAIL", "CONN_REFUSED")

    def is_blocked(self) -> bool:
        return self.status == "CF_BLOCKED"

    def is_error(self) -> bool:
        return self.status in ("TIMEOUT", "PARSE_HATASI", "HATA")


_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.5",
    "Range": "bytes=0-4096",
}


async def http_ping(url: str, timeout: float = 5.0) -> PingResult:
    host = urlparse(url).netloc.lstrip("www.")
    t0 = asyncio.get_event_loop().time()

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True,
                                     headers=_HEADERS) as client:
            r = await client.get(url)
            elapsed = int((asyncio.get_event_loop().time() - t0) * 1000)
            code = r.status_code
            preview = r.text[:200].replace("\n", " ").strip()
            headers = dict(list(r.headers.items())[:10])
            server = r.headers.get("server", "").lower()

            if code in (200, 206):
                return PingResult("OK", code, f"HTTP {code}", headers,
                                  preview, host, elapsed)

            if code == 202:
                return PingResult("CHALLENGE", code,
                                  "HTTP 202 — JS PoW/CF challenge bekleniyor",
                                  headers, preview, host, elapsed)

            if code == 403 and ("cloudflare" in server or "cf" in server):
                return PingResult("CF_BLOCKED", code,
                                  "HTTP 403 Cloudflare korumalı", headers,
                                  preview, host, elapsed)

            if code == 403:
                body_lower = preview.lower()
                if "cloudflare" in body_lower or "cf-ray" in body_lower:
                    return PingResult("CF_BLOCKED", code,
                                      "HTTP 403 muhtemelen CF", headers,
                                      preview, host, elapsed)
                return PingResult("CF_BLOCKED", code,
                                  f"HTTP 403 ({server or 'bilinmiyor'})",
                                  headers, preview, host, elapsed)

            if code == 404:
                return PingResult("SITE_YOK", code, "HTTP 404 sayfa mevcut değil",
                                  headers, preview, host, elapsed)

            if code in (502, 503):
                return PingResult("OFFLINE", code, f"HTTP {code} sunucu hatası",
                                  headers, preview, host, elapsed)

            if code == 525:
                return PingResult("SSL_HATASI", code,
                                  "HTTP 525 SSL handshake failed",
                                  headers, preview, host, elapsed)

            return PingResult("HATA", code, f"HTTP {code} ({server})",
                              headers, preview, host, elapsed)

    except httpx.ConnectError as exc:
        elapsed = int((asyncio.get_event_loop().time() - t0) * 1000)
        msg = str(exc).lower()
        if "connection refused" in msg:
            return PingResult("CONN_REFUSED", 0, f"Bağlantı reddedildi: {exc}",
                              {}, "", host, elapsed)
        if "dns" in msg or "resolve" in msg:
            return PingResult("DNS_FAIL", 0, f"DNS çözümlemesi başarısız: {exc}",
                              {}, "", host, elapsed)
        return PingResult("HATA", 0, str(exc)[:120], {}, "", host, elapsed)

    except httpx.TimeoutException as exc:
        elapsed = int((asyncio.get_event_loop().time() - t0) * 1000)
        return PingResult("TIMEOUT", 0, f"{timeout}sn içinde yanıt yok",
                          {}, "", host, elapsed)

    except Exception as exc:
        elapsed = int((asyncio.get_event_loop().time() - t0) * 1000)
        return PingResult("HATA", 0, str(exc)[:120], {}, "", host, elapsed)


async def quick_ping(url: str, timeout: float = 5.0) -> bool:
    """Sadece OK/DEAD döndür. Detay gerekmezse kullan."""
    r = await http_ping(url, timeout)
    return r.is_ok()


def slugify(title: str) -> str:
    s = title.lower().strip()
    tr_map = str.maketrans("şçğğıöüıŞÇĞĞİÖÜİ", "scggioiuSCGGIOUI")
    s = s.translate(tr_map)
    s = re.sub(r"[^a-z0-9\- ]", "", s)
    s = re.sub(r"\s+", "-", s).strip("-")
    s = re.sub(r"-+", "-", s)
    return s


def construct_tranimaci_url(title: str, ep: int = 1) -> str:
    slug = slugify(title)
    return f"https://tranimaci.com/video/{slug}-{ep}-bolum"


def construct_madara_url(base_site: str, title: str, ep: int = 1) -> str:
    slug = slugify(title)
    base = base_site.rstrip("/")
    return f"{base}/manga/{slug}/bolum-{ep}/"
