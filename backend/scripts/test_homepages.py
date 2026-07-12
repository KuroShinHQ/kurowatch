"""Anasayfa ve site yapısını kontrol et - doğru URL pattern'ini bul"""
import asyncio
from playwright.async_api import async_playwright

sites = {
    "tranimeizle.io": "https://www.tranimeizle.io/",
    "animexe.com": "https://animexe.com/",
    "animpow.com": "https://animpow.com/",
    "openani.me": "https://openani.me/",
    "codanime.net": "https://codanime.net/",
    "acheriya.com": "https://acheriya.com/",
}

async def test_homepage(name: str, url: str) -> dict:
    result = {"name": name, "url": url, "status": None, "final_url": None,
              "title": "", "naruto_links": [], "videos": 0, "iframes": [],
              "auth_required": False, "html_len": 0, "error": None}
    
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
            locale="tr-TR",
            viewport={"width": 1920, "height": 1080},
        )
        page = await ctx.new_page()
        
        try:
            resp = await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            result["status"] = resp.status if resp else None
            result["final_url"] = page.url
            result["title"] = await page.title()
            await asyncio.sleep(3)
            
            info = await page.evaluate("""() => {
                const links = Array.from(document.querySelectorAll('a[href*=\"naruto\" i]')).map(a => a.href.substring(0,120));
                const vids = document.querySelectorAll('video').length;
                const ifs = Array.from(document.querySelectorAll('iframe')).map(x => x.src.substring(0,100));
                const html = document.body.innerHTML.substring(0, 3000);
                return { links, videos: vids, iframes: ifs, html };
            }""")
            
            result["naruto_links"] = info.get("links", [])
            result["videos"] = info.get("videos", 0)
            result["iframes"] = info.get("iframes", [])
            result["html_len"] = len(info.get("html", ""))
            
            html_lower = info.get("html", "").lower()
            auth_kw = ["giriş yap", "kaydol", "üye ol", "login", "register", "oturum aç"]
            result["auth_required"] = any(k in html_lower for k in auth_kw)
            
        except Exception as e:
            result["error"] = str(e)
        
        await browser.close()
    
    return result

async def main():
    for name, url in sites.items():
        print(f"\n{'='*60}")
        print(f"Anasayfa: {name}")
        print(f"{'='*60}")
        
        result = await test_homepage(name, url)
        
        print(f"HTTP: {result['status']} | Final URL: {(result.get('final_url') or '')[:80]}")
        print(f"Title: {result.get('title','')[:100]}")
        print(f"Naruto linkleri: {result.get('naruto_links',[])[:5]}")
        print(f"Auth: {result.get('auth_required')}")
        if result.get('error'):
            print(f"ERROR: {result['error']}")

asyncio.run(main())
