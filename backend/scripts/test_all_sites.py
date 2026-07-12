"""Test all Turkish anime sites user provided for Naruto S01E01"""
import asyncio
from playwright.async_api import async_playwright

# Naruto S01E01 URL patterns for each site
naruto_urls = {
    "tranimeizle.io": "https://www.tranimeizle.io/naruto-1-bolum-izle",
    "animexe.com": "https://animexe.com/naruto-1-bolum-izle",
    "animpow.com": "https://animpow.com/naruto-1-bolum-izle",
    "openani.me": "https://openani.me/naruto-1-bolum-izle",
    "codanime.net": "https://codanime.net/turkce-anime-izle/naruto-1-bolum-izle",
    "acheriya.com": "https://acheriya.com/naruto-1-bolum-izle",
}

async def test_site(name: str, url: str) -> dict:
    """Playwright ile siteyi test et: video var mı? login gerekli mi?"""
    result = {"name": name, "url": url, "status": None, "final_url": None,
              "videos": 0, "iframes": [], "video_urls": [], "auth_required": False,
              "error": None, "html_len": 0, "title": ""}
    
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
            locale="tr-TR",
            viewport={"width": 1920, "height": 1080},
        )
        page = await ctx.new_page()
        
        network_videos = []
        page.on("request", lambda req: network_videos.append(req.url) if any(k in req.url.lower() for k in (".m3u8", ".mp4", "manifest")) else None)
        
        try:
            resp = await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            result["status"] = resp.status if resp else None
            result["final_url"] = page.url
            result["title"] = await page.title()
            
            # Wait for page load
            for i in range(12):
                await asyncio.sleep(2)
                
                info = await page.evaluate("""() => {
                    const vids = Array.from(document.querySelectorAll('video')).map(v => ({
                        src: v.src || v.currentSrc,
                        readyState: v.readyState
                    }));
                    const ifs = Array.from(document.querySelectorAll('iframe')).filter(x => x.src).map(x => x.src.substring(0,100));
                    return {
                        videos: vids,
                        iframes: ifs,
                        html: document.body.innerHTML.substring(0, 2000)
                    };
                }""")
                
                html_lower = (info.get("html") or "").lower()
                auth_indicators = ["giriş yap", "kaydol", "üye ol", "login", "register", "triangle-alert", "lucide-alert", "oturum"]
                has_auth = any(k in html_lower for k in auth_indicators)
                has_video = len(info.get("videos", [])) > 0
                has_iframe = any("player" in (f or "") or "embed" in (f or "") for f in info.get("iframes", []))
                
                if i == 11 or has_video or (has_iframe and not has_auth):
                    result["videos"] = len(info.get("videos", []))
                    result["iframes"] = info.get("iframes", [])
                    result["video_urls"] = list(set(network_videos))
                    result["auth_required"] = has_auth
                    result["html_len"] = len(info.get("html", ""))
                    print(f"  Cycle {i+1}: videos={len(info.get('videos',[]))} iframes={len(info.get('iframes',[]))} auth={has_auth}")
                    break
        except Exception as e:
            result["error"] = str(e)
        
        await browser.close()
    
    return result

async def main():
    for name, url in naruto_urls.items():
        print(f"\n{'='*60}")
        print(f"Testing: {name}")
        print(f"URL: {url}")
        print(f"{'='*60}")
        
        result = await test_site(name, url)
        
        print(f"HTTP: {result['status']} | Final URL: {(result.get('final_url') or '')[:80]}")
        print(f"Title: {result.get('title','')[:80]}")
        print(f"Videos in DOM: {result['videos']}")
        print(f"Iframes: {result['iframes']}")
        print(f"Network video URLs: {result.get('video_urls',[])}")
        print(f"Auth required: {result.get('auth_required')}")
        if result.get('error'):
            print(f"ERROR: {result['error']}")
        
        has_working_video = (
            result["videos"] > 0 or 
            len(result.get("video_urls", [])) > 0
        ) and not result["auth_required"]
        
        if has_working_video:
            print(f"\n✅ {name}: VIDEO BULUNDU!")
        elif result["auth_required"]:
            print(f"\n⚠️  {name}: OTURUM GEREKLİ")
        elif result["error"]:
            print(f"\n❌ {name}: HATA - {result['error']}")
        else:
            print(f"\n❌ {name}: Video bulunamadı")

asyncio.run(main())
