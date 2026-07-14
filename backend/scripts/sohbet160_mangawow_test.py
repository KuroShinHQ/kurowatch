"""Test mangawow chapter download - extract image URLs"""
import asyncio, httpx, re

async def main():
    async with httpx.AsyncClient(timeout=15, follow_redirects=True,
                                  headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'tr-TR,tr;q=0.9'}) as cl:
        
        # Test solo-leveling chapter 1
        print("=== MANGAWOW CHAPTER TEST ===")
        r = await cl.get("https://www.mangawow.org/manga/solo-leveling/chapter-1/")
        print(f"Status: {r.status_code}, Size: {len(r.text)}B")
        
        # Extract all image URLs
        imgs = re.findall(r'<img[^>]+src="([^"]*)"', r.text)
        print(f"\nTotal images: {len(imgs)}")
        for i in imgs[:20]:
            print(f"  {i}")
        
        # Check for chapter navigation
        titles = re.findall(r'<title[^>]*>([^<]+)</title>', r.text)
        print(f"\nTitle: {titles}")
        
        # Check what the page is about
        for keyword in ["solo leveling", "bolum", "chapter", "oku", "manga", "sayfa"]:
            count = r.text.lower().count(keyword)
            if count > 0:
                print(f"Keyword '{keyword}': {count}")
        
        # Try to find image in a page-specific format
        # Usually manga sites store images in p, div, or span with specific classes
        page_divs = re.findall(r'<div[^>]*class="[^"]*page[^"]*"[^>]*>', r.text)
        print(f"\nDivs with 'page' class: {len(page_divs)}")
        
        # Check for manga reader specific classes
        for cls in ["reading", "chapter", "manga", "comic", "image", "reader"]:
            if cls in r.text.lower():
                matches = re.findall(rf'class="[^"]*{cls}[^"]*"', r.text.lower())
                print(f"Class '{cls}': {len(matches)} matches")
        
        # Save full page
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        save_path = os.path.join(script_dir, "..", "..", "tmp_mangawow_ch1.html")
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(r.text)
        print(f"\nSaved to {save_path}")

if __name__ == "__main__":
    asyncio.run(main())
