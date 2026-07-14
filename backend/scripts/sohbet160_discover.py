"""Fix monomanga redirect test + explore hdfc movie catalog"""
import asyncio, httpx, re, os

script_dir = os.path.dirname(os.path.abspath(__file__))

async def main():
    async with httpx.AsyncClient(timeout=15, follow_redirects=True,
                                  headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                                           'Accept-Language': 'tr-TR,tr;q=0.9'}) as cl:
        
        # Check monomanga with follow redirects
        print("=== MONOMANGA CHAPTER PAGE ===")
        r = await cl.get("https://monomanga.com.tr/manga/martial-peak/bolum-1/")
        print(f"Martial Peak Ch.1 (follow): HTTP {r.status_code} ({len(r.text)}B)")
        # List redirect history
        print(f"Redirect history: {[str(h.url) + ' -> ' + str(h.status_code) for h in r.history]}")
        
        # Check for images in final page
        imgs = re.findall(r'<img[^>]+src="([^"]*)"', r.text)
        print(f"Images: {len(imgs)}")
        for i in imgs[:10]:
            print(f"  {i[:120]}")
        
        # Check page title
        titles = re.findall(r'<title[^>]*>([^<]+)</title>', r.text)
        print(f"Title: {titles}")
        
        # Check for chapter content
        has_chapter = 'chapter' in r.text.lower() or 'bolum' in r.text.lower()
        has_pages = 'page' in r.text.lower() or 'img' in r.text.lower()
        has_captcha = 'captcha' in r.text.lower() or 'cf-turnstile' in r.text or 'cloudflare' in r.text.lower()
        print(f"Chapter content: {has_chapter}, Has pages: {has_pages}, Captcha: {has_captcha}")
        
        # Now explore hdfc - get all movie links from multiple pages
        print("\n=== HDFC MOVIE DISCOVERY ===")
        
        all_links = set()
        start_urls = [
            "https://www.hdfilmcehennemi.nl/",  # homepage may have links
        ]
        
        # Check homepage links
        r2 = await cl.get("https://www.hdfilmcehennemi.nl/")
        if r2.status_code == 200:
            links = re.findall(r'href="(https?://www\.hdfilmcehennemi\.nl/[^/"\?]+/)"', r2.text)
            all_links.update(links)
            print(f"Links from homepage: {len(links)}")
        
        # Check film robotu
        r3 = await cl.get("https://www.hdfilmcehennemi.nl/film-robotu-1/")
        if r3.status_code == 200:
            links = re.findall(r'href="(https?://www\.hdfilmcehennemi\.nl/[^/"\?]+/)"', r3.text)
            all_links.update(links)
            print(f"Links from film robotu: {len(links)}")
        
        # Check movie pages for related movies
        movie_pages = [
            "https://www.hdfilmcehennemi.nl/american-psycho/",
            "https://www.hdfilmcehennemi.nl/popeye-the-slayer-man/",
            "https://www.hdfilmcehennemi.nl/your-host/",
        ]
        for murl in movie_pages:
            try:
                r4 = await cl.get(murl)
                if r4.status_code == 200:
                    links = re.findall(r'href="(https?://www\.hdfilmcehennemi\.nl/[^/"\?]+/)"', r4.text)
                    all_links.update(links)
                    await asyncio.sleep(0.3)
            except:
                pass
        
        print(f"\nTotal unique movie links: {len(all_links)}")
        
        # Exclude known non-movie pages
        exclude = {'/', '/film-robotu-1/', '/category/', '/iletisim-1/', '/apk/', '/windows-uygulamasi/'}
        movie_links = [l for l in sorted(all_links) if not any(e in l for e in ['/category/', '/iletisim', '/apk/', '/windows'])]
        print(f"Likely movie links: {len(movie_links)}")
        for l in movie_links:
            print(f"  {l}")
            
        # Test each for iframe presence
        print("\n=== HDFC MOVIE IFRAME CHECK ===")
        working = []
        for url in movie_links[:30]:  # test first 30
            try:
                r5 = await cl.get(url, timeout=8)
                if r5.status_code == 200:
                    has_iframe = '<iframe' in r5.text
                    size = len(r5.text)
                    if has_iframe and size > 10000:
                        working.append(url)
                        print(f"  ✅ {url.split('/')[-2]:40s} ({size}B) iframe")
                    elif size > 10000:
                        print(f"  ❌ {url.split('/')[-2]:40s} ({size}B) no iframe")
                    else:
                        print(f"  ❌ {url.split('/')[-2]:40s} ({size}B) too small")
                else:
                    print(f"  ❌ {url.split('/')[-2]:40s} HTTP {r5.status_code}")
            except Exception as e:
                print(f"  ❌ {url.split('/')[-2]:40s} ERROR {str(e)[:30]}")
            await asyncio.sleep(0.3)

if __name__ == "__main__":
    asyncio.run(main())
