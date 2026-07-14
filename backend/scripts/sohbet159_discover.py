"""SOHBET-159: Discover video URL patterns + movie sources"""
import asyncio, httpx, re, json

async def check(client, url, label):
    try:
        r = await client.get(url, timeout=20, follow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                     'Accept-Language': 'tr-TR,tr;q=0.9'})
        return label, r.status_code, len(r.text), r.text
    except Exception as e:
        return label, None, 0, str(e)

async def main():
    async with httpx.AsyncClient(timeout=20) as cl:
        # === ANIZM PAGE ANALYSIS ===
        print("=== ANIZM PAGE JS DATA ANALYSIS ===")
        _, _, size, html = await check(cl, "https://tranimeizle.org.tr/naruto-1-bolum-izle", "naruto ep")
        print(f"  Page size: {size} bytes")
        
        # Search for various patterns
        patterns = {
            'playerConfig': r'playerConfig\s*[=:]\s*({[^}]+})',
            'videoUrl': r'videoUrl["\']?\s*[=:]\s*["\']([^"\']+)["\']',
            'fileUrl': r'file["\']?\s*[=:]\s*["\']([^"\']+\.(?:mp4|m3u8))["\']',
            'source src': r'<source[^>]+src=["\']([^"\']+)["\']',
            'data-video': r'data-video=["\']([^"\']+)["\']',
            'embed_url': r'embed_url["\']?\s*[=:]\s*["\']([^"\']+)["\']',
            'iframe|embed': r'<(?:iframe|embed)[^>]+src=["\']([^"\']+)["\']',
            'window\.__NUXT__': r'window\.__NUXT__\s*=\s*({.*?});',
            'window\.__DATA__': r'window\.__DATA__\s*=\s*({.*?});',
            'script type="application/json"': r'<script[^>]+type=["\']application/json["\'][^>]*>(.*?)</script>',
        }
        
        for name, pattern in patterns.items():
            matches = re.findall(pattern, html, re.DOTALL)
            for m in matches[:3]:
                truncated = str(m)[:150]
                print(f"  {name:40s}: {truncated}")
        
        # Also check if there's a JSON blob with episode data
        script_pattern = r'<script[^>]*>(.*?)</script>'
        scripts = re.findall(script_pattern, html, re.DOTALL)
        for i, script in enumerate(scripts):
            if any(kw in script.lower() for kw in ['player', 'video', 'source', 'stream', 'embed', 'episode', 'iframe']):
                print(f"\n  Script {i} (video-related, {len(script)} chars):")
                print(f"    {script[:300]}...")
                if len(script) > 300:
                    print(f"    ...({len(script)-300} more chars)")

        # === NEW MOVIE SITES ===
        print("\n\n=== NEW MOVIE SITE TESTS ===")
        movie_sites = [
            ("https://www.hdfilmcehennemi.sh/american-psycho/", "hdfc.sh american psycho"),
            ("https://hdfilmcehennemi.mobi/", "hdfc.mobi homepage"),
            ("https://hdfilmcehennemi.mobi/american-psycho/", "hdfc.mobi american psycho"),
            ("https://hdfilmcehennemi.mobi/film/american-psycho/", "hdfc.mobi/film/"),
            ("https://www.fullhdfilmizlesene.pw/", "fullhdfilmizlesene"),
            ("https://www.fullhdfilmizlesene.pw/film/3-idiots-izle/", "fullhd 3 idiots"),
            ("https://www.filmmodu.org/", "filmmodu"),
            ("https://www.filmmodu.org/3-idiots-izle/", "filmmodu 3 idiots"),
            ("https://dizimag.com.tr/film/", "dizimag film (bellki)"),
            ("https://www.hdfilmcehennemi.nl/american-psycho/", "hdfc.nl american psycho"),
            ("https://filmizle.com/", "filmizle"),
            ("https://www.filmizlesene.pw/", "filmizlesene"),
        ]
        for url, label in movie_sites:
            try:
                r = await cl.get(url, timeout=15, follow_redirects=True,
                    headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'tr-TR,tr;q=0.9'})
                has_video = bool(re.findall(r'<(?:iframe|video|source)', r.text))
                print(f"  {label:45s} HTTP {r.status_code} ({len(r.text)}B) video:{has_video}")
            except Exception as e:
                print(f"  {label:45s} ERROR: {str(e)[:60]}")

        # === DIZIMAG EPISODE DATA ===
        print("\n\n=== DIZIMAG EPISODE PAGE ===")
        _, _, _, html = await check(cl, "https://www.dizimag.com.tr/dizi/breaking-bad/", "breaking bad")
        # Look for episode links
        links = re.findall(r'href=["\']([^"\']*/bolum[^"\']*)["\']', html, re.IGNORECASE)
        print(f"  Episode links found: {len(links)}")
        for link in links[:10]:
            print(f"    {link}")
        
        # Look for season/episode data
        sezon_links = re.findall(r'href=["\']([^"\']*(?:sezon|season|bolum|episode)[^"\']*)["\']', html, re.IGNORECASE)
        print(f"  Season/Episode links: {len(sezon_links)}")
        for link in sezon_links[:10]:
            print(f"    {link}")

if __name__ == "__main__":
    asyncio.run(main())
