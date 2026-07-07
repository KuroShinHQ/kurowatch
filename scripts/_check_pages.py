"""
Verify if mangatr.net URLs actually serve chapter content.
"""
import httpx, asyncio, re

async def check(url, label):
    async with httpx.AsyncClient(timeout=10, follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0"}) as client:
        r = await client.get(url)
        body = r.text
        has_content = any(x in body for x in ["page-break", "reading-content", "wp-content", "manga-reader", "chapter-reader"])
        has_images = any(x in body for x in ["data-src=", "wp-content/uploads", ".jpg", ".png", "loading=\"lazy\""])
        title_tag = ""
        m = re.search(r"<title>(.*?)</title>", body[:2000], re.IGNORECASE | re.DOTALL)
        if m:
            title_tag = m.group(1)[:80]
        status = r.status_code
        print(f"{label}: {status} has_content={has_content} images={has_images}")
        print(f"  Title: {title_tag}")
        print(f"  Size: {len(body)}b")

async def main():
    checks = [
        ("https://mangatr.net/manga/solo-leveling/bolum-1/", "SOLO 1 (good)"),
        ("https://mangatr.net/manga/solo-leveling/bolum-2/", "SOLO 2 (good)"),
        ("https://mangatr.net/manga/14/bolum-1/", "#13 slug=14"),
        ("https://mangatr.net/manga/22/bolum-1/", "#35 slug=22"),
        ("https://mangatr.net/manga/the-greatest-estate-developer/bolum-1/", "#13 correct EN"),
        ("https://mangatr.net/manga/dunyanin-en-iyi-muhendisi/bolum-1/", "#13 correct TR"),
        ("https://mangatr.net/manga/kaderin-zirvesi/bolum-1/", "#35 TR slug"),
        ("https://mangatr.net/manga/1/bolum-1/", "TRASH slug=1"),
        ("https://mangatr.net/manga/999999/bolum-1/", "TRASH slug=999999"),
    ]
    for url, label in checks:
        await check(url, label)
        await asyncio.sleep(0.5)

asyncio.run(main())
