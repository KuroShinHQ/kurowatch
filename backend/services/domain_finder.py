"""
SOHBET-147 — Alternative Domain Finder
Searches for working alternative domains for dead sites.
"""
import asyncio, json, logging, os, re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

import httpx

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "domain_finder.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("domain_finder")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
HEADERS = {"User-Agent": UA, "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8"}

# Known working alternatives (hardcoded fallback)
KNOWN_ALTERNATIVES = {
    "hdfilmcehennemi.now": ["www.hdfilmcehennemi.nl", "www.hdfilmcehennemi.com",
                            "www.hdfilmcehennemi.ltd", "www.hdfilmcehennemi.sh"],
    "hdfilmcehennemi.nl": ["www.hdfilmcehennemi.now", "www.hdfilmcehennemi.com"],
    "ragnarscans.com": ["ragnarscans.net"],
    "ragnarscans.net": ["ragnarscans.com"],
    "mangatr.com": ["mangatr.app", "mangatr.me"],
    "mangatr.net": ["mangatr.app", "mangatr.me"],
    "manga-sehri.com": ["mangasehri.net"],
    "mangasehri.com": ["mangasehri.net"],
    "mangaokutr.com": ["mangaokutr.net"],
    "turkanime.tv": ["tranimaci.com", "tranimeizle.top"],
    "turkanime.com.tr": ["tranimaci.com", "tranimeizle.top"],
    "tranimaci.com": ["tranimeizle.top", "tranimeizle.co"],
    "tranimeizle.top": ["tranimaci.com", "tranimeizle.co"],
    "asurascans.com.tr": ["asurascans.net"],
    "setfilmizle.uk": ["setfilmizle.vip", "setfilmizle.com"],
    "dizibox.so": ["dizibox.me", "dizibox.vip"],
    "dizipod.com": ["dizipod.net", "dizipod.live"],
    "yabancidizi.pro": ["yabancidizi.pw", "yabancidizi.co"],
    "hayalistic.com.tr": ["hayalistic.net"],
    "merlintoon.com": ["merlintoon.net"],
    "mangatepesi.com": ["mangatepesi.net"],
    "monomanga.com.tr": ["monomanga.net"],
    "ruyamanga.com": ["ruyamanga.net"],
}

# Site name → possible search keywords
SITE_SEARCH_KEYWORDS = {
    "hdfilmcehennemi": "hdfilmcehennemi yeni domain adresi 2026",
    "hdfilmcehennemi.now": "hdfilmcehennemi yeni site adresi",
    "setfilmizle": "setfilmizle yeni domain 2026",
    "ragnarscans": "ragnarscans yeni adres",
    "asurascans": "asurascans yeni domain",
    "dizipod": "dizipod yeni adres",
    "dizibox": "dizibox yeni domain",
    "manga-sehri": "manga şehri yeni adres",
    "turkanime": "turkanime yeni domain",
    "tranimaci": "tranimaci yeni adres",
    "yabancidizi": "yabancı dizi yeni site",
    "mangatr": "mangatr yeni adres",
    "hayalistic": "hayalistic yeni domain",
    "merlintoon": "merlintoon yeni adres",
}


@dataclass
class DomainCandidate:
    domain: str
    source: str  # duckduckgo, google, known, search
    status: str = "UNTESTED"
    status_code: Optional[int] = None
    elapsed_ms: float = 0.0
    content_match: bool = False
    error: Optional[str] = None


async def test_domain(d: str, sample_path: str = "/") -> DomainCandidate:
    """Test if a domain is reachable and returns content."""
    url = f"https://www.{d}{sample_path}" if not d.startswith("http") else d
    clean_domain = urlparse(url).netloc.lstrip("www.")

    cand = DomainCandidate(domain=clean_domain, source="test")
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True, headers=HEADERS) as c:
            r = await c.get(url)
            cand.status_code = r.status_code
            if r.status_code < 400:
                cand.status = "OK"
            elif r.status_code == 403:
                if "cloudflare" in (r.text[:500] if hasattr(r, 'text') and r.text else '').lower():
                    cand.status = "CLOUDFLARE"
                else:
                    cand.status = "BLOCKED"
            else:
                cand.status = f"HTTP_{r.status_code}"
    except Exception as e:
        cand.status = "ERROR"
        cand.error = str(e)[:60]
    return cand


async def search_duckduckgo(query: str, max_results: int = 10) -> list[str]:
    """Search DuckDuckGo for alternative domains."""
    urls = []
    try:
        url = f"https://html.duckduckgo.com/html/?q={__import__('urllib.parse').quote(query)}"
        async with httpx.AsyncClient(timeout=15, follow_redirects=True, headers=HEADERS) as c:
            r = await c.get(url)
            if r.status_code == 200:
                domains = set(re.findall(r'https?://([^/"\'<>]+)', r.text))
                for d in domains:
                    d = d.lstrip("www.").split("/")[0].split("?")[0]
                    if d and '.' in d and not any(x in d for x in ['duckduckgo', 'google', 'facebook', 'twitter',
                                                                     'instagram', 'youtube', 'reddit', 'github']):
                        urls.append(d)
    except Exception as e:
        logger.warning(f"DuckDuckGo search error: {e}")
    return list(set(urls))[:max_results]


async def search_google_cse(query: str, api_key: str = "", cse_id: str = "") -> list[str]:
    """Search Google Custom Search if API key is available."""
    if not api_key or not cse_id:
        return []
    urls = []
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                "https://www.googleapis.com/customsearch/v1",
                params={"key": api_key, "cx": cse_id, "q": query, "num": 10},
            )
            if r.status_code == 200:
                for item in r.json().get("items", []):
                    link = item.get("link", "")
                    domain = urlparse(link).netloc.lstrip("www.")
                    if domain:
                        urls.append(domain)
    except Exception as e:
        logger.warning(f"Google CSE error: {e}")
    return urls


async def find_alternatives_for_domain(
    dead_domain: str,
    site_name: str = "",
    sample_path: str = "/",
    google_key: str = "",
    google_cse: str = "",
) -> list[DomainCandidate]:
    """Find working alternatives for a dead domain."""
    logger.info(f"Finding alternatives for: {dead_domain}")
    candidates = []

    # 1. Check known alternatives
    known = KNOWN_ALTERNATIVES.get(dead_domain, [])
    for alt_domain in known:
        cand = await test_domain(alt_domain, sample_path)
        cand.source = "known"
        candidates.append(cand)
        logger.info(f"  Known {alt_domain}: {cand.status}")
        if cand.status == "OK":
            pass  # good candidate, keep checking others too

    # 2. Web search
    search_terms = []
    name_key = site_name or dead_domain.split(".")[0]
    for key in [name_key, dead_domain]:
        if key in SITE_SEARCH_KEYWORDS:
            search_terms.append(SITE_SEARCH_KEYWORDS[key])
    search_terms.append(f"{name_key} yeni domain 2026")
    search_terms.append(f"{name_key} güncel adres")

    found_domains = set()
    for query in search_terms[:3]:
        results = await search_duckduckgo(query)
        found_domains.update(results)

    if google_key and google_cse:
        for query in search_terms[:2]:
            results = await search_google_cse(query, google_key, google_cse)
            found_domains.update(results)

    # Test found domains
    for d in found_domains:
        if d == dead_domain or d in known:
            continue
        cand = await test_domain(d, sample_path)
        cand.source = "search"
        candidates.append(cand)
        logger.info(f"  Search {d}: {cand.status}")

    # 3. Try common TLD variations
    base = dead_domain.rsplit(".", 1)[0]
    for tld in [".com", ".net", ".org", ".io", ".app", ".co", ".me", ".live", ".pw", ".vip"]:
        alt = f"{base}{tld}"
        if alt not in known and alt not in found_domains:
            cand = await test_domain(alt, sample_path)
            cand.source = "tld_guess"
            candidates.append(cand)
            if cand.status == "OK":
                logger.info(f"  TLD guess {alt}: {cand.status}")

    # Sort: OK first, then CF, then rest
    candidates.sort(key=lambda c: (0 if c.status == "OK" else 1 if c.status == "CLOUDFLARE" else 2))
    return candidates


async def find_and_test_all_dead(
    db_session,
    google_key: str = "",
    google_cse: str = "",
    progress_callback=None,
) -> dict[str, list[DomainCandidate]]:
    """Find alternatives for all dead domains in the DB."""
    from sqlalchemy import text

    # Get unique dead domains
    result = await db_session.execute(text("""
        SELECT DISTINCT s.site_name, s.site_url
        FROM site s
        WHERE s.is_dead = 1 AND s.site_url IS NOT NULL
        LIMIT 50
    """))
    dead_sites = [(row[0], row[1]) for row in result.fetchall()]

    logger.info(f"Finding alternatives for {len(dead_sites)} dead sites")
    all_candidates = {}

    for idx, (site_name, site_url) in enumerate(dead_sites):
        parsed = urlparse(site_url)
        domain = parsed.netloc.lstrip("www.")
        path = parsed.path or "/"

        candidates = await find_alternatives_for_domain(
            domain, site_name, path, google_key, google_cse
        )
        all_candidates[domain] = candidates
        working = [c for c in candidates if c.status == "OK"]
        logger.info(f"[{idx+1}/{len(dead_sites)}] {domain}: {len(working)} working alternatives")

        if progress_callback:
            await progress_callback(idx + 1, len(dead_sites), domain, len(working))

    return all_candidates


def _content_type_to_path_pattern(ctype: str, title_slug: str) -> list[str]:
    """İçerik türüne göre olası URL pattern'leri üret."""
    patterns = {
        'movie': [f'/film/{title_slug}/', f'/film/{title_slug}-izle/', f'/movie/{title_slug}/'],
        'series': [f'/dizi/{title_slug}/', f'/dizi/{title_slug}-izle/', f'/series/{title_slug}/'],
        'anime': [f'/anime/{title_slug}/', f'/anime/{title_slug}-izle/', f'/video/{title_slug}/'],
        'manga': [f'/manga/{title_slug}/', f'/manga/{title_slug}/bolum-1/', f'/seri/{title_slug}/'],
        'manhwa': [f'/manga/{title_slug}/', f'/manga/{title_slug}/bolum-1/', f'/seri/{title_slug}/'],
        'game': [f'/?s={title_slug}', f'/game/{title_slug}/'],
        'cartoon': [f'/dizi/{title_slug}/', f'/cartoon/{title_slug}/'],
    }
    return patterns.get(ctype, [f'/{title_slug}/'])


def _title_to_slug(title: str) -> str:
    """Başlığı URL-slug formatına çevir."""
    import re
    slug = title.lower()
    tr_map = {'ç': 'c', 'ğ': 'g', 'ı': 'i', 'İ': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u', 'ə': 'e'}
    for k, v in tr_map.items():
        slug = slug.replace(k, v)
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug.strip())
    return slug


async def search_content_on_site(site_url: str, title: str, ctype: str) -> Optional[str]:
    """Belirli bir site içerisinde içerik başlığını ara, çalışan URL döndür."""
    parsed = urlparse(site_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    slug = _title_to_slug(title)

    patterns = _content_type_to_path_pattern(ctype, slug)
    patterns.insert(0, f'/?s={slug}')  # site search first

    for path in patterns[:5]:
        url = f"{base}{path}"
        try:
            async with httpx.AsyncClient(timeout=10, follow_redirects=True, headers=HEADERS) as c:
                r = await c.head(url)
                if r.status_code == 405:
                    r = await c.get(url)
                if r.status_code == 200:
                    logger.info(f"  Found on {parsed.netloc}: {path}")
                    return url
        except Exception:
            continue
    return None


async def find_alternatives_for_content(db_session, content_id: int) -> dict:
    """Tek içerik için alternatif site bul. DB'ye kaydetmez, öneri listesi döndür."""
    from sqlalchemy import text

    result = await db_session.execute(text("""
        SELECT id, title, type FROM content WHERE id = :cid
    """), {"cid": content_id})
    content = result.fetchone()
    if not content:
        return {"ok": False, "error": "Content not found"}

    cid, title, ctype = content

    # Mevcut siteleri al
    result = await db_session.execute(text("""
        SELECT id, site_name, site_url FROM site WHERE content_id = :cid
    """), {"cid": cid})
    existing = [{"id": r[0], "name": r[1], "url": r[2]} for r in result.fetchall()]

    # Mevcut domain'lerden alternatif tara
    candidates = []
    for site in existing:
        domain = urlparse(site["url"]).netloc.lstrip("www.")
        alt_candidates = await find_alternatives_for_domain(domain, site["name"])
        for c in alt_candidates:
            if c.status == "OK":
                site_url = f"https://www.{c.domain}/"
                found_url = await search_content_on_site(site_url, title, ctype)
                if found_url:
                    candidates.append({
                        "domain": c.domain,
                        "url": found_url,
                        "status": c.status,
                        "source": c.source,
                    })

    return {
        "ok": True,
        "content_id": cid,
        "title": title,
        "type": ctype,
        "existing_sites": existing,
        "candidates": candidates,
    }


async def auto_update_dead_contents(db_session, max_items: int = 20) -> dict:
    """Tüm ölü içerikleri tara, alternatif bul, DB'ye kaydet."""
    from sqlalchemy import text

    updates = {"checked": 0, "updated": 0, "errors": 0, "details": []}

    # İlk URL'si 404/403 dönen içerikleri bul
    import httpx
    rows = await db_session.execute(text("""
        SELECT DISTINCT c.id, c.title, c.type, s.site_url, s.site_name
        FROM content c
        JOIN site s ON s.content_id = c.id
        WHERE s.site_url IS NOT NULL
        LIMIT :limit
    """), {"limit": max_items * 3})
    all_rows = rows.fetchall()

    import random
    random.shuffle(all_rows)  # farklı domainlerden örnek al

    tested = 0
    seen_cid = set()
    for cid, title, ctype, site_url, site_name in all_rows:
        if cid in seen_cid or tested >= max_items:
            continue
        seen_cid.add(cid)

        # Test current URL
        try:
            async with httpx.AsyncClient(timeout=8, follow_redirects=True, headers=HEADERS) as c:
                r = await c.head(site_url)
                if r.status_code == 405:
                    r = await c.get(site_url)
                if r.status_code == 200:
                    continue  # already working
        except Exception:
            pass

        tested += 1
        updates["checked"] += 1

        # Search for this content
        domain = urlparse(site_url).netloc.lstrip("www.")
        logger.info(f"Finding alternatives for #{cid} {title[:40]} ({domain})")

        alts = await find_alternatives_for_domain(domain, site_name, "/")
        working = [c for c in alts if c.status == "OK"]

        if not working:
            # Try common Turkish series/manga sites directly
            fallback_sites = []
            if ctype == 'series':
                fallback_sites = ['dizipod.com', 'dizibox.live', 'yabancidizi.pro']
            elif ctype in ('manga', 'manhwa'):
                fallback_sites = ['mangasehri.net', 'ragnarscans.net', 'monomanga.com.tr']

            for fb_domain in fallback_sites:
                if fb_domain == domain:
                    continue
                cand = await test_domain(fb_domain)
                if cand.status == "OK":
                    found = await search_content_on_site(f"https://www.{fb_domain}", title, ctype)
                    if found:
                        working.append(cand)
                        break

        if working:
            best = working[0]
            site_url_new = None
            if not site_url_new:
                site_url_new = f"https://www.{best.domain}/"

            # Find exact content URL
            found_url = await search_content_on_site(site_url_new, title, ctype)
            if found_url:
                await db_session.execute(text("""
                    UPDATE site SET site_name = :name, site_url = :url, is_dead = 0
                    WHERE content_id = :cid AND site_url = :old_url
                """), {"name": best.domain, "url": found_url, "cid": cid, "old_url": site_url})
                updates["updated"] += 1
                updates["details"].append({
                    "cid": cid, "title": title, "old_url": site_url, "new_url": found_url
                })
                logger.info(f"  UPDATED #{cid} {title[:40]}: {site_url} -> {found_url}")
        else:
            updates["errors"] += 1

    await db_session.commit()
    return updates


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "content":
        domain = sys.argv[2] if len(sys.argv) > 2 else ""
        path = sys.argv[3] if len(sys.argv) > 3 else "/"
        candidates = asyncio.run(find_alternatives_for_domain(domain, "", path))
        print(json.dumps([
            {"domain": c.domain, "source": c.source, "status": c.status,
             "status_code": c.status_code}
            for c in candidates
        ], indent=2, ensure_ascii=False))
    elif len(sys.argv) > 1 and sys.argv[1] == "search":
        title = sys.argv[2] if len(sys.argv) > 2 else ""
        ctype = sys.argv[3] if len(sys.argv) > 3 else "series"
        site = sys.argv[4] if len(sys.argv) > 4 else "https://www.setfilmizle.uk"
        result = asyncio.run(search_content_on_site(site, title, ctype))
        print(json.dumps({"url": result}, indent=2))
    else:
        domain = sys.argv[1] if len(sys.argv) > 1 else "hdfilmcehennemi.now"
        path = sys.argv[2] if len(sys.argv) > 2 else "/"
        candidates = asyncio.run(find_alternatives_for_domain(domain, "", path))
        print(json.dumps([
            {"domain": c.domain, "source": c.source, "status": c.status,
             "status_code": c.status_code}
            for c in candidates
        ], indent=2, ensure_ascii=False))
