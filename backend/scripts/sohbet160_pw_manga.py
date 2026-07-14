
import asyncio
import re, os
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1280, 'height': 720})
        
        # Try monomanga
        print("=== MONOMANGA SOLO LEVELING ===")
        await page.goto("https://monomanga.com.tr/manga/solo-leveling/", wait_until='networkidle', timeout=30000)
        title = await page.title()
        print(f"Title: {title}")
        
        # Check for chapter links
        chapters = await page.evaluate('''() => {
            const links = document.querySelectorAll('a[href*="bolum"], a[href*="chapter"]');
            return Array.from(links).slice(0, 10).map(a => ({href: a.href, text: a.textContent.trim()}));
        }''')
        print(f"Chapter links found: {len(chapters)}")
        for ch in chapters[:5]:
            print(f"  {ch['text']}: {ch['href']}")
        
        # Screenshot
        await page.screenshot(path='/tmp/monomanga_listing.png')
        print("Screenshot saved")
        
        # Try a chapter
        if chapters:
            ch_url = chapters[0]['href']
            print(f"\nNavigating to: {ch_url}")
            await page.goto(ch_url, wait_until='networkidle', timeout=30000)
            title2 = await page.title()
            print(f"Chapter title: {title2}")
            
            # Check for images
            images = await page.evaluate('''() => {
                const imgs = document.querySelectorAll('img');
                return Array.from(imgs).slice(0, 20).map(img => ({
                    src: img.src,
                    width: img.naturalWidth,
                    height: img.naturalHeight,
                    visible: img.offsetWidth > 0
                }));
            }''')
            print(f"Images on chapter page: {len(images)}")
            for img in images[:10]:
                print(f"  {img['src'][:100]} ({img['width']}x{img['height']}, visible={img['visible']})")
            
            await page.screenshot(path='/tmp/monomanga_chapter.png')
            print("Chapter screenshot saved")
        
        await browser.close()

asyncio.run(main())
