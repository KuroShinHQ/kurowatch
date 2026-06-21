"""Tranimeizle arama - hızlı slug HEAD check + WP REST"""
import re, sys, json
sys.path.insert(0, '/mnt/c/Kuroshin/kurowatch')
import curl_cffi.requests as req

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def slugify(title: str) -> str:
    import unicodedata
    t = unicodedata.normalize('NFD', title.lower())
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')
    t = re.sub(r"[^a-z0-9\s-]", "", t)
    t = re.sub(r"\s+", "-", t.strip())
    t = re.sub(r"-+", "-", t)
    return t

def try_head(slug, base="https://www.tranimeizle.co"):
    url = f"{base}/{slug}-1-bolum-izle"
    try:
        r = req.head(url, headers=HEADERS, impersonate='chrome131', timeout=8, allow_redirects=True)
        print(f"  HEAD {url}: {r.status_code}")
        return r.status_code in (200, 301, 302)
    except Exception as e:
        print(f"  ERR {url}: {e}")
        return False

# Test title
title = "The Faraway Paladin (Saihate no Paladin)"

# Farklı slug varyantları dene
# AniList romaji başlığı parantez içindeki kısım olabilir
m = re.search(r'\(([^)]+)\)', title)
romaji = m.group(1) if m else None
main_title = title[:title.index('(')].strip() if '(' in title else title

candidates = []
if romaji:
    candidates.append(slugify(romaji))
candidates.append(slugify(main_title))
if romaji:
    # sadece ilk 3 kelime
    candidates.append(slugify(" ".join(romaji.split()[:3])))

print(f"Title: {title}")
print(f"Candidates: {candidates}")
for slug in candidates:
    found = try_head(slug)
    if found:
        print(f"FOUND: https://www.tranimeizle.co/{slug}-1-bolum-izle")
        break
