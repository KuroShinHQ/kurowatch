"""
Domain pool + health check for movie/series sites.
Domains change frequently; this module finds the active domain.
Includes dynamic domain sniffer for sites with rotating domains.
"""
import json
import logging
from pathlib import Path
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

_SOURCES_PATH = Path(__file__).parent.parent.parent / "movie_series_sources.json"
_active_cache: dict[str, Optional[str]] = {}  # site_name → active_domain

_DYNAMIC_TLDS = (
    ".com", ".net", ".org", ".tv", ".live", ".vip", ".info",
    ".xyz", ".co", ".io", ".gg", ".ws", ".me", ".love", ".pro",
    ".now", ".art", ".name",
)

_DYNAMIC_NUMERALS = (1, 2, 3, 4, 5)
_DYNAMIC_TLD_FOR_NUM = (".com", ".net")


def _load_sources() -> dict:
    if _SOURCES_PATH.exists():
        try:
            return json.loads(_SOURCES_PATH.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error("sources.json yuklenemedi: %s", e)
    return {}


def get_source_config(site_name: str) -> Optional[dict]:
    sources = _load_sources()
    return sources.get(site_name)


async def _sniff_domain(site_name: str) -> Optional[str]:
    """Try common TLD patterns + numeral suffixes to discover current domain."""
    logger.info("Sniffer basliyor: %s", site_name)
    candidates: list[str] = []

    base = site_name.lower().replace("www.", "")
    # Strip trailing number (e.g. "sezonlukdizi1" → "sezonlukdizi")
    import re
    base_stripped = re.sub(r"\d+$", "", base)

    # 1. Base name + common TLDs
    for tld in _DYNAMIC_TLDS:
        candidates.append(f"{base_stripped}{tld}")

    # 2. Base name + number suffix + TLD
    for num in _DYNAMIC_NUMERALS:
        for tld in _DYNAMIC_TLD_FOR_NUM:
            candidates.append(f"{base_stripped}{num}{tld}")

    # 3. Also try with www. prefix for first few
    www_candidates = [f"www.{c}" for c in candidates[:20]]
    candidates = www_candidates + candidates

    seen: set[str] = set()
    async with httpx.AsyncClient(timeout=6, follow_redirects=True) as client:
        for domain in candidates:
            if domain in seen:
                continue
            seen.add(domain)
            url = f"https://{domain}"
            try:
                resp = await client.head(url)
                if resp.status_code < 400:
                    logger.info("Sniffer buldu: %s → %s (HTTP %d)", site_name, domain, resp.status_code)
                    return domain
            except Exception:
                pass

    logger.warning("Sniffer bulamadi: %s (%d domain denendi)", site_name, len(seen))
    return None


def _save_domain_to_sources(site_name: str, domain: str):
    """Discovered domain'i JSON config'e ekle."""
    try:
        if _SOURCES_PATH.exists():
            data = json.loads(_SOURCES_PATH.read_text(encoding="utf-8"))
        else:
            data = {}
        if site_name in data:
            domains = data[site_name].get("domains", [])
            if domain not in domains:
                domains.insert(0, domain)
                data[site_name]["domains"] = domains
                _SOURCES_PATH.write_text(
                    json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
                )
                logger.info("JSON güncellendi: %s → %s eklendi", site_name, domain)
    except Exception as e:
        logger.error("JSON güncellenemedi: %s", e)


async def get_active_domain(site_name: str, force_refresh: bool = False, force_sniff: bool = False) -> Optional[str]:
    if not force_refresh and not force_sniff and site_name in _active_cache:
        cached = _active_cache[site_name]
        if cached:
            logger.debug("Domain cache: %s → %s", site_name, cached)
            return cached
        if not force_sniff:
            return None

    config = get_source_config(site_name)
    if not config:
        if force_sniff:
            return await _sniff_domain(site_name)
        logger.warning("Kaynak bulunamadi: %s", site_name)
        return None

    domains = config.get("domains", [])
    for domain in domains:
        url = f"https://{domain}"
        try:
            async with httpx.AsyncClient(timeout=8, follow_redirects=True) as c:
                resp = await c.head(url)
                if resp.status_code < 400:
                    logger.info("Aktif domain: %s → %s (HTTP %d)", site_name, domain, resp.status_code)
                    _active_cache[site_name] = domain
                    return domain
                logger.debug("Domain pasif: %s (HTTP %d)", domain, resp.status_code)
        except Exception as e:
            logger.debug("Domain erisilemez: %s (%s)", domain, e)

    # Static pool exhausted — try dynamic sniffer
    if not domains or force_sniff:
        discovered = await _sniff_domain(site_name)
        if discovered:
            _active_cache[site_name] = discovered
            _save_domain_to_sources(site_name, discovered)
            return discovered

    logger.warning("Aktif domain bulunamadi: %s (%d domain denendi)", site_name, len(domains))
    _active_cache[site_name] = None
    return None


async def get_active_url(site_name: str, path: str = "", force_refresh: bool = False) -> Optional[str]:
    domain = await get_active_domain(site_name, force_refresh)
    if not domain:
        return None
    return f"https://{domain}{path}"
