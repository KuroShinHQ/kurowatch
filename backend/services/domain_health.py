"""
SOHBET-147 — Domain Health Checker
Tests all domains in the site table, updates is_dead status.
"""
import asyncio, json, logging, os, re, time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

import httpx

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "domain_health.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("domain_health")


@dataclass
class HealthResult:
    domain: str
    status: str  # OK, DEAD, UNREACHABLE, CLOUDFLARE, TIMEOUT
    status_code: Optional[int] = None
    elapsed_ms: float = 0.0
    error: Optional[str] = None
    sample_url: Optional[str] = None
    content_type: Optional[str] = None
    checked_at: str = field(default_factory=lambda: datetime.now().isoformat())


DOMAIN_TIMEOUT = 15
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
HEADERS = {"User-Agent": UA, "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8"}


async def check_single_url(url: str) -> HealthResult:
    """Test a single URL and return health status. Retry for rate-limited domains."""
    parsed = urlparse(url)
    domain = parsed.netloc.lstrip("www.")
    start = time.time()

    result = HealthResult(domain=domain, sample_url=url[:120])

    async def _do_check() -> HealthResult:
        r2 = HealthResult(domain=domain, sample_url=url[:120])
        try:
            async with httpx.AsyncClient(timeout=DOMAIN_TIMEOUT, follow_redirects=True, headers=HEADERS) as c:
                rr = await c.head(url)
                if rr.status_code == 405:
                    rr = await c.get(url)
                r2.status_code = rr.status_code
                r2.elapsed_ms = round((time.time() - start) * 1000, 1)

                body_lower = (rr.text[:1000] if hasattr(rr, 'text') and rr.text else '').lower()

                if rr.status_code < 400:
                    r2.status = "OK"
                elif "cloudflare" in body_lower or "cf-ray" in rr.headers.get("cf-ray", ""):
                    r2.status = "CLOUDFLARE"
                    r2.error = "Cloudflare challenge detected"
                elif rr.status_code in (404, 410):
                    r2.status = "DEAD"
                    r2.error = f"HTTP {rr.status_code}"
                elif rr.status_code in (403, 503, 520, 521, 525, 526):
                    r2.status = "BLOCKED"
                    r2.error = f"HTTP {rr.status_code}"
                else:
                    r2.status = "DEAD"
                    r2.error = f"HTTP {rr.status_code}"
        except httpx.TimeoutException:
            r2.status = "TIMEOUT"
            r2.error = "Connection timed out"
        except httpx.ConnectError as e:
            if "getaddrinfo" in str(e):
                r2.status = "DNS_FAIL"
            else:
                r2.status = "UNREACHABLE"
            r2.error = str(e)[:60]
        except Exception as e:
            r2.status = "ERROR"
            r2.error = str(e)[:60]
        return r2

    result = await _do_check()

    # Retry: setfilmizle rate-limit 404 → 5sn bekle, tekrar dene
    if result.status in ("DEAD", "BLOCKED") and 'setfilmizle' in domain:
        await asyncio.sleep(5)
        retry = await _do_check()
        if retry.status == "OK":
            return retry

    return result


async def health_check_url(url: str) -> HealthResult:
    """Alias for check_single_url."""
    return await check_single_url(url)


async def check_domain_with_samples(domain: str, sample_urls: list[str]) -> HealthResult:
    """Test a domain by trying multiple sample URLs."""
    best = HealthResult(domain=domain, status="UNTESTED")

    for url in sample_urls[:3]:
        result = await check_single_url(url)
        logger.info(f"  Sample: {url[:80]} → {result.status} ({result.status_code})")
        if result.status == "OK":
            return result
        if result.status == "CLOUDFLARE":
            best = result
        elif best.status == "UNTESTED" or best.status == "ERROR":
            best = result

    return best


async def get_all_domains(db_session):
    """Extract unique domains from site table."""
    from sqlalchemy import text
    result = await db_session.execute(text("""
        SELECT DISTINCT LOWER(REPLACE(REPLACE(REPLACE(
            SUBSTR(site_url, INSTR(site_url, '://') + 3),
            'www.', ''), '/', ''), '?', '')) as domain
        FROM site WHERE site_url IS NOT NULL AND site_url != ''
    """))
    return [row[0] for row in result.fetchall() if row[0]]


async def get_domain_sample_urls(db_session, domain: str) -> list[str]:
    """Get sample URLs for a domain from site and episode tables."""
    from sqlalchemy import text
    urls = []
    result = await db_session.execute(text("""
        SELECT site_url FROM site
        WHERE site_url LIKE :pattern AND site_url IS NOT NULL
        LIMIT 5
    """), {"pattern": f"%{domain}%"})
    urls.extend([row[0] for row in result.fetchall()])

    if len(urls) < 3:
        result = await db_session.execute(text("""
            SELECT url FROM episode
            WHERE url LIKE :pattern AND url IS NOT NULL
            LIMIT 3
        """), {"pattern": f"%{domain}%"})
        urls.extend([row[0] for row in result.fetchall()])

    return urls


async def check_all_domains(db_session, progress_callback=None):
    """Check all domains in the site table."""
    domains = await get_all_domains(db_session)
    logger.info(f"Checking {len(domains)} domains...")
    results = {}

    for idx, domain in enumerate(domains):
        if not domain:
            continue
        samples = await get_domain_sample_urls(db_session, domain)
        # Rate-limit protection for aggressive sites
        if 'setfilmizle' in domain:
            await asyncio.sleep(2)
        if not samples:
            results[domain] = HealthResult(domain=domain, status="NO_SAMPLES")
            continue
        result = await check_domain_with_samples(domain, samples)
        results[domain] = result
        logger.info(f"[{idx+1}/{len(domains)}] {domain}: {result.status}")

        if progress_callback:
            await progress_callback(idx + 1, len(domains), domain, result.status)

    return results


async def update_dead_status(db_session, results: dict[str, HealthResult]):
    """Update site.is_dead based on health check results."""
    from sqlalchemy import text, update
    from backend.models import Site

    updated = 0
    for domain, result in results.items():
        is_dead = 0 if result.status == "OK" else 1
        if result.status in ("CLOUDFLARE", "NO_SAMPLES"):
            continue  # don't mark CF sites as dead, they might work in browser

        stmt = text("""
            UPDATE site SET is_dead = :is_dead
            WHERE site_url LIKE :pattern
        """)
        r = await db_session.execute(stmt, {"is_dead": is_dead, "pattern": f"%{domain}%"})
        updated += r.rowcount

    await db_session.commit()
    logger.info(f"Updated {updated} site records")
    return updated


# CLI entry point
if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else None
    if url:
        result = asyncio.run(check_single_url(url))
        print(json.dumps({
            "domain": result.domain,
            "status": result.status,
            "status_code": result.status_code,
            "elapsed_ms": result.elapsed_ms,
            "error": result.error,
        }, indent=2, ensure_ascii=False))
    else:
        print("Usage: python -m backend.services.domain_health <url>")
