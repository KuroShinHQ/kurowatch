"""Düzeltilmiş URL'ler + protocol-relative fix ile tekrar test."""
import asyncio
import sys
import time

sys.path.insert(0, '/mnt/c/Kuroshin/kurowatch')

SEP = "=" * 70

TESTS = [
    ("turkanime.tv",      "anime", "https://www.turkanime.tv/video/ore-dake-level-up-na-ken-1-bolum"),
    ("diziwatch.ac",      "dizi",  "https://diziwatch.ac/dizi/solo-leveling/sezon-1/bolum-1"),
    ("anizm.net",         "anime", "https://anizm.net/ore-dake-level-up-na-ken-1-bolum"),
    ("dizibox.live ep-1", "dizi",  "https://www.dizibox.live/dungeon-meshi-1-sezon-1-bolum-izle/"),
]


async def stream_test(domain, media_type, url):
    from backend.downloader.stream_finder import find_stream_url
    print(f"\n{SEP}")
    print(f"[{media_type.upper()}] {domain}")
    print(f"URL: {url[:80]}")
    t0 = time.time()
    try:
        result = await find_stream_url(url)
        elapsed = time.time() - t0
        print(f"Süre: {elapsed:.0f}s")
        if result == url:
            print(f">>> SONUÇ: ❌ Embed bulunamadı (orijinal URL döndü)")
        elif any(x in result for x in ('.m3u8', '.mp4', 'manifest.mpd')):
            print(f">>> SONUÇ: ✅ DOĞRUDAN VİDEO")
            print(f"URL: {result[:100]}")
        else:
            print(f">>> SONUÇ: ✅ EMBED/PLAYER BULUNDU")
            print(f"Embed: {result[:100]}")
    except Exception as e:
        elapsed = time.time() - t0
        print(f">>> SONUÇ: ❌ HATA ({elapsed:.0f}s): {e}")


async def main():
    print(SEP)
    print("Site Testleri — Düzeltilmiş URL + protocol-relative fix")
    print(SEP)
    for domain, mt, url in TESTS:
        await stream_test(domain, mt, url)
    print(f"\n{SEP}")
    print("TAMAMLANDI")


if __name__ == "__main__":
    asyncio.run(main())
