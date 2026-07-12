"""
SOHBET-147 — URL Pattern Generator
Learns URL patterns from existing site entries and generates new URLs for alternative domains.
"""
import json, logging, os, re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse, urlunparse

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "url_patterns.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("url_patterns")


@dataclass
class UrlPattern:
    site_name: str
    content_type: str  # anime, manga, manhwa, movie, series, game
    path_template: str  # e.g. /{slug}-{ep}-bolum-izle or /{type}/{slug}/
    has_ep_number: bool = False
    has_season: bool = False
    has_film_prefix: bool = False
    slug_style: str = "turkish"  # turkish, english, mixed
    query_template: str = ""

    def generate(self, domain: str, slug: str, ep_num: Optional[int] = None,
                 season: Optional[int] = None) -> str:
        """Generate a URL from this pattern."""
        path = self.path_template
        if self.has_ep_number and ep_num is not None:
            path = path.replace("{ep}", str(ep_num))
        if self.has_season and season is not None:
            path = path.replace("{season}", str(season))
        path = path.replace("{slug}", slug)
        scheme = "https"
        netloc = f"www.{domain}" if not domain.startswith("www.") else domain
        return f"{scheme}://{netloc}{path}"


CONTENT_TYPE_PATTERNS = {
    "anime": [
        UrlPattern("tranimaci.com", "anime", "/{slug}-{ep}-bolum-izle", has_ep_number=True, slug_style="english"),
        UrlPattern("animexe.com", "anime", "/watch/{slug}/{season}/{ep}", has_ep_number=True, has_season=True, slug_style="english"),
    ],
    "manga": [
        UrlPattern("mangatr.app", "manga", "/manga/{slug}/bolum-{ep}/", has_ep_number=True, slug_style="english"),
        UrlPattern("ragnarscans.net", "manga", "/manga/{slug}/{ep}/", has_ep_number=True, slug_style="english"),
    ],
    "manhwa": [
        UrlPattern("mangatr.app", "manhwa", "/manga/{slug}/bolum-{ep}/", has_ep_number=True, slug_style="english"),
        UrlPattern("ragnarscans.net", "manhwa", "/manga/{slug}/{ep}/", has_ep_number=True, slug_style="english"),
    ],
    "movie": [
        UrlPattern("hdfilmcehennemi.now", "movie", "/film/{slug}/", slug_style="turkish", has_film_prefix=True),
        UrlPattern("hdfilmcehennemi.nl", "movie", "/{slug}/", slug_style="english"),
    ],
    "series": [
        UrlPattern("setfilmizle.uk", "series", "/{slug}/", slug_style="english"),
        UrlPattern("dizibox.so", "series", "/{slug}/sezon-{season}/bolum-{ep}/", has_ep_number=True, has_season=True, slug_style="english"),
    ],
    "game": [
        UrlPattern("fitgirl-repacks.site", "game", "/?s={slug}", slug_style="english"),
    ],
}


def learn_pattern_from_urls(urls: list[str]) -> Optional[UrlPattern]:
    """Extract a URL pattern from existing URLs."""
    if not urls:
        return None

    parsed = [urlparse(u) for u in urls]
    paths = [p.path for p in parsed]

    # Check common patterns
    common_path = os.path.commonpath(paths) if len(paths) > 1 else paths[0]
    has_nums = bool(re.search(r'\d+', paths[0]))
    has_film = '/film/' in paths[0]

    # Determine slug style
    has_turkish = bool(re.search(r'[ığüşöç]', paths[0]))
    slug_style = "turkish" if has_turkish else "english"

    slug = paths[0].split("/")[-2] if paths[0].endswith("/") else paths[0].split("/")[-1] if paths[0] else ""
    # Try to identify the slug
    has_ep = "bolum" in paths[0].lower() or "episode" in paths[0].lower() or "bölüm" in paths[0].lower()

    pattern = UrlPattern(
        site_name="unknown",
        content_type="unknown",
        path_template=paths[0] if paths else "/",
        has_ep_number=has_nums,
        has_film_prefix=has_film,
        slug_style=slug_style,
    )
    return pattern


async def find_slug_for_content(db_session, content_id: int, domain: str) -> Optional[str]:
    """Find the correct slug for a content on a given domain."""
    from sqlalchemy import text

    # Get existing site URLs for this content
    result = await db_session.execute(text("""
        SELECT site_url, site_name FROM site WHERE content_id = :cid AND site_url IS NOT NULL
    """), {"cid": content_id})
    existing = result.fetchall()

    if not existing:
        return None

    # Extract slug from existing URLs
    for site_url, site_name in existing:
        parsed = urlparse(site_url)
        if domain in parsed.netloc or domain.split(".")[0] in parsed.netloc:
            existing_domain = parsed.netloc.lstrip("www.")
            path = parsed.path.rstrip("/")
            slug = path.split("/")[-1] if path else ""
            if slug:
                return slug

    # Fallback: use slug from first existing site URL
    first_url = existing[0][0]
    parsed = urlparse(first_url)
    path = parsed.path.rstrip("/")
    # Remove common prefixes
    for prefix in ["/film/", "/manga/", "/dizi/", "/watch/", "/video/"]:
        if path.startswith(prefix):
            return path[len(prefix):]
    slug = path.split("/")[-1] if path else ""
    return slug if slug else None


def apply_new_domain_to_url(old_url: str, new_domain: str, content_type: str, slug: str = "") -> str:
    """Apply a new domain to an old URL, adjusting the path if needed."""
    parsed = urlparse(old_url)
    path = parsed.path
    old_domain = parsed.netloc.lstrip("www.")

    # Simple domain replacement
    new_url = old_url.replace(parsed.netloc, f"www.{new_domain}" if not new_domain.startswith("www.") else new_domain)

    # Check if we need path adjustments based on content type
    if content_type == "movie":
        if "hdfilmcehennemi.nl" in new_domain:
            # Remove /film/ prefix, .nl doesn't use it
            new_url = new_url.replace("/film/", "/")
            # Remove -izle suffix
            new_url = re.sub(r'-izle(-\d+)?/?', '/', new_url)
    elif content_type == "manga" or content_type == "manhwa":
        if "mangatr.app" in new_domain and "/bolum-" not in path:
            pass  # keep as-is, mangatr.app has different path format
        if "ragnarscans.net" in new_domain and path.startswith("/manga/"):
            pass  # keep standard ragnar format

    return new_url


def extract_slug(url: str) -> str:
    """Extract the content slug from a URL."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    parts = path.split("/")
    # Skip common prefixes
    skip = {"film", "manga", "dizi", "watch", "video", "anime", "seri", "category"}
    for part in reversed(parts):
        if part and part not in skip:
            return part
    return parts[-1] if parts else ""


def normalize_domain(domain: str) -> str:
    """Normalize domain to netloc format."""
    domain = domain.strip().lower()
    domain = domain.lstrip("www.").lstrip(".")
    domain = re.sub(r'^https?://', '', domain)
    return domain


__all__ = [
    "UrlPattern", "CONTENT_TYPE_PATTERNS", "learn_pattern_from_urls",
    "find_slug_for_content", "apply_new_domain_to_url",
    "extract_slug", "normalize_domain",
]
