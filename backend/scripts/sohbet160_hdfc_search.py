"""Test hdfc.sh search functionality for movie discovery + check iframe embed URLs"""
import asyncio, httpx, re

async def main():
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as cl:
        headers = {'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'tr-TR,tr;q=0.9'}
        
        # Check the search/robot page
        print("=== HDFC SEARCH ===")
        r = await cl.get("https://www.hdfilmcehennemi.sh/film-robotu-1/", headers=headers)
        print(f"Film Robotu: HTTP {r.status_code} ({len(r.text)}B)")
        
        # Try search with query param
        r2 = await cl.get("https://www.hdfilmcehennemi.sh/?s=inception", headers=headers)
        print(f"Search inception: HTTP {r2.status_code} ({len(r2.text)}B)")
        
        r3 = await cl.get("https://www.hdfilmcehennemi.sh/?s=avatar", headers=headers)
        print(f"Search avatar: HTTP {r3.status_code} ({len(r3.text)}B)")
        
        # Check the existing working movie page for iframe/embed URLs
        print("\n=== HDFC IFRAME ANALYSIS ===")
        r4 = await cl.get("https://www.hdfilmcehennemi.sh/american-psycho/", headers=headers)
        iframes = re.findall(r'<iframe[^>]+src="([^"]*)"', r4.text)
        print(f"American Psycho - iframes: {iframes}")
        embeds = re.findall(r'(?:src|data-src)="([^"]*(?:embed|player)[^"]*)"', r4.text)
        print(f"American Psycho - embeds: {embeds}")
        
        # Check if the embed URL works
        if iframes:
            for url in iframes:
                r5 = await cl.get(url, headers=headers, timeout=10)
                print(f"Embed {url}: HTTP {r5.status_code} ({len(r5.text)}B)")
        
        # Try to access hdfc embed domain directly
        print("\n=== HDFC MOBI EMBED ===")
        r6 = await cl.get("https://hdfilmcehennemi.mobi/", headers=headers)
        print(f"mobi homepage: HTTP {r6.status_code} ({len(r6.text)}B)")
        
        # Try WP JSON API
        print("\n=== HDFC API ===")
        r7 = await cl.get("https://www.hdfilmcehennemi.sh/wp-json/wp/v2/posts?per_page=20", headers=headers)
        print(f"WP JSON posts: HTTP {r7.status_code} ({len(r7.text)}B)")
        if r7.status_code == 200:
            posts = r7.json()
            print(f"Posts found: {len(posts)}")
            for p in posts[:10]:
                print(f"  - {p.get('title',{}).get('rendered','N/A')}: {p.get('link','')}")

if __name__ == "__main__":
    asyncio.run(main())
