import httpx
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9",
    "Referer": "https://ruyamanga.net/",
}

tests = [
    ("ruyamanga.net bolum-122 no-list", "https://ruyamanga.net/manga/i-am-the-fated-villain/bolum-122/"),
    ("asurascans.com.tr bolum-239 no-list", "https://asurascans.com.tr/manga/bilge-okuyucunun-bakis-acisi/bolum-239/"),
    ("ruyamanga.com bolum-1 style=list", "https://www.ruyamanga.com/manga/world-s-apocalypse-online/bolum-1/?style=list"),
    ("ruyamanga.net bolum-1 style=list", "https://ruyamanga.net/manga/i-am-the-fated-villain/bolum-1/?style=list"),
    ("asurascans.com.tr bolum-1 style=list", "https://asurascans.com.tr/manga/bilge-okuyucunun-bakis-acisi/bolum-1/?style=list"),
]

for name, url in tests:
    try:
        with httpx.Client(timeout=12, follow_redirects=True, headers=HEADERS) as c:
            r = c.get(url)
        imgs = re.findall(r'data-src=["\']([^"\']*\.(?:jpg|jpeg|png|webp))', r.text, re.IGNORECASE)
        reading = "reading-content" in r.text
        print(f"{r.status_code} | {len(imgs):3} img | reading={reading} | {name}")
    except Exception as e:
        print(f"ERR | {name} | {e}")
