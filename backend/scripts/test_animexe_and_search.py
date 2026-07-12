"""animexe.com yt-dlp test + acheriya/openani/codanime için doğru URL bul"""
import asyncio, json
from playwright.async_api import async_playwright

sites = {
    "acheriya.com": "https://acheriya.com/izle/naruto",
    "openani.me": "https://openani.me/",
    "codanime.net": "https://codanime.net/",
}

async def search_naruto(name: str, url: str) -> dict:
    """Site içinde ara / Naruto linklerini bul"""
    result = {"name": name, "naruto_links": [], "error": None}
    
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
            locale="tr-TR",
        )
        page = await ctx.new_page()
        try:
            await page.goto(url, timeout=30000, wait_until="load")
            await asyncio.sleep(3)
            
            # Get all links containing naruto
            links = await page.evaluate("""() => 
                Array.from(document.querySelectorAll('a[href*=\"naruto\" i]'))
                    .map(a => ({ href: a.href, text: a.textContent.trim().substring(0, 60) }))
            """)
            result["naruto_links"] = links[:20]
            
            # Try search if exists
            search_box = await page.query_selector('input[type="text"], input[type="search"], input[name="s"], input[name="search"]')
            if search_box:
                await search_box.fill("naruto")
                await search_box.press("Enter")
                await asyncio.sleep(3)
                search_links = await page.evaluate("""() => 
                    Array.from(document.querySelectorAll('a[href*=\"naruto\" i]'))
                        .map(a => ({ href: a.href, text: a.textContent.trim().substring(0, 60) }))
                """)
                result["search_links"] = search_links[:20]
            
        except Exception as e:
            result["error"] = str(e)
        await browser.close()
    return result

async def main():
    print("="*60)
    print("yt-dlp ile animexe.com testi")
    print("="*60)
    
    import subprocess
    result = subprocess.run(
        ["yt-dlp", "-s", "--print", "title", "--print", "duration", "--print", "url",
         "https://animexe.com/watch/naruto/1/1"],
        capture_output=True, text=True, timeout=60
    )
    print(f"stdout: {result.stdout}")
    print(f"stderr: {result.stderr[:500]}")
    print(f"returncode: {result.returncode}")
    
    # Try direct MP4
    print("\n" + "="*60)
    print("yt-dlp ile direct MP4 testi")
    print("="*60)
    result2 = subprocess.run(
        ["yt-dlp", "-s", "--print", "title", "--print", "format",
         "https://renjiabari.asia/file/tau-video/8f80f1f3-8643-46c1-b55f-b8af7277c7e1.mp4"],
        capture_output=True, text=True, timeout=30
    )
    print(f"stdout: {result2.stdout}")
    print(f"stderr: {result2.stderr[:500]}")
    
    # Explore other sites
    print("\n" + "="*60)
    print("Diğer sitelerde Naruto link ara")
    print("="*60)
    for name, url in sites.items():
        print(f"\n--- {name} ---")
        r = await search_naruto(name, url)
        for link in r.get("naruto_links", []):
            print(f"  {link.get('text',''):<50} {link.get('href','')[:100]}")
        for link in r.get("search_links", []):
            print(f"  [ARAMA] {link.get('text',''):<50} {link.get('href','')[:100]}")
        if r.get("error"):
            print(f"  HATA: {r['error']}")

asyncio.run(main())
