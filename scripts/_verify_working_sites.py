"""
Test which manga sites actually serve real chapter content.
Uses httpx to download a chapter page and checks for image content.
"""
import httpx, asyncio, re, sys

SITES = {
    "merlintoon.com": "/seri/solo-leveling/bolum-1/",
    "mangawow.com": "/manga/solo-leveling/bolum-1/",
    "mangadenizi.com": "/manga/solo-leveling/bolum-1/",
    "hayalistic.com.tr": "/manga/solo-leveling/bolum-1/",
    "ragnarscans.com": "/manga/solo-leveling/bolum-1/",
    "ragnarscans.net": "/manga/solo-leveling/bolum-1/",
    "asurascans.com.tr": "/manga/solo-leveling/bolum-1/",
    "ruyamanga.com": "/manga/solo-leveling/bolum-1/",
    "turkmanga.net": "/manga/above-all-gods/bolum-640/",
    "mangaturk.org": "/manga/solo-leveling/bolum-1/",
}

async def check_site(domain, path):
    url = f"https://{domain}{path}"
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0",
                     "Accept": "text/html,*/*"}) as client:
            r = await client.get(url)
            body = r.text
            status = r.status_code
            ct = r.headers.get("content-type", "")[:40]
            redirect = str(r.url) if str(r.url) != url else ""
            has_images = any(x in body for x in [".jpg", ".png", "wp-content/uploads", "data-src=", "loading="])
            has_chapter_text = any(x in body.lower() for x in ["chapter", "bolum", "page-break"])
            has_title = "<title>" in body
            size = len(body)
            
            print(f"{domain}: {status} | {size}b | img={has_images} ch={has_chapter_text} title={has_title} | {ct[:30]}")
            if redirect:
                print(f"  -> {redirect[:80]}")
            if not has_images and not has_chapter_text:
                print(f"  [NO CONTENT] body[:200]: {body[:200]}")
    except Exception as e:
        print(f"{domain}: ERROR {e}")

async def main():
    print(f"Testing {len(SITES)} sites for real manga content...\n")
    for domain, path in SITES.items():
        await check_site(domain, path)
        await asyncio.sleep(0.5)

asyncio.run(main())
