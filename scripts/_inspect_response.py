"""
Inspect what mangatr.net actually returns.
"""
import httpx, asyncio

async def main():
    async with httpx.AsyncClient(timeout=10, follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0",
                 "Accept": "text/html,*/*",
                 "Accept-Language": "tr-TR,tr;q=0.9"}) as client:
        
        # Test 1: Solo Leveling chapter page
        r = await client.get("https://mangatr.net/manga/solo-leveling/bolum-1/")
        print(f"=== MANGA SOLO LEVELING Ch1 ===")
        print(f"Status: {r.status_code}")
        print(f"Headers: {dict(r.headers)}")
        print(f"Body ({len(r.text)}b):")
        print(r.text[:1500])
        print("...")

asyncio.run(main())
