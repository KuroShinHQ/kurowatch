"""
SOHBET-147 — Test Runner
Tests all URLs in the database, reports pass/fail counts per domain/content-type.
"""
import asyncio, json, logging, os, time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

import httpx

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "test_runner.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("test_runner")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
HEADERS = {"User-Agent": UA, "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8"}
TIMEOUT = 15

SAMPLE_SIZE = 3  # sample URLs per content


@dataclass
class URLTestResult:
    url: str
    status_code: Optional[int] = None
    status: str = "UNKNOWN"  # OK, DEAD, CLOUDFLARE, BLOCKED, TIMEOUT, DNS_FAIL, ERROR
    elapsed_ms: float = 0.0
    error: Optional[str] = None
    content_type: Optional[str] = None
    domain: str = ""
    site_name: str = ""


@dataclass
class DomainStats:
    total: int = 0
    ok: int = 0
    dead: int = 0
    cloudflare: int = 0
    blocked: int = 0
    timeout: int = 0
    dns_fail: int = 0
    error: int = 0


@dataclass
class TestReport:
    started_at: str = ""
    finished_at: str = ""
    elapsed_seconds: float = 0.0
    total_urls: int = 0
    total_ok: int = 0
    total_dead: int = 0
    total_cloudflare: int = 0
    ok_pct: float = 0.0
    by_domain: dict[str, DomainStats] = field(default_factory=dict)
    by_content_type: dict[str, DomainStats] = field(default_factory=dict)
    sample_results: list[URLTestResult] = field(default_factory=list)


async def test_url(url: str) -> URLTestResult:
    """Test a single URL and return result."""
    parsed = urlparse(url)
    domain = parsed.netloc.lstrip("www.")
    result = URLTestResult(url=url[:200], domain=domain)
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True, headers=HEADERS) as c:
            r = await c.head(url)
            if r.status_code == 405:
                r = await c.get(url)
            result.status_code = r.status_code
            result.elapsed_ms = round((time.time() - start) * 1000, 1)
            body = (r.text[:500] if hasattr(r, 'text') and r.text else '').lower()
            if r.status_code < 400:
                result.status = "OK"
            elif "cloudflare" in body or "cf-ray" in (r.headers.get("cf-ray", "")):
                result.status = "CLOUDFLARE"
            elif r.status_code in (404, 410):
                result.status = "DEAD"
            else:
                result.status = "DEAD"
                result.error = f"HTTP {r.status_code}"
    except httpx.TimeoutException:
        result.status = "TIMEOUT"
        result.error = "timeout"
    except httpx.ConnectError as e:
        if "getaddrinfo" in str(e):
            result.status = "DNS_FAIL"
        else:
            result.status = "UNREACHABLE"
        result.error = str(e)[:60]
    except Exception as e:
        result.status = "ERROR"
        result.error = str(e)[:60]
    return result


async def run_full_test(db_session, sample_size: int = SAMPLE_SIZE,
                        include_ok_domains: bool = False,
                        specific_domain: Optional[str] = None) -> TestReport:
    """Test all URLs in the database and produce a report."""
    from sqlalchemy import text

    report = TestReport()
    report.started_at = datetime.now().isoformat()

    # Get unique content with site info
    query = """
        SELECT DISTINCT c.id, c.title, c.type, s.site_name, s.site_url
        FROM content c
        JOIN site s ON s.content_id = c.id
        WHERE s.site_url IS NOT NULL AND s.site_url != ''
    """
    if specific_domain:
        query += f" AND s.site_url LIKE '%{specific_domain}%'"

    result = await db_session.execute(text(query))
    content_sites = result.fetchall()

    # Group by content
    content_map = defaultdict(list)
    for row in content_sites:
        cid, title, ctype, sname, surl = row
        content_map[cid].append({
            "title": title, "type": ctype, "site_name": sname, "site_url": surl
        })

    all_results: list[URLTestResult] = []
    by_domain: dict[str, DomainStats] = defaultdict(DomainStats)
    by_content_type: dict[str, DomainStats] = defaultdict(DomainStats)

    for cid, sites in content_map.items():
        ctype = sites[0]["type"] or "unknown"
        for site in sites[:sample_size]:
            r = await test_url(site["site_url"])
            r.content_type = ctype
            r.site_name = site["site_name"]
            all_results.append(r)

            ds = by_domain[r.domain]
            ds.total += 1
            getattr(ds, r.status.lower().replace("-", "_"), None)
            if r.status == "OK":
                ds.ok += 1
            elif r.status == "CLOUDFLARE":
                ds.cloudflare += 1
            elif r.status in ("DEAD", "HTTP_404", "HTTP_410"):
                ds.dead += 1
            elif r.status == "TIMEOUT":
                ds.timeout += 1
            elif r.status == "DNS_FAIL":
                ds.dns_fail += 1
            elif r.status == "BLOCKED":
                ds.blocked += 1
            else:
                ds.error += 1

            ct = by_content_type[ctype]
            ct.total += 1
            if r.status == "OK":
                ct.ok += 1
            else:
                getattr(ct, r.status.lower() + "_count", None)
                ct.dead += 1

    report.finished_at = datetime.now().isoformat()
    report.elapsed_seconds = round(
        (datetime.fromisoformat(report.finished_at) - datetime.fromisoformat(report.started_at)).total_seconds(), 1
    )
    report.total_urls = len(all_results)
    report.total_ok = sum(1 for r in all_results if r.status == "OK")
    report.total_dead = sum(1 for r in all_results if r.status != "OK")
    report.total_cloudflare = sum(1 for r in all_results if r.status == "CLOUDFLARE")
    report.ok_pct = round(report.total_ok / report.total_urls * 100, 1) if report.total_urls else 0.0
    report.by_domain = dict(by_domain)
    report.by_content_type = dict(by_content_type)
    report.sample_results = all_results[:50]  # keep first 50 for detail

    logger.info(f"Test complete: {report.total_urls} URLs, {report.ok_pct}% OK")
    return report


async def test_domain_update(db_session, domain: str, new_domain: str) -> TestReport:
    """Test a specific domain update by checking if new URLs work."""
    from sqlalchemy import text
    report = TestReport()
    report.started_at = datetime.now().isoformat()

    # Get sample URLs with the new domain
    result = await db_session.execute(text("""
        SELECT c.id, c.title, c.type, s.site_name, s.site_url
        FROM content c
        JOIN site s ON s.content_id = c.id
        WHERE s.site_url LIKE :pattern
        LIMIT 30
    """), {"pattern": f"%{new_domain}%"})
    rows = result.fetchall()

    by_domain: dict[str, DomainStats] = defaultdict(DomainStats)
    results = []
    for row in rows:
        cid, title, ctype, sname, surl = row
        r = await test_url(surl)
        r.content_type = ctype
        r.site_name = sname
        results.append(r)
        ds = by_domain[r.domain]
        ds.total += 1
        if r.status == "OK":
            ds.ok += 1
        else:
            ds.dead += 1

    report.finished_at = datetime.now().isoformat()
    report.total_urls = len(results)
    report.total_ok = sum(1 for r in results if r.status == "OK")
    report.total_dead = report.total_urls - report.total_ok
    report.ok_pct = round(report.total_ok / report.total_urls * 100, 1) if report.total_urls else 0.0
    report.by_domain = dict(by_domain)
    report.sample_results = results

    logger.info(f"Domain update test: {new_domain} → {report.ok_pct}% OK ({report.total_ok}/{report.total_urls})")
    return report


def print_report(report: TestReport) -> str:
    """Format report as a readable string."""
    lines = [f"=== Test Report ==="]
    lines.append(f"Started: {report.started_at}")
    lines.append(f"Duration: {report.elapsed_seconds}s")
    lines.append(f"Total URLs tested: {report.total_urls}")
    lines.append(f"OK: {report.total_ok} ({report.ok_pct}%)")
    lines.append(f"Dead/Error: {report.total_dead}")
    lines.append(f"Cloudflare: {report.total_cloudflare}")
    lines.append("")

    lines.append(f"{'Domain':<25} {'Total':>6} {'OK':>6} {'Dead':>6} {'CF':>6}")
    lines.append("-" * 55)
    for domain, stats in sorted(report.by_domain.items(), key=lambda x: -x[1].total):
        if stats.total > 0:
            lines.append(f"{domain:<25} {stats.total:>6} {stats.ok:>6} {stats.dead:>6} {stats.cloudflare:>6}")

    lines.append("")
    lines.append(f"{'Content Type':<15} {'Total':>6} {'OK':>6} {'%':>6}")
    lines.append("-" * 35)
    for ctype, stats in sorted(report.by_content_type.items(), key=lambda x: -x[1].total):
        pct = round(stats.ok / stats.total * 100, 1) if stats.total else 0
        lines.append(f"{ctype:<15} {stats.total:>6} {stats.ok:>6} {pct:>6}")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "url":
        url = sys.argv[2]
        result = asyncio.run(test_url(url))
        print(json.dumps({
            "url": result.url, "status": result.status,
            "status_code": result.status_code, "elapsed_ms": result.elapsed_ms,
            "domain": result.domain,
        }, indent=2, ensure_ascii=False))
    else:
        print("Usage: python -m backend.services.test_runner url <url>")
