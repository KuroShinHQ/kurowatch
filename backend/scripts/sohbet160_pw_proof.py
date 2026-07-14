"""Enhanced Playwright: scroll manga + click play on movie"""
import asyncio, json, os
from playwright.async_api import async_playwright

async def main():
    downloads_dir = "/mnt/c/Kuroshin/kurowatch/downloads"
    os.makedirs(downloads_dir, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        # === MANGAWOW ===
        print("=== MANGAWOW: SOLO LEVELING CH.1 ===")
        await page.goto("https://www.mangawow.org/manga/solo-leveling/chapter-1/", wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(2000)
        
        # Scroll to load lazy images
        for i in range(10):
            await page.evaluate(f'window.scrollTo(0, {i * 800})')
            await page.wait_for_timeout(1000)
        
        # Get all visible images
        images = await page.evaluate('''() => {
            const imgs = document.querySelectorAll('img');
            const results = [];
            imgs.forEach((img, i) => {
                const rect = img.getBoundingClientRect();
                if (img.naturalWidth > 100 && img.naturalHeight > 100 && !img.src.includes('logo') && !img.src.includes('icon')) {
                    results.push({
                        index: i,
                        src: img.src,
                        width: img.naturalWidth,
                        height: img.naturalHeight,
                        visible: rect.top < window.innerHeight && rect.bottom > 0
                    });
                }
            });
            return results;
        }''')
        print(f"Manga images found: {len(images)}")
        for img in images[:10]:
            print(f"  [{img['index']}] {img['src'][:100]}")
        
        # Try to download one image as proof
        if images:
            import subprocess
            img_url = images[0]['src']
            outpath = f"{downloads_dir}/manga_proof.jpg"
            proc = subprocess.run(['curl', '-s', '-o', outpath, '-L', img_url], capture_output=True)
            if os.path.exists(outpath) and os.path.getsize(outpath) > 10000:
                print(f"Downloaded manga image: {outpath} ({os.path.getsize(outpath)}B)")
            else:
                print(f"Download failed or too small")
        
        await page.screenshot(path=f"{downloads_dir}/mangawow_scrolled.png", full_page=True)
        print("Screenshot saved after scroll")
        
        # === HDFC ===
        print("\n=== HDFC.NL: AMERICAN PSYCHO ===")
        await page.goto("https://www.hdfilmcehennemi.nl/american-psycho-6/", wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(3000)
        
        # Try clicking all buttons/links that say "izle", "play", "oynat"
        buttons = await page.evaluate('''() => {
            const elements = document.querySelectorAll('a, button, div[role="button"]');
            const playButtons = [];
            elements.forEach(el => {
                const text = (el.textContent || '').toLowerCase().trim();
                const className = (el.className || '').toLowerCase();
                if (text.includes('izle') || text.includes('play') || text.includes('oynat') || 
                    className.includes('play') || className.includes('izle')) {
                    playButtons.push({
                        tag: el.tagName,
                        text: el.textContent.trim(),
                        className: el.className,
                        visible: el.offsetWidth > 0
                    });
                }
            });
            return playButtons;
        }''')
        print(f"Play buttons found: {len(buttons)}")
        for b in buttons:
            print(f"  {b['tag']}: {b['text'][:30]} class={b['className'][:30]}")
        
        # Try clicking first play button
        for i in range(len(buttons)):
            try:
                btn = page.locator(f'text={buttons[i]["text"]}').first
                if await btn.is_visible():
                    await btn.click()
                    print(f"Clicked: {buttons[i]['text']}")
                    await page.wait_for_timeout(3000)
                    break
            except:
                pass
        
        # Check if iframe has src now
        iframe_info = await page.evaluate('''() => {
            const iframes = document.querySelectorAll('iframe');
            return Array.from(iframes).map(f => ({
                src: f.src,
                id: f.id,
                visible: f.offsetWidth > 0
            }));
        }''')
        print(f"Iframes after click: {iframe_info}")
        
        await page.screenshot(path=f"{downloads_dir}/hdfc_after_click.png", full_page=True)
        
        # Try yt-dlp on the full page
        print("\n=== yt-dlp on hdfc page ===")
        proc = await asyncio.create_subprocess_exec(
            'wsl', '-e', 'bash', '-c',
            f'cd /mnt/c/Kuroshin/kurowatch/downloads && source /root/kuroshin/venv/bin/activate && yt-dlp --referer "https://www.hdfilmcehennemi.nl/" --user-agent "Mozilla/5.0" --dump-json "https://www.hdfilmcehennemi.nl/american-psycho-6/" 2>&1',
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        out = stdout.decode()
        if 'm3u8' in out or 'mp4' in out:
            print(f"yt-dlp found video: {out[:500]}")
        else:
            print(f"yt-dlp output: {out[:500]}")
        
        await browser.close()
        print("\nDONE")

if __name__ == "__main__":
    asyncio.run(main())
