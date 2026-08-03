"""SOHBET-159: Extract video URL from Anizm page using Playwright"""
import asyncio, re, json, os
DOWNLOAD_DIR = '/mnt/c/Kuroshin/kurowatch/temp/sohbet159_test'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

async def extract_and_download():
    """Use Playwright to extract video URL from Anizm and download"""
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.set_default_timeout(30000)
        
        # Intercept responses to find video URLs
        video_urls = []
        
        async def on_response(response):
            url = response.url
            if '.m3u8' in url or '.mp4' in url:
                video_urls.append(url)
                print(f"  🎬 Video response: {url}")
            if 'iframe' in url.lower() or 'embed' in url.lower():
                print(f"  🔗 Embed/iframe response: {url}")
        
        page.on('response', on_response)
        
        try:
            print("  Loading Anizm page...")
            await page.goto("https://tranimeizle.org.tr/naruto-1-bolum-izle", 
                          wait_until='networkidle', timeout=30000)
            print(f"  Page loaded. Title: {await page.title()}")
            
            # Wait for any video elements
            await page.wait_for_timeout(5000)
            
            # Try to get video from iframes
            iframes = page.frame_locator('iframe')
            
            # Get page content after JS execution
            html = await page.content()
            
            # Search for video URLs in HTML
            patterns = [
                r'(https?://[^"\']+\.(?:m3u8|mp4)[^"\']*)',
                r'file["\']?\s*[=:]\s*["\']([^"\']+\.(?:m3u8|mp4))["\']',
                r'videoUrl["\']?\s*[=:]\s*["\'](https?://[^"\']+)["\']',
                r'src=["\'](https?://[^"\']+\.(?:m3u8|mp4)[^"\']*)["\']',
            ]
            
            for pattern in patterns:
                found = re.findall(pattern, html, re.IGNORECASE)
                for url in found[:5]:
                    print(f"  📄 Found in HTML: {url}")
                    video_urls.append(url)
            
            # Try Playwright native video detection
            videos = await page.query_selector_all('video')
            print(f"  <video> tags: {len(videos)}")
            for v in videos:
                src = await v.get_attribute('src')
                if src:
                    print(f"  🎥 Video src: {src}")
                    video_urls.append(src)
            
            iframes = await page.query_selector_all('iframe')
            print(f"  <iframe> tags: {len(iframes)}")
            for ifr in iframes:
                src = await ifr.get_attribute('src')
                if src:
                    print(f"  🔗 Iframe src: {src[:120]}")
            
            # Look for JSON data in page
            texts = await page.query_selector_all('script')
            for script in texts:
                content = await script.inner_html()
                if 'player' in content.lower() or 'video' in content.lower() or 'source' in content.lower():
                    matches = re.findall(r'(https?://[^"\']+\.(?:m3u8|mp4)[^"\']*)', content, re.IGNORECASE)
                    for url in matches:
                        print(f"  📜 Script video URL: {url}")
                        video_urls.append(url)
            
            # If we found video URLs, try to download one
            if video_urls:
                target_url = video_urls[0]
                print(f"\n  Downloading: {target_url[:100]}")
                import httpx
                async with httpx.AsyncClient(timeout=60) as cl:
                    try:
                        r = await cl.get(target_url)
                        if r.status_code == 200:
                            ext = '.m3u8' if '.m3u8' in target_url else '.mp4'
                            fname = f"naruto_ep1{ext}"
                            fpath = os.path.join(DOWNLOAD_DIR, fname)
                            with open(fpath, 'wb') as f:
                                f.write(r.content)
                            print(f"  ✅ Downloaded: {len(r.content)} bytes -> {fpath}")
                            
                            # For m3u8, show playlist content
                            if '.m3u8' in target_url:
                                print(f"  📋 Playlist (first 500 chars): {r.text[:500]}")
                        else:
                            print(f"  ❌ HTTP {r.status_code}: {target_url[:80]}")
                    except Exception as e:
                        print(f"  ❌ Download error: {e}")
            else:
                print("  ❌ No video URLs found")
                
                # Save HTML for offline analysis
                with open(os.path.join(DOWNLOAD_DIR, 'naruto_ep1.html'), 'w', encoding='utf-8') as f:
                    f.write(html)
                print(f"  HTML saved for analysis: {len(html)} bytes")
        
        except Exception as e:
            print(f"  ❌ Playwright error: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(extract_and_download())
