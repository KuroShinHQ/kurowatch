"""Check filmmodu page content for actual video player"""
import asyncio, httpx, re, os

async def main():
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as cl:
        r = await cl.get("https://filmmodu.org/film/esaretin-bedeli-izle/",
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                     'Accept-Language': 'tr-TR,tr;q=0.9'})
        print(f"Status: {r.status_code}, Size: {len(r.text)}")
        # Save to file for analysis
        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tmp_filmmodu.html")
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(r.text)
        print("Saved to /tmp/filmmodu_page.html")

        # Check key indicators
        checks = {
            "iframe": '<iframe' in r.text,
            "video tag": '<video' in r.text,
            "m3u8": '.m3u8' in r.text,
            "player": 'player' in r.text.lower(),
            "embed": 'embed' in r.text.lower(),
            "source": '<source' in r.text,
            "youtube": 'youtube' in r.text.lower() or 'youtu.be' in r.text,
            "recaptcha": 'recaptcha' in r.text.lower(),
            "hugedomains": 'hugedomains' in r.text.lower(),
            "for sale": 'for sale' in r.text.lower(),
            "film modu": 'film modu' in r.text.lower() or 'filmmodu' in r.text.lower(),
            "izle": 'izle' in r.text.lower(),
        }
        for k, v in checks.items():
            print(f"  {k}: {v}")

        # Find all scripts and their src URLs
        scripts = re.findall(r'<script[^>]*src="([^"]*)"', r.text)
        print(f"\nScripts ({len(scripts)}):")
        for s in scripts[:15]:
            print(f"  {s}")

        # Check for JSON-LD
        jsonlds = re.findall(r'<script type="application/ld\+json">([^<]+)</script>', r.text)
        print(f"\nJSON-LD: {len(jsonlds)}")
        for j in jsonlds[:3]:
            print(f"  {j[:200]}")

if __name__ == "__main__":
    asyncio.run(main())
