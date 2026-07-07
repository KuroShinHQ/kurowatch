"""
Kaynak sitelerden yerel etiket / tür çıkarımı.
Dizigom, fullhdfilmizlesene, manga(Madara/Next.js/MangaDex) sayfalarından
içeriğe ait yerel etiketleri çıkarır ve küresel metadata (AniList/TMDB)
ile eşleştirmede kullanılır.
"""
import logging
import re
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# AniList İngilizce tür -> Türkçe gösterim (frontend ile uyumlu)
GENRE_TR = {
    "Action": "Aksiyon",
    "Adventure": "Macera",
    "Comedy": "Komedi",
    "Drama": "Dram",
    "Ecchi": "Ecchi",
    "Fantasy": "Fantezi",
    "Hentai": "Hentai",
    "Horror": "Korku",
    "Isekai": "Isekai",
    "Josei": "Josei",
    "Magic": "Sihir",
    "Mahou Shoujo": "Sihirli Kız",
    "Mecha": "Meka",
    "Military": "Askeri",
    "Music": "Müzik",
    "Mystery": "Gizem",
    "Psychological": "Psikolojik",
    "Romance": "Romantik",
    "Samurai": "Samuray",
    "School": "Okul",
    "Sci-Fi": "Bilim Kurgu",
    "Seinen": "Seinen",
    "Shoujo": "Shoujo",
    "Shounen": "Shounen",
    "Slice of Life": "Günlük Yaşam",
    "Sports": "Spor",
    "Supernatural": "Doğaüstü",
    "Thriller": "Gerilim",
    "Vampire": "Vampir",
    "Webtoon": "Webtoon",
}

# Türkçe (küçük) -> AniList İngilizce tür ters haritası
REVERSE_GENRE_TR = {v.lower(): k for k, v in GENRE_TR.items()}

# Sık görülen site kategorileri
_EXTRA_EN = {
    "aksiyon": "Action",
    "animasyon": "Animation",
    "anime": "Anime",
    "bilim kurgu": "Sci-Fi",
    "dizi": "Series",
    "film": "Movie",
    "gizem": "Mystery",
    "gerilim": "Thriller",
    "gençlik": "Youth",
    "intikam": "Revenge",
    "komedi": "Comedy",
    "korku": "Horror",
    "macera": "Adventure",
    "manga": "Manga",
    "manhwa": "Manhwa",
    "romantik": "Romance",
    "savaş": "War",
    "suç": "Crime",
    "tarihî": "Historical",
    "tarihi": "Historical",
    "webtoon": "Webtoon",
    "yaşam": "Slice of Life",
    "çizgi dizi": "Cartoon",
    "çizgi film": "Cartoon",
}

# Site öznel etiket -> küresel metadata eşleştirmesi
_TAG_TO_ENGLISH = {**REVERSE_GENRE_TR, **_EXTRA_EN}

# Tür bazlı renk paleti (frontend TAG_COLORS ile uyumlu)
_TAG_COLOR = {
    "action": "#ff6b6b",
    "adventure": "#ffb84d",
    "comedy": "#ffd966",
    "drama": "#a78bfa",
    "fantasy": "#c084fc",
    "horror": "#ef4444",
    "isekai": "#22d3ee",
    "manga": "#ffd9a1",
    "manhwa": "#bbc5eb",
    "movie": "#c084fc",
    "mystery": "#64748b",
    "revenge": "#f43f5e",
    "romance": "#f472b6",
    "school": "#38bdf8",
    "sci-fi": "#818cf8",
    "series": "#ff9a3c",
    "shounen": "#fbbf24",
    "slice of life": "#86efac",
    "sports": "#4ade80",
    "supernatural": "#2dd4bf",
    "thriller": "#94a3b8",
    "webtoon": "#a3e635",
    "youth": "#facc15",
}


def normalize_tag(name: str) -> str:
    """Etiket adını temizle; boşluk, kategori önekleri, fazla uzunlukları at."""
    if not name:
        return ""
    text = re.sub(r"<[^>]+>", "", name)
    text = re.sub(r"^(?:tür(?:ler)?|kategori|etiket|tag|genre)s?\s*[:\-]\s*", "", text, flags=re.I)
    text = re.sub(r"[\s\xa0]+", " ", text)
    text = text.strip(' \t\n\r\u200c\u200b·•,;/')
    text = text[:60]
    if not text:
        return ""
    # Yaygın kaçış/encode hatalarını düzelt
    text = text.replace("&amp;", "&").replace("&#039;", "'").replace("&quot;", '"')
    return text


def title_case_tag(name: str) -> str:
    """İlk harfler büyük, küçük bağlaçlar ise korunur."""
    small = {"ve", "ile", "veya", "de", "da", "ki", "için", "gibi", "kadar"}
    parts = name.lower().split()
    if not parts:
        return name
    return " ".join(p.capitalize() if i == 0 or p not in small else p for i, p in enumerate(parts))


def turkish_to_english(tag: str) -> Optional[str]:
    """Yerel Türkçe etiketi küresel metadata terimine çevir."""
    if not tag:
        return None
    key = tag.lower().strip()
    return _TAG_TO_ENGLISH.get(key)


def tag_color(name: str) -> str:
    key = name.lower().strip()
    return _TAG_COLOR.get(key, "#9090b0")


def _extract_with_lxml(html: str, selectors: list[str]) -> list[str]:
    tags: list[str] = []
    try:
        from lxml import html as lh
        tree = lh.fromstring(html)
        for sel in selectors:
            try:
                for el in tree.cssselect(sel):
                    t = normalize_tag(el.text_content())
                    if t and t not in tags:
                        tags.append(t)
            except Exception:  # noqa: BLE001
                continue
    except Exception as exc:  # noqa: BLE001
        logger.debug("lxml tag extraction failed: %s", exc)
    return tags


def _extract_meta_keywords(html: str) -> list[str]:
    tags: list[str] = []
    for m in re.finditer(r'<meta[^>]+name=["\']?keywords["\']?[^>]+content=["\']([^"\']+)', html, re.I):
        for part in m.group(1).split(","):
            t = normalize_tag(part)
            if t and t not in tags:
                tags.append(t)
    return tags


def _extract_regex_links(html: str, patterns: list[str]) -> list[str]:
    tags: list[str] = []
    for pat in patterns:
        for m in re.finditer(pat, html, re.I | re.S):
            t = normalize_tag(m.group(1))
            if t and t not in tags:
                tags.append(t)
    return tags


# ── Site-specific extractors ─────────────────────────────────────────

def extract_dizigom_tags(html: str, url: str) -> list[str]:
    """dizigom sayfasından tür etiketlerini çıkar."""
    selectors = [
        ".genres a",
        ".film-info a[href*='tur']",
        ".film-info a[href*='genre']",
        ".post-tags a",
        ".tagcloud a",
        "a[rel='tag']",
        ".categories a",
    ]
    tags = _extract_with_lxml(html, selectors)
    if not tags:
        tags = _extract_regex_links(
            html,
            [
                r'<div[^>]*class=["\'][^"\']*genres?[^"\']*["\'][^>]*>.*?<a[^>]*>(.*?)</a>',
                r'<span[^>]*class=["\'][^"\']*genre[^"\']*["\'][^>]*>(.*?)</span>',
                r'tür(?:ler)?\s*[:\-]\s*<a[^>]*>(.*?)</a>',
            ],
        )
    if not tags:
        tags = _extract_meta_keywords(html)
    logger.info("dizigom tags from %s: %s", url[:60], tags)
    return tags[:12]


def extract_fullhdfilmizlesene_tags(html: str, url: str) -> list[str]:
    """fullhdfilmizlesene sayfasından türleri çıkar."""
    selectors = [
        ".film-info a[href*='tur']",
        ".film-info a[href*='genre']",
        ".genres a",
        ".categories a",
        "a[rel='tag']",
        ".tags a",
        ".post-tags a",
    ]
    tags = _extract_with_lxml(html, selectors)
    if not tags:
        tags = _extract_meta_keywords(html)
    logger.info("fullhdfilmizlesene tags from %s: %s", url[:60], tags)
    return tags[:12]


def extract_movie_series_tags(html: str, url: str, site_name: str = "") -> list[str]:
    """Genel film/dizi sitesi etiket çıkarımı."""
    selectors = [
        ".genres a",
        ".film-info a[href*='tur']",
        ".film-info a[href*='genre']",
        ".categories a",
        "a[rel='tag']",
        ".tags a",
        ".post-tags a",
    ]
    tags = _extract_with_lxml(html, selectors)
    if not tags:
        tags = _extract_meta_keywords(html)
    logger.info("%s tags from %s: %s", site_name or "site", url[:60], tags)
    return tags[:12]


def extract_manga_source_tags(html: str, url: str) -> list[str]:
    """Manga/manhwa chapter sayfasından tür/tema etiketleri çıkar."""
    selectors = [
        ".genres-content a",
        ".manga-info-list a[href*='genre']",
        ".post-content a[href*='genre']",
        ".tags-content a",
        "a[href*='genre']",
        ".manga-tags a",
        ".post-tags a",
    ]
    tags = _extract_with_lxml(html, selectors)
    if not tags:
        tags = _extract_meta_keywords(html)
    if not tags:
        # Meta description içinde virgülle ayrılmış kelimeler
        for m in re.finditer(r'<meta[^>]+name=["\']?description["\']?[^>]+content=["\']([^"\']+)', html, re.I):
            for part in m.group(1).split(","):
                t = normalize_tag(part)
                if t and t not in tags:
                    tags.append(t)
    logger.info("manga tags from %s: %s", url[:60], tags)
    return tags[:12]


def extract_site_tags(site_name: str, html: str, url: str) -> list[str]:
    """Site adına göre uygun tag extractor'ı çağır."""
    name = site_name.lower()
    if name == "dizigom":
        return extract_dizigom_tags(html, url)
    if name == "fullhdfilmizlesene":
        return extract_fullhdfilmizlesene_tags(html, url)
    if name == "hdfilmcehennemi":
        return extract_movie_series_tags(html, url, name)
    return []


__all__ = [
    "GENRE_TR",
    "REVERSE_GENRE_TR",
    "normalize_tag",
    "title_case_tag",
    "turkish_to_english",
    "tag_color",
    "extract_dizigom_tags",
    "extract_fullhdfilmizlesene_tags",
    "extract_movie_series_tags",
    "extract_manga_source_tags",
    "extract_site_tags",
]
