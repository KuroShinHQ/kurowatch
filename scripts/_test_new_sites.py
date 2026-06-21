"""
_test_new_sites.py — Yeni site URL'leri ile stream testi.
turkanime.tv + dizibox.live: önce episode URL bul, sonra stream_finder.
diziwatch.ac + anizm.net: direkt episode URL → stream_finder.
"""
import asyncio
import sys
import re
import httpx
import time

sys.path.insert(0, '/mnt/c/Kuroshin/kurowatch')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.5",
}

SEP = "=" * 80


def fetch(url, referer=None):
    h = dict(HEADERS)
    if referer:
        h["Referer"] = referer
    with httpx.Client(timeout=15, follow_redirects=True, headers=h) as c:
        r = c.get(url)
    return r


def find_episode_url_turkanime(html, base_url):
    """turkanime.tv — bölüm listesinden 1. bölüm URL'si bul."""
    # /bolum/ veya /episode/ pattern
    matches = re.findall(r'href=["\'](' + re.escape(base_url.rstrip('/')) + r'/bolum/[^"\']+)["\']', html, re.IGNORECASE)
    if not matches:
        matches = re.findall(r'href=["\']([^"\']*turkanime\.tv[^"\']*bolum[^"\']+)["\']', html, re.IGNORECASE)
    if not matches:
        # Genel bölüm link patternı
        matches = re.findall(r'href=["\']([^"\']+(?:bolum|episode|ep)[^"\']*)["\']', html, re.IGNORECASE)
    return matches[0] if matches else None


def find_episode_url_dizibox(html, base_url):
    """dizibox.live — bölüm link bul."""
    matches = re.findall(r'href=["\']([^"\']*dizibox\.live[^"\']*(?:bolum|episode|sezon)[^"\']*)["\']', html, re.IGNORECASE)
    if not matches:
        matches = re.findall(r'href=["\']([^"\']+(?:sezon|bolum)[^"\']*)["\']', html, re.IGNORECASE)
    return matches[0] if matches else None


async def stream_test(domain, episode_url):
    from backend.downloader.stream_finder import find_stream_url
    print(f"  Stream finder → {episode_url[:80]}")
    t0 = time.time()
    try:
        result = await find_stream_url(episode_url)
        elapsed = time.time() - t0
        if result == episode_url:
            print(f"  [{elapsed:.0f}s] ❌ Embed bulunamadı (orijinal URL döndü)")
            return False
        elif any(x in result for x in ('.m3u8', '.mp4', 'manifest.mpd')):
            print(f"  [{elapsed:.0f}s] ✅ DOĞRUDAN VİDEO: {result[:80]}")
            return True
        else:
            print(f"  [{elapsed:.0f}s] ✅ EMBED BULUNDU: {result[:80]}")
            return True
    except Exception as e:
        print(f"  [{time.time()-t0:.0f}s] ❌ HATA: {e}")
        return False


async def test_turkanime():
    domain = "turkanime.tv"
    series_url = "https://www.turkanime.tv/anime/ore-dake-level-up-na-ken-how-to-get-stronger"
    print(f"\n{SEP}")
    print(f"[2] turkanime.tv | {series_url[:70]}")

    try:
        r = fetch(series_url, referer="https://www.turkanime.tv/")
        print(f"  Seri sayfası: {r.status_code}")
        if r.status_code != 200:
            print(f"  >>> SONUÇ: ❌ Erişilemiyor ({r.status_code})")
            return

        # Episode URL bul
        ep_url = find_episode_url_turkanime(r.text, series_url)
        if not ep_url:
            # Tüm linklere bak
            all_links = re.findall(r'href=["\']([^"\']+)["\']', r.text)
            ep_links = [l for l in all_links if 'turkanime' in l and ('bolum' in l or 'episode' in l)]
            print(f"  Bulunan bölüm linkleri: {ep_links[:3]}")
            if ep_links:
                ep_url = ep_links[0]

        if not ep_url:
            print(f"  ⚠️  Episode URL bulunamadı — seri sayfası dönüyor, JS lazy-load olabilir")
            # Playwright ile dene
            await stream_test(domain, series_url)
        else:
            print(f"  Episode URL: {ep_url[:80]}")
            await stream_test(domain, ep_url)
    except Exception as e:
        print(f"  ❌ HATA: {e}")


async def test_diziwatch():
    domain = "diziwatch.ac"
    episode_url = "https://diziwatch.ac/dizi/solo-leveling/sezon-1/bolum-1"
    print(f"\n{SEP}")
    print(f"[3a] diziwatch.ac | {episode_url[:70]}")

    try:
        r = fetch(episode_url, referer="https://diziwatch.ac/")
        print(f"  HTTP: {r.status_code} | final_url: {str(r.url)[:70]}")
        if r.status_code not in (200, 301, 302):
            print(f"  >>> SONUÇ: ❌ Erişilemiyor ({r.status_code})")
            return
        await stream_test(domain, episode_url)
    except Exception as e:
        print(f"  ❌ HATA: {e}")


async def test_anizm():
    domain = "anizm.net"
    episode_url = "https://anizm.net/ore-dake-level-up-na-ken-1-bolum"
    print(f"\n{SEP}")
    print(f"[3b] anizm.net | {episode_url[:70]}")

    try:
        r = fetch(episode_url, referer="https://anizm.net/")
        print(f"  HTTP: {r.status_code} | final_url: {str(r.url)[:70]}")
        if r.status_code not in (200, 301, 302):
            print(f"  >>> SONUÇ: ❌ Erişilemiyor ({r.status_code})")
            return
        # Video iframe kontrol
        iframes = re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', r.text, re.IGNORECASE)
        print(f"  HTML iframe sayısı: {len(iframes)}")
        for f in iframes[:3]:
            print(f"  iframe: {f[:80]}")
        await stream_test(domain, episode_url)
    except Exception as e:
        print(f"  ❌ HATA: {e}")


async def test_dizibox():
    domain = "dizibox.live"
    series_url = "https://www.dizibox.live/diziler/dungeon-meshi/"
    print(f"\n{SEP}")
    print(f"[4] dizibox.live | {series_url[:70]}")

    try:
        r = fetch(series_url, referer="https://www.dizibox.live/")
        print(f"  Seri sayfası: {r.status_code}")
        if r.status_code != 200:
            print(f"  >>> SONUÇ: ❌ Erişilemiyor ({r.status_code})")
            return

        ep_url = find_episode_url_dizibox(r.text, series_url)
        if not ep_url:
            all_links = re.findall(r'href=["\']([^"\']+)["\']', r.text)
            ep_links = [l for l in all_links if 'dizibox' in l and ('sezon' in l or 'bolum' in l)]
            print(f"  Bulunan bölüm linkleri: {ep_links[:3]}")
            if ep_links:
                ep_url = ep_links[0]

        if not ep_url:
            print(f"  ⚠️  Episode URL bulunamadı — Playwright ile seri sayfasını dene")
            await stream_test(domain, series_url)
        else:
            print(f"  Episode URL: {ep_url[:80]}")
            await stream_test(domain, ep_url)
    except Exception as e:
        print(f"  ❌ HATA: {e}")


async def main():
    print(SEP)
    print("Yeni Site Testleri (turkanime / diziwatch / anizm / dizibox)")
    print(SEP)

    await test_turkanime()
    await test_diziwatch()
    await test_anizm()
    await test_dizibox()

    print(f"\n{SEP}")
    print("TEST TAMAMLANDI")


if __name__ == "__main__":
    asyncio.run(main())
