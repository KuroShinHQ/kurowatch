"""Test alternative manga sites (mangawow, ruyamanga, golgebahcesi) for chapter images"""
import asyncio, httpx, re

async def test_manga(client, base_url, manga_slug, label):
    results = {}
    
    # Test manga page
    for url, desc in [
        (f"{base_url}/manga/{manga_slug}/", "manga page"),
        (f"{base_url}/manga/{manga_slug}/bolum-1/", "ch1"),
        (f"{base_url}/manga/{manga_slug}/chapter-1/", "ch1-alt"),
    ]:
        try:
            r = await client.get(url, timeout=12, follow_redirects=True,
                headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'tr-TR,tr;q=0.9'})
            has_ch_content = 'bolum' in r.text.lower() or 'chapter' in r.text.lower()
            has_img = '<img' in r.text
            is_wp = '/wp-content/' in r.text or 'wp-json' in r.text
            results[desc] = (r.status_code, len(r.text), has_ch_content, has_img, is_wp)
        except Exception as e:
            results[desc] = (None, 0, False, False, str(e)[:30])
    
    print(f"\n=== {label} ({base_url}) ===")
    for k, v in results.items():
        status, size, ch, img, wp = v
        icon = "✅" if (status == 200 and size > 10000) else "❌"
        print(f"  {icon} {k:15s} HTTP {status} ({size}B) ch={ch} img={img} wp={wp}")
    
    return results

async def main():
    async with httpx.AsyncClient(timeout=12, follow_redirects=True,
                                  headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'tr-TR,tr;q=0.9'}) as cl:
        
        sites = [
            ("https://www.mangawow.org", "solo-leveling", "mangawow"),
            ("https://www.ruyamanga2.com", "omniscient-reader", "ruyamanga2"),
            ("https://www.ruyamanga.net", "solo-leveling", "ruyamanga"),
            ("https://golgebahcesi.com", "solo-leveling", "golgebahcesi"),
        ]
        
        for base_url, slug, label in sites:
            await test_manga(cl, base_url, slug, label)
            await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(main())
