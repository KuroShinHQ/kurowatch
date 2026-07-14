"""Test monomanga chapter download and verify actual content"""
import asyncio, httpx, re, os

script_dir = os.path.dirname(os.path.abspath(__file__))

async def main():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
               'Accept-Language': 'tr-TR,tr;q=0.9'}
    
    async with httpx.AsyncClient(timeout=15, follow_redirects=True, headers=headers) as cl:
        
        # Check listing page for chapters
        print("=== MONOMANGA CHAPTER DISCOVERY ===")
        
        # Test 1: Check Martial Peak listing
        r = await cl.get("https://monomanga.com.tr/manga/martial-peak/")
        if r.status_code == 200:
            ch_links = re.findall(r'href="([^"]*bolum[^"]*)"', r.text)
            ch_urls = re.findall(r'href="(https?://[^"]*)"', r.text)
            print(f"Total links with 'bolum': {len(ch_links)}")
            for l in ch_links[:10]:
                print(f"  {l}")
        
        # Test 2: Check the homepage for any manga links
        r2 = await cl.get("https://monomanga.com.tr/")
        print(f"\nHomepage: HTTP {r2.status_code} ({len(r2.text)}B)")
        
        # Check if there are manga links on homepage
        manga_links = re.findall(r'href="(https?://monomanga\.com\.tr/manga/[^"]*)"', r2.text)
        print(f"Homepage manga links: {len(manga_links)}")
        for l in manga_links[:10]:
            print(f"  {l}")
        
        # Test 3: Try direct manga image CDN
        # Look for image patterns in the listing page
        imgs = re.findall(r'<img[^>]+src="([^"]*)"', r.text)
        print(f"\nListing page images: {len(imgs)}")
        for i in imgs[:5]:
            print(f"  {i[:120]}")
        
        # Test 4: Try a different manga's chapter 
        r3 = await cl.get("https://monomanga.com.tr/manga/solo-leveling/bolum-1/")
        print(f"\nSolo Leveling Ch.1: HTTP {r3.status_code} ({len(r3.text)}B)")
        title = re.findall(r'<title[^>]*>([^<]+)</title>', r3.text)
        print(f"Title: {title}")
        
        # Test 5: Try chapter without trailing slash
        r4 = await cl.get("https://monomanga.com.tr/manga/solo-leveling/bolum-1")
        print(f"\nSolo Leveling Ch.1 (no slash): HTTP {r4.status_code} ({len(r4.text)}B)")
        title4 = re.findall(r'<title[^>]*>([^<]+)</title>', r4.text)
        print(f"Title: {title4}")
        
        # Test 6: Try chapter page listing
        r5 = await cl.get("https://monomanga.com.tr/manga/solo-leveling/")
        if r5.status_code == 200:
            ch5 = re.findall(r'href="([^"]*bolum[^"]*)"', r5.text)
            print(f"\nSolo Leveling chapter links: {ch5[:20]}")
            # Check for sayfa/page links
            sayfa = re.findall(r'href="([^"]*sayfa[^"]*)"', r5.text)
            print(f"Page links: {sayfa}")
            # Check newer chapter
            if ch5:
                test_ch = ch5[0]
                if not test_ch.startswith('http'):
                    test_ch = 'https://monomanga.com.tr' + test_ch
                r6 = await cl.get(test_ch)
                print(f"First chapter page: HTTP {r6.status_code} ({len(r6.text)}B)")
                title6 = re.findall(r'<title[^>]*>([^<]+)</title>', r6.text)
                print(f"Title: {title6}")
                # Check for manga reader images
                imgs6 = re.findall(r'<img[^>]+src="([^"]*)"', r6.text)
                print(f"Images: {len(imgs6)}")
                for i6 in imgs6[:10]:
                    print(f"  {i6[:120]}")

if __name__ == "__main__":
    asyncio.run(main())
