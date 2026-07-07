"""
fitgirl.py — FitGirl Repacks scraper (lightweight HTTP only, no Playwright).
Search: GET https://fitgirl-repacks.site/?s=game_name
Parse: lxml.html with strict sanitization, extract magnet/torrent/repack_size.
"""
import re
import json
import logging
from typing import Optional
from urllib.parse import urljoin, urlparse
from html import unescape

import httpx

logger = logging.getLogger(__name__)

_BASE_URL = "https://fitgirl-repacks.site"
_SEARCH_URL = f"{_BASE_URL}/?s="

# Timeouts
_TIMEOUT_SEARCH = 20
_TIMEOUT_DETAIL = 25

# Minimum HTML length to consider a page valid (CF challenge returns ~500 bytes)
_MIN_HTML_LENGTH = 2000

# User-Agent to avoid basic blocks
_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/132.0.0.0 Safari/537.36"
)


# ── Security: HTML Sanitizer ──────────────────────────────────────────

def _sanitize_text(text: str) -> str:
    """Strip HTML entities, control chars, excessive whitespace."""
    t = unescape(text)
    t = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', t)
    return ' '.join(t.split()).strip()


def _sanitize_url(url: str, base: str = _BASE_URL) -> Optional[str]:
    """Validate and absolutize a URL. Return None if dangerous."""
    url = url.strip()
    if not url:
        return None
    # Magnet URIs
    if url.startswith("magnet:?xt="):
        # Basic magnet validation: must have xt parameter
        if "xt=urn" in url:
            return url
        logger.warning("fitgirl: invalid magnet URI (no xt=urn)")
        return None
    # Torrent / page URLs
    if not url.startswith("http://") and not url.startswith("https://"):
        url = urljoin(base, url)
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        logger.warning("fitgirl: non-http URL rejected: %s", url[:60])
        return None
    # No IP-based URLs (security: avoid local network)
    host = parsed.hostname or ""
    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", host):
        logger.warning("fitgirl: IP-based URL rejected: %s", url[:60])
        return None
    # Strip tracking/fingerprint params
    return url.split("?")[0] if ".torrent" in url else url


# ── HTTP Client ───────────────────────────────────────────────────────

async def _fetch(url: str, timeout: int = _TIMEOUT_SEARCH) -> Optional[str]:
    """Fetch HTML via httpx with browser-like headers. Returns None on CF block / error."""
    headers = {
        "User-Agent": _UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": _BASE_URL,
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
    }
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            text = resp.text
            # CF challenge detection
            if resp.status_code in (403, 503) or len(text) < _MIN_HTML_LENGTH:
                title_m = re.search(r'<title[^>]*>(.*?)</title>', text, re.IGNORECASE | re.DOTALL)
                title = title_m.group(1) if title_m else "no title"
                if "just a moment" in title.lower() or "challenge" in title.lower():
                    logger.warning("fitgirl: CF challenge at %s (title=%s, len=%d)", url[:60], title, len(text))
                    return None
                logger.warning("fitgirl: HTTP %d at %s (title=%s, len=%d)", resp.status_code, url[:60], title, len(text))
                return None
            logger.info("fitgirl: fetched %s (HTTP %d, %d bytes)", url[:60], resp.status_code, len(text))
            return text
    except httpx.TimeoutException:
        logger.warning("fitgirl: timeout fetching %s", url[:60])
        return None
    except Exception as exc:
        logger.warning("fitgirl: fetch error %s: %s", url[:60], exc)
        return None


# ── Search: Parse search results ──────────────────────────────────────

def _parse_search_results(html: str) -> list[dict]:
    """
    Parse FitGirl search results page HTML.
    Returns list of {title, url, repack_size, year}.
    Uses lxml for safe structured parsing.
    """
    results: list[dict] = []
    try:
        from lxml import html as lh
        tree = lh.fromstring(html)
        lh.make_links_absolute(tree, base_url=_BASE_URL)
    except Exception as exc:
        logger.error("fitgirl: lxml parse error: %s", exc)
        # Fallback: regex-based extraction (with sanitization)
        return _parse_search_results_regex(html)

    # FitGirl uses <article> or <div class="post"> or <h2> entry-title
    # Common WP theme: each result is an <article> with class
    articles = tree.cssselect("article") or tree.cssselect("div.post") or tree.cssselect("div.entry")
    if not articles:
        # Try h2.entry-title > a pattern (default WP search)
        titles = tree.cssselect("h2.entry-title a") or tree.cssselect("h2 a")
        for a_tag in titles:
            title = _sanitize_text(a_tag.text_content())
            href = _sanitize_url(a_tag.get("href", ""))
            if not title or not href:
                continue
            results.append({"title": title, "url": href, "repack_size": None, "year": None})
        return _dedupe_search(results)

    for art in articles:
        # Title
        title_el = (
            art.cssselect("h2.entry-title a") or
            art.cssselect("h2 a") or
            art.cssselect(".entry-title a") or
            art.cssselect("a")
        )
        if not title_el:
            continue
        title = _sanitize_text(title_el[0].text_content())
        url = _sanitize_url(title_el[0].get("href", ""))
        if not title or not url:
            continue

        # Repack size: look for "Repack Size" text in the article body
        size = None
        body_text = _sanitize_text(art.text_content()) if art.text_content() else ""
        size_m = re.search(
            r'(?:repack\s*size|size|repack)[:\s]*([\d.]+[\s]*(?:GB|MB|GiB|MiB))',
            body_text, re.IGNORECASE
        )
        if size_m:
            size = size_m.group(1).strip()

        # Year: look for "(2024)" or similar in title or snippet
        yr_m = re.search(r'[(\[]?(19\d\d|20[0-3]\d)[)\]]?', title)
        year = int(yr_m.group(1)) if yr_m else None

        results.append({"title": title, "url": url, "repack_size": size, "year": year})

    return _dedupe_search(results)


def _parse_search_results_regex(html: str) -> list[dict]:
    """Fallback: regex-based search result parsing with sanitization."""
    results: list[dict] = []
    # Match <a href="..." class="...">Title</a> patterns in entry-title context
    pattern = re.compile(
        r'<h2[^>]*class="[^"]*entry-title[^"]*"[^>]*>.*?'
        r'<a\s+href="([^"]+)"[^>]*>(.*?)</a>',
        re.IGNORECASE | re.DOTALL
    )
    for m in pattern.finditer(html):
        url = _sanitize_url(m.group(1))
        title = _sanitize_text(m.group(2))
        if not title or not url:
            continue
        yr_m = re.search(r'[(\[]?(19\d\d|20[0-3]\d)[)\]]?', title)
        year = int(yr_m.group(1)) if yr_m else None
        results.append({"title": title, "url": url, "repack_size": None, "year": year})
    return _dedupe_search(results)


def _dedupe_search(items: list[dict]) -> list[dict]:
    """Remove duplicate results by URL."""
    seen: set[str] = set()
    out: list[dict] = []
    for it in items:
        if it["url"] not in seen:
            seen.add(it["url"])
            out.append(it)
    return out


# ── Detail: Parse single post page ────────────────────────────────────

def _parse_detail_page(html: str, source_url: str) -> dict:
    """
    Parse a FitGirl post page for magnet/torrent/download info.
    Returns dict with: magnet, torrent_url, repack_size, title, downloads[]
    """
    result: dict = {
        "magnet": None,
        "torrent_url": None,
        "repack_size": None,
        "title": None,
        "downloads": [],
    }

    try:
        from lxml import html as lh
        tree = lh.fromstring(html)
    except Exception:
        return _parse_detail_page_regex(html)

    # Title
    title_el = tree.cssselect("h1.entry-title") or tree.cssselect("h1") or tree.cssselect("title")
    if title_el:
        result["title"] = _sanitize_text(title_el[0].text_content())

    # Magnet links
    for a in tree.cssselect("a[href^='magnet:']"):
        magnet = _sanitize_url(a.get("href", ""))
        if magnet:
            result["magnet"] = magnet
            result["downloads"].append({"type": "magnet", "url": magnet})

    # Torrent links
    found_torrents: set[str] = set()
    for a in tree.cssselect("a[href$='.torrent']") or tree.cssselect("a[href*='.torrent']"):
        url = _sanitize_url(a.get("href", ""), _BASE_URL)
        if url and url not in found_torrents:
            found_torrents.add(url)
            result["downloads"].append({"type": "torrent", "url": url})
            if not result["torrent_url"]:
                result["torrent_url"] = url

    # Repack size: look in post body text
    body_el = tree.cssselect("div.entry-content") or tree.cssselect("div.post-content") or tree.cssselect("article")
    if body_el:
        body_text = _sanitize_text(body_el[0].text_content())
        size_m = re.search(
            r'(?:repack\s*size|size|repack)[:\s]*([\d.]+[\s]*(?:GB|MB|GiB|MiB))',
            body_text, re.IGNORECASE
        )
        if size_m:
            result["repack_size"] = size_m.group(1).strip()

    return result


def _parse_detail_page_regex(html: str) -> dict:
    """Fallback regex-based detail parsing with sanitization."""
    result: dict = {"magnet": None, "torrent_url": None, "repack_size": None, "title": None, "downloads": []}

    # Title
    tm = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.IGNORECASE | re.DOTALL)
    if tm:
        result["title"] = _sanitize_text(tm.group(1))

    # Magnet
    mm = re.search(r'(magnet:\?xt=urn:[a-zA-Z0-9:%_&;=+.\-/]+)', html)
    if mm:
        magnet = _sanitize_url(mm.group(1))
        if magnet:
            result["magnet"] = magnet
            result["downloads"].append({"type": "magnet", "url": magnet})

    # Torrent
    for tm2 in re.finditer(r'href="([^"]+\.torrent[^"]*)"', html, re.IGNORECASE):
        url = _sanitize_url(tm2.group(1), _BASE_URL)
        if url:
            if not result["torrent_url"]:
                result["torrent_url"] = url
            result["downloads"].append({"type": "torrent", "url": url})

    # Repack size
    sm = re.search(
        r'(?:repack\s*size|size|repack)[:\s]*([\d.]+[\s]*(?:GB|MB|GiB|MiB))',
        html, re.IGNORECASE
    )
    if sm:
        result["repack_size"] = sm.group(1).strip()

    return result


# ── Public API ────────────────────────────────────────────────────────

async def search(query: str) -> list[dict]:
    """
    Search FitGirl for a game. Returns list of {title, url, repack_size, year}.
    Pure HTTP, no browser automation. Returns empty list on CF block / error.
    """
    from urllib.parse import quote
    search_url = _SEARCH_URL + quote(query)
    logger.info("fitgirl: searching %s", search_url[:80])

    html = await _fetch(search_url)
    if not html:
        logger.warning("fitgirl: search returned no HTML (CF block or timeout)")
        return []

    results = _parse_search_results(html)
    logger.info("fitgirl: search found %d results for '%s'", len(results), query[:50])
    return results


async def get_detail(url: str) -> dict:
    """
    Fetch a FitGirl post page and extract download info.
    Returns {magnet, torrent_url, repack_size, title, downloads[]}.
    """
    resolved = _sanitize_url(url)
    if not resolved:
        logger.warning("fitgirl: invalid detail URL: %s", url[:60])
        return {"magnet": None, "torrent_url": None, "repack_size": None, "title": None, "downloads": []}

    logger.info("fitgirl: fetching detail %s", resolved[:80])
    html = await _fetch(resolved, timeout=_TIMEOUT_DETAIL)
    if not html:
        logger.warning("fitgirl: detail page returned no HTML")
        return {"magnet": None, "torrent_url": None, "repack_size": None, "title": None, "downloads": []}

    return _parse_detail_page(html, resolved)
