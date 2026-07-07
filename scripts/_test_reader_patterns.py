"""Find actual reader URLs on Next.js manga sites"""
import asyncio, httpx, re

async def main():
    client = httpx.AsyncClient(timeout=12, follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0"})
    
    # Try reader URLs on monomanga
    base = "https://monomanga.com.tr"
    print("=== monomanga.com.tr reader patterns ===")
    patterns = [
        "/manga/solo-leveling/bolum-1",
        "/manga/solo-leveling/bolum/1",
        "/manga/solo-leveling/1",
        "/manga/solo-leveling/bolum-1-bolum",
        "/seri/solo-leveling/bolum-1",
        "/oku/solo-leveling/bolum-1",
        "/oku/solo-leveling/1",
        "/read/solo-leveling/1",
        "/manga/solo-leveling/bolum-1/",
        "/manga/solo-leveling/bolum/1/",
    ]
    for p in patterns:
        url = f"{base}{p}"
        try:
            r = await client.get(url, timeout=8)
            body = r.text
            has_imgs = any(x in body.lower() for x in [".jpg", ".png", "wp-content/uploads", "data-src=", "<img", "page-break", "chapter"])
            print(f"  {p:50s} -> {r.status_code}, {len(body):>6}B, imgs={has_imgs}")
        except Exception as e:
            print(f"  {p:50s} -> ERR: {str(e)[:40]}")
    
    # Try to find Next.js API routes  
    print("\n=== Next.js API routes ===")
    api_urls = [
        "/api/manga/solo-leveling",
        "/api/manga/solo-leveling/1",
        "/api/manga/solo-leveling/chapters",
        "/_next/data/development/manga/solo-leveling.json",
        "/_next/data/development/manga/solo-leveling/bolum-1.json",
        "/api/chapter/solo-leveling/1",
        "/api/series/solo-leveling",
        "/api/series/solo-leveling/chapters",
    ]
    for p in api_urls:
        url = f"{base}{p}"
        try:
            r = await client.get(url, timeout=8)
            has_imgs = any(x in r.text.lower() for x in [".jpg", ".png", "wp-content", "chapter", "bolum"])
            print(f"  {p:50s} -> {r.status_code}, {len(r.text):>6}B, json={has_imgs}")
        except Exception as e:
            print(f"  {p:50s} -> ERR: {str(e)[:40]}")
    
    # Now test mangaoku.com.tr
    print("\n=== mangaoku.com.tr reader patterns ===")
    base = "https://mangaoku.com.tr"
    patterns = [
        "/manga/solo-leveling/bolum-1",
        "/manga/solo-leveling/bolum/1",
        "/manga/solo-leveling/1",
        "/oku/solo-leveling/1",
        "/read/solo-leveling/1",
    ]
    for p in patterns:
        url = f"{base}{p}"
        try:
            r = await client.get(url, timeout=8)
            body = r.text
            has_imgs = any(x in body.lower() for x in [".jpg", ".png", "wp-content/uploads", "data-src=", "<img", "page-break", "chapter"])
            print(f"  {p:50s} -> {r.status_code}, {len(body):>6}B, imgs={has_imgs}")
        except Exception as e:
            print(f"  {p:50s} -> ERR: {str(e)[:40]}")
    
    # golgebahcesi.com - check skycdn
    print("\n=== golgebahcesi.com reader patterns ===")
    base = "https://golgebahcesi.com"
    patterns = [
        "/manga/solo-leveling/bolum-1",
        "/manga/solo-leveling/bolum/1",
        "/manga/solo-leveling/1",
        "/oku/solo-leveling/bolum-1",
        "/oku/solo-leveling/1",
        "/bolum/solo-leveling/1",
    ]
    for p in patterns:
        url = f"{base}{p}"
        try:
            r = await client.get(url, timeout=8)
            body = r.text
            has_imgs = any(x in body.lower() for x in [".jpg", ".png", "wp-content/uploads", "data-src=", "<img", "page-break", "chapter", "skycdn"])
            print(f"  {p:50s} -> {r.status_code}, {len(body):>6}B, imgs={has_imgs}")
        except Exception as e:
            print(f"  {p:50s} -> ERR: {str(e)[:40]}")
    
    await client.aclose()

asyncio.run(main())
