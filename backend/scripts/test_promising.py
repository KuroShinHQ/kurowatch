"""Promising sitelerin detaylı testi - Naruto S01E01 video var mı?"""
import asyncio
from playwright.async_api import async_playwright

naruto_urls = {
    "animexe.com": "https://animexe.com/watch/naruto/1/1",
    "acheriya.com": "https://acheriya.com/izle/naruto",
}

async def deep_test(name: str, url: str, **kw) -> dict:
    result = {"name": name, "url": url, "status": None, "final_url": None,
              "title": "", "videos": 0, "video_details": [], "iframes": [],
              "network_m3u8": [], "network_mp4": [], "auth_required": False,
              "error": None}
    
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
            locale="tr-TR",
            viewport={"width": 1920, "height": 1080},
        )
        page = await ctx.new_page()
        
        network_videos = []
        def on_request(req):
            u = req.url.lower()
            if any(k in u for k in (".m3u8", ".mp4", "manifest")):
                network_videos.append(req.url)
                print(f"  [NET] {req.url[:100]}")
        page.on("request", on_request)
        
        try:
            resp = await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            result["status"] = resp.status if resp else None
            result["final_url"] = page.url
            result["title"] = await page.title()
            
            # Wait and poll for up to 30s
            for i in range(15):
                await asyncio.sleep(2)
                
                info = await page.evaluate("""() => {
                    const vids = Array.from(document.querySelectorAll('video')).map(v => ({
                        src: v.src || v.currentSrc || '',
                        readyState: v.readyState,
                        duration: v.duration,
                        networkState: v.networkState,
                        error: v.error ? v.error.message : null,
                        rect: v.getBoundingClientRect()
                    }));
                    const ifs = Array.from(document.querySelectorAll('iframe')).filter(x => x.src).map(x => x.src.substring(0, 120));
                    const html = document.body.innerHTML.substring(0, 3000);
                    return { videos: vids, iframes: ifs, html };
                }""")
                
                has_video = any(v.get("src") for v in info.get("videos", []))
                has_player_iframe = any("player" in (f or "").lower() or "embed" in (f or "").lower() for f in info.get("iframes", []))
                
                html_lower = info.get("html", "").lower()
                auth_kw = ["giriş yap", "kaydol", "üye ol", "login", "register", "oturum aç"]
                
                if i == 14 or has_video or has_player_iframe:
                    result["videos"] = len(info.get("videos", []))
                    result["video_details"] = info.get("videos", [])
                    result["iframes"] = info.get("iframes", [])
                    result["network_m3u8"] = [u for u in network_videos if ".m3u8" in u.lower()]
                    result["network_mp4"] = [u for u in network_videos if ".mp4" in u.lower()]
                    result["auth_required"] = any(k in html_lower for k in auth_kw)
                    print(f"  Cycle {i+1}: videos={len(info.get('videos',[]))} iframes={len(info.get('iframes',[]))} auth={result['auth_required']}")
                    break
            
        except Exception as e:
            result["error"] = str(e)
        
        await browser.close()
    
    return result

async def main():
    for name, url in naruto_urls.items():
        print(f"\n{'='*60}")
        print(f"DEEP TEST: {name}")
        print(f"URL: {url}")
        print(f"{'='*60}")
        
        result = await deep_test(name, url)
        
        print(f"\nHTTP: {result['status']} | Final: {(result.get('final_url') or '')[:80]}")
        print(f"Title: {result.get('title','')[:100]}")
        print(f"Videos in DOM: {result['videos']}")
        for v in result.get("video_details", []):
            print(f"  -> src={v.get('src','')[:80]} readyState={v.get('readyState')} dur={v.get('duration')}")
        print(f"Iframes: {result.get('iframes',[])}")
        print(f"Network m3u8: {result.get('network_m3u8',[])}")
        print(f"Auth: {result.get('auth_required')}")
        if result.get('error'):
            print(f"ERROR: {result['error']}")
        
        has_video = result['videos'] > 0 and any(v.get("src") for v in result.get("video_details", []))
        has_network = len(result.get("network_m3u8", [])) > 0 or len(result.get("network_mp4", [])) > 0
        has_player_iframe = any("player" in (f or "").lower() or "embed" in (f or "").lower() for f in result.get("iframes", []))
        
        if has_video or has_network:
            print(f"\n✅ {name}: VIDEO VAR!")
        elif result["auth_required"]:
            print(f"\n⚠️  {name}: OTURUM GEREKLİ")
        elif has_player_iframe:
            print(f"\n🔍 {name}: Player iframe var - embed kontrol et")
            for f in result.get("iframes", []):
                if "player" in f.lower() or "embed" in f.lower():
                    print(f"  -> {f}")
        else:
            print(f"\n❌ {name}: Video yok")

asyncio.run(main())
