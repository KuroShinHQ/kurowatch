"""Episode URL'leri bul ve ilk iframe/video kontrol."""
import httpx
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.5",
}

def check_ep(label, url, referer):
    h = dict(HEADERS)
    h["Referer"] = referer
    print(f"\n{'='*60}")
    print(f"{label}")
    print(f"URL: {url}")
    try:
        with httpx.Client(timeout=15, follow_redirects=True, headers=h) as c:
            r = c.get(url)
        print(f"Status: {r.status_code} | final: {str(r.url)[:80]} | len={len(r.text)}")
        # iframe ara
        iframes = re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', r.text, re.IGNORECASE)
        # video src ara
        videos = re.findall(r'<(?:video|source)[^>]+src=["\']([^"\']+)["\']', r.text, re.IGNORECASE)
        # data-src ile embed
        embeds = re.findall(r'(?:data-src|data-iframe|data-video)=["\']([^"\']+)["\']', r.text, re.IGNORECASE)
        # m3u8/mp4 direkt
        streams = re.findall(r'["\']([^"\']*(?:\.m3u8|\.mp4|manifest)[^"\']*)["\']', r.text, re.IGNORECASE)

        print(f"  iframe: {iframes[:3]}")
        print(f"  video:  {videos[:3]}")
        print(f"  embeds: {embeds[:3]}")
        print(f"  streams:{streams[:3]}")

        if r.status_code == 200 and (iframes or videos or streams):
            print("  → PLAYWRIGHT GEREKMEYEBİLİR, HTML'de veri var")
        elif r.status_code == 200:
            print("  → Tüm içerik JS ile yükleniyor (Playwright şart)")
    except Exception as e:
        print(f"HATA: {e}")

# turkanime.tv — episode URL dene
check_ep(
    "turkanime.tv ep-1 dene",
    "https://www.turkanime.tv/video/ore-dake-level-up-na-ken-1-bolum",
    "https://www.turkanime.tv/"
)
check_ep(
    "turkanime.tv ep-1 dene (alternatif slug)",
    "https://www.turkanime.tv/video/ore-dake-level-up-na-ken-how-to-get-stronger-1-bolum",
    "https://www.turkanime.tv/"
)

# dizibox — dungeon meshi episode linkleri ara
print(f"\n{'='*60}")
print("dizibox.live — dungeon-meshi episode linkleri")
with httpx.Client(timeout=15, follow_redirects=True, headers=HEADERS) as c:
    r = c.get("https://www.dizibox.live/diziler/dungeon-meshi/")
# Dungeon Meshi özel linkler
dm_links = [l for l in re.findall(r'href=["\']([^"\']+)["\']', r.text) if 'dungeon' in l.lower() or 'meshi' in l.lower()]
print(f"dungeon-meshi linkleri ({len(dm_links)}): {dm_links[:10]}")

# Sezon/bölüm linkleri (genel format /sezon-N/bolum-N)
sezon_links = [l for l in re.findall(r'href=["\']([^"\']+)["\']', r.text) if re.search(r'sezon.?\d+.?bolum', l, re.IGNORECASE)]
print(f"sezon/bolum linkleri ({len(sezon_links)}): {sezon_links[:5]}")

# diziwatch — player JS ara
print(f"\n{'='*60}")
print("diziwatch.ac — JS player config ara")
with httpx.Client(timeout=15, follow_redirects=True, headers=HEADERS) as c:
    r = c.get("https://diziwatch.ac/dizi/solo-leveling/sezon-1/bolum-1", headers={**HEADERS, "Referer": "https://diziwatch.ac/"})
print(f"Status: {r.status_code} | len={len(r.text)}")
# JS içinde video config ara
js_configs = re.findall(r'(?:file|src|source|videoUrl|videoSrc|streamUrl)\s*[:=]\s*["\']([^"\']+)["\']', r.text, re.IGNORECASE)
print(f"JS video config: {js_configs[:5]}")
# Embed/iframe URL
iframes = re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', r.text, re.IGNORECASE)
print(f"iframe: {iframes[:3]}")
# İlk 500 char
idx = r.text.find('player') if 'player' in r.text.lower() else r.text.find('video')
if idx > 0:
    print(f"'player'/'video' context:\n{r.text[max(0,idx-50):idx+200]}")
