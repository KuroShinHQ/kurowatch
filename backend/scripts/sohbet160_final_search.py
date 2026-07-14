"""Final creative search for movie sources + test monomanga download"""
import asyncio, httpx, re, os, sys, json

script_dir = os.path.dirname(os.path.abspath(__file__))

async def check(client, url, label):
    try:
        r = await client.get(url, timeout=12, follow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'tr-TR,tr;q=0.9'})
        return label, r.status_code, len(r.text), '<iframe' in r.text, r.text[:300]
    except Exception as e:
        return label, None, 0, False, str(e)[:60]

async def main():
    async with httpx.AsyncClient(timeout=12, limits=httpx.Limits(max_keepalive_connections=3, max_connections=3),
                                  headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'tr-TR,tr;q=0.9'}) as cl:
        
        tests = [
            # hdfc API discovery  
            ("https://www.hdfilmcehennemi.sh/wp-json/", "wp-json root"),
            ("https://www.hdfilmcehennemi.sh/wp-json/wp/v2/types/post", "wp post types"),
            ("https://www.hdfilmcehennemi.sh/wp-json/wp/v2/posts?per_page=5", "wp posts"),
            # Alternative .nl paths
            ("https://www.hdfilmcehennemi.nl/", "nl homepage"),
            ("https://www.hdfilmcehennemi.nl/american-psycho/", "nl american-psycho"),
            ("https://www.hdfilmcehennemi.nl/film-robotu-1/", "nl film robotu"),
            # Try .nl with different URL patterns from search results
            ("https://www.hdfilmcehennemi.nl/maxxxine-30/", "nl maxxxine"),
            ("https://www.hdfilmcehennemi.nl/popeye-the-slayer-man/", "nl popeye"),
            ("https://www.hdfilmcehennemi.nl/your-host/", "nl your-host"),
            ("https://www.hdfilmcehennemi.nl/in-a-violent-nature-24/", "nl violent nature"),
            # Try .io variants
            ("https://www.hdfilmcehennemi.io/american-psycho/", "io american-psycho"),
            ("https://www.hdfilmcehennemi.io/film-robotu-1/", "io film robotu"),
            # Check if any of the known movies exist on .nl with their exact slug
            ("https://www.hdfilmcehennemi.nl/the-collector/", "nl the-collector"),
            ("https://www.hdfilmcehennemi.nl/howls-moving-castle/", "nl howls"),
            ("https://www.hdfilmcehennemi.nl/wall-e/", "nl wall-e"),
            ("https://www.hdfilmcehennemi.nl/shark-tale/", "nl shark-tale"),
            # Try fullhdfilmizlesene.pw with different patterns
            ("https://www.fullhdfilmizlesene.pw/american-psycho-izle/", "fullhd ap-izle"),
            ("https://www.fullhdfilmizlesene.pw/american-psycho/", "fullhd ap"),
            # New: hdfilmcehennemi3.com
            ("https://www.hdfilmcehennemi3.com/american-psycho/", "hdfc3 ap"),
            ("https://www.hdfilmcehennemi3.com/", "hdfc3 homepage"),
        ]

        print("=== FINAL MOVIE SOURCE SCAN ===")
        for url, label in tests:
            lbl, status, size, has_iframe, text = await check(cl, url, label)
            ok = status == 200 and size > 5000
            icon = "✅" if ok and has_iframe else ("✅" if ok else "❌") 
            print(f"  {icon} {label:30s} HTTP {status} ({size}B) iframe={has_iframe}")
            await asyncio.sleep(0.3)

        # Now test monomanga for 1 manga download
        print("\n=== MONOMANGA DOWNLOAD TEST ===")
        from urllib.parse import urljoin
        
        # Get a manga chapter page from monomanga
        r = await cl.get("https://monomanga.com.tr/manga/martial-peak/bolum-1/")
        print(f"Martial Peak Ch.1: HTTP {r.status_code} ({len(r.text)}B)")
        
        if r.status_code == 200:
            # Check for image sources
            imgs = re.findall(r'<img[^>]+src="([^"]*)"', r.text)
            print(f"Images found: {len(imgs)}")
            for img in imgs[:5]:
                print(f"  {img[:100]}")
            # Check for chapter content
            has_pages = 'page' in r.text.lower() or 'chapter' in r.text.lower() or 'chapter' in r.text.lower()
            print(f"Has chapter content: {has_pages}")
            # Save for analysis
            save_path = os.path.join(script_dir, "..", "..", "tmp_monomanga_ch1.html")
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(r.text)
            print(f"Saved to {save_path}")
        
        # Also test a manhwa
        r2 = await cl.get("https://monomanga.com.tr/manga/a-returners-magic-should-be-special/bolum-1/")
        print(f"\nA Returner's Magic Ch.1: HTTP {r2.status_code} ({len(r2.text)}B)")

if __name__ == "__main__":
    asyncio.run(main())
