"""
Domain pool + health check for movie/series sites.
Domains change frequently; this module finds the active domain.
"""
import json
import logging
from pathlib import Path
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

_SOURCES_PATH = Path(__file__).parent.parent.parent / "movie_series_sources.json"
_active_cache: dict[str, Optional[str]] = {}  # site_name → active_domain


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


async def get_active_domain(site_name: str, force_refresh: bool = False) -> Optional[str]:
    if not force_refresh and site_name in _active_cache:
        cached = _active_cache[site_name]
        if cached:
            logger.debug("Domain cache: %s → %s", site_name, cached)
            return cached
        return None

    config = get_source_config(site_name)
    if not config:
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

    logger.warning("Aktif domain bulunamadi: %s (%d domain denendi)", site_name, len(domains))
    _active_cache[site_name] = None
    return None


async def get_active_url(site_name: str, path: str = "", force_refresh: bool = False) -> Optional[str]:
    domain = await get_active_domain(site_name, force_refresh)
    if not domain:
        return None
    return f"https://{domain}{path}"
