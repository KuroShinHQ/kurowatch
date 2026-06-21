"""
build_ta_index.py — turkanime.tv sitemap'inden tüm anime URL'lerini çıkar.
Çıktı: /tmp/ta_index.json  →  {slug: episode_url}  formatında
"""
import asyncio, aiohttp, gzip, re, json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept-Encoding": "gzip, deflate",
}

SITEMAPS = [
    "https://www.turkanime.tv/sitemap/tv/sitemap1.xml.gz",
    "https://www.turkanime.tv/sitemap/tv/sitemap2.xml.gz",
    "https://www.turkanime.tv/sitemap/tv/sitemap3.xml.gz",
]

async def main():
    connector = aiohttp.TCPConnector(ssl=False)
    all_slugs: dict[str, str] = {}  # slug_prefix → ep1_url

    async with aiohttp.ClientSession(connector=connector) as session:
        for sm_url in SITEMAPS:
            print(f"İndiriliyor: {sm_url}")
            try:
                async with session.get(sm_url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=30)) as r:
                    if r.status != 200:
                        print(f"  HATA: {r.status}")
                        continue
                    raw = await r.read()
                    # gzip decode
                    try:
                        xml = gzip.decompress(raw).decode("utf-8", errors="ignore")
                    except Exception:
                        xml = raw.decode("utf-8", errors="ignore")

                    # /video/SLUG-1-bolum URL'lerini çıkar (ep 1 olanlar)
                    urls = re.findall(r"<loc>(https://www\.turkanime\.tv/video/[^<]+)</loc>", xml)
                    ep1_urls = [u for u in urls if re.search(r"-1-bolum$", u)]
                    other_urls = [u for u in urls if u not in ep1_urls]

                    print(f"  Toplam URL: {len(urls)} | ep1: {len(ep1_urls)} | diger: {len(other_urls)}")

                    for url in ep1_urls:
                        # slug = URL'den episode suffix'i kaldır
                        m = re.match(r"https://www\.turkanime\.tv/video/(.+)-1-bolum$", url)
                        if m:
                            slug = m.group(1)
                            all_slugs[slug] = url

                    # Ep1 olmayan ama yeni animeler için de slug çıkar
                    for url in other_urls:
                        m = re.match(r"https://www\.turkanime\.tv/video/(.+)-(\d+)-bolum", url)
                        if m:
                            slug = m.group(1)
                            ep_num = int(m.group(2))
                            # Sadece ep1 URL'si yoksa ekle
                            if slug not in all_slugs:
                                # ep1 URL'sini türet
                                ep1_url = f"https://www.turkanime.tv/video/{slug}-1-bolum"
                                all_slugs[slug] = ep1_url

            except Exception as e:
                print(f"  ERR: {str(e)[:80]}")

    print(f"\nToplam unique anime slug: {len(all_slugs)}")
    print("Örnekler:")
    for slug in list(all_slugs.keys())[:10]:
        print(f"  {slug}")

    # JSON'a kaydet
    out = "/mnt/c/Kuroshin/kurowatch/scripts/ta_index.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(all_slugs, f, ensure_ascii=False, indent=2)
    print(f"\nKaydedildi: {out}")

asyncio.run(main())
