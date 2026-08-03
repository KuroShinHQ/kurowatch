"""SOHBET-158: Test downloads from new sites"""
import asyncio, httpx, re, os

DOWNLOAD_DIR = '/mnt/c/Kuroshin/kurowatch/temp/sohbet158_test'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

async def test():
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as cl:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'tr-TR,tr;q=0.9',
        }
        
        # TEST 1: Anizm (tranimeizle) anime page
        print("=== TEST 1: Anizm Anime Page ===")
        r = await cl.get("https://tranimeizle.org.tr/naruto/", headers=headers)
        print(f"  Naruto page: HTTP {r.status_code} ({len(r.text)} bytes)")
        
        # Look for video/iframe in the page
        iframes = re.findall(r'<iframe[^>]*src=["\']([^"\']+)["\']', r.text)
        videos = re.findall(r'<video[^>]*src=["\']([^"\']+)["\']', r.text)
        print(f"  Iframes found: {len(iframes)}")
        print(f"  Video tags: {len(videos)}")
        for iframe in iframes[:3]:
            print(f"    Iframe: {iframe[:100]}")
        
        # TEST 2: Dizimag Series Page
        print("\n=== TEST 2: Dizimag Series Page ===")
        r = await cl.get("https://www.dizimag.com.tr/dizi/dexter/", headers=headers)
        print(f"  Dexter page: HTTP {r.status_code} ({len(r.text)} bytes)")
        episodes = re.findall(r'href=["\']([^"\']*(?:bolum|episode|sezon)[^"\']*)["\']', r.text)
        print(f"  Episode links found: {len(episodes)}")
        for ep in episodes[:5]:
            print(f"    Ep link: {ep[:80]}")
        
        # TEST 3: Anizm Episode Page
        print("\n=== TEST 3: Anizm Episode Page ===")
        r = await cl.get("https://tranimeizle.org.tr/naruto-1-bolum-izle", headers=headers)
        print(f"  Naruto ep1: HTTP {r.status_code} ({len(r.text)} bytes)")
        iframes = re.findall(r'<iframe[^>]*src=["\']([^"\']+)["\']', r.text)
        videos = re.findall(r'<video[^>]*src=["\']([^"\']+)["\']', r.text)
        print(f"  Iframes: {len(iframes)}, Videos: {len(videos)}")
        # Look for any data-* attributes with video URLs
        data_vids = re.findall(r'data-[^=]*=["\']([^"\']*\.(?:mp4|m3u8)[^"\']*)["\']', r.text)
        sources = re.findall(r'<source[^>]*src=["\']([^"\']+)["\']', r.text)
        print(f"  Data-video: {len(data_vids)}, Sources: {len(sources)}")
        
        # TEST 4: hdfilmcehennemi.sh movie page (American Psycho - known working)
        print("\n=== TEST 4: hdfilmcehennemi.sh Movie Page ===")
        r = await cl.get("https://www.hdfilmcehennemi.sh/american-psycho/", headers=headers)
        print(f"  American Psycho: HTTP {r.status_code} ({len(r.text)} bytes)")
        iframes = re.findall(r'<iframe[^>]*src=["\']([^"\']+)["\']', r.text)
        print(f"  Iframes: {len(iframes)}")
        for iframe in iframes[:3]:
            print(f"    Iframe: {iframe[:100]}")

if __name__ == "__main__":
    asyncio.run(test())
