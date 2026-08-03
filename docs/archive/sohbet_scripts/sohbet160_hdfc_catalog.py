"""Complete hdfc.nl catalog scan + match with our 113 films"""
import asyncio, httpx, re, os, json, sqlite3

script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, "..", "..", "memory", "kurowatch.db")
db_path = os.path.normpath(db_path)

async def main():
    async with httpx.AsyncClient(timeout=12, follow_redirects=True,
                                  headers={'User-Agent': 'Mozilla/5.0',
                                           'Accept-Language': 'tr-TR,tr;q=0.9'}) as cl:
        # Get all unique movie links from all discovery pages
        all_links = set()
        sources = [
            "https://www.hdfilmcehennemi.nl/",
            "https://www.hdfilmcehennemi.nl/film-robotu-1/",
            "https://www.hdfilmcehennemi.nl/yabancidiziizle-5/",
        ]
        
        # Also check category pages with different patterns
        for base in sources:
            r = await cl.get(base)
            if r.status_code == 200:
                links = re.findall(r'href="(https?://www\.hdfilmcehennemi\.nl/[^/"\?]+/)"', r.text)
                all_links.update(links)
            await asyncio.sleep(0.3)
        
        # Now check related movies from known working pages
        known_working = [
            "https://www.hdfilmcehennemi.nl/popeye-the-slayer-man/",
            "https://www.hdfilmcehennemi.nl/your-host/",
            "https://www.hdfilmcehennemi.nl/american-psycho-6/",
            "https://www.hdfilmcehennemi.nl/in-a-violent-nature-24/",
        ]
        for url in known_working:
            r = await cl.get(url)
            if r.status_code == 200:
                links = re.findall(r'href="(https?://www\.hdfilmcehennemi\.nl/[^/"\?]+/)"', r.text)
                all_links.update(links)
            await asyncio.sleep(0.3)
        
        # Filter out non-movie pages
        exclude_patterns = ['/category/', '/iletisim', '/apk/', '/windows', '/yabancidiziizle',
                           '/film-robotu', '/film-istekleri', '/serifilmlerim',
                           '/en-cok-begenilen', '/en-cok-yorumlanan', '/imdb-7-puan']
        movie_links = sorted([l for l in all_links 
                            if not any(e in l for e in exclude_patterns)])
        
        print(f"Total unique movie links to check: {len(movie_links)}")
        
        # Check each link for iframe
        working_urls = []
        non_working = []
        
        for i, url in enumerate(movie_links):
            try:
                r = await cl.get(url, timeout=8)
                if r.status_code == 200:
                    has_iframe = '<iframe' in r.text
                    size = len(r.text)
                    slug = url.rstrip('/').split('/')[-1]
                    if has_iframe and size > 20000:
                        print(f"  ✅ [{i+1}/{len(movie_links)}] {slug[:50]:50s} ({size}B)")
                        working_urls.append(url)
                    elif size > 20000:
                        non_working.append((url, "no_iframe", size))
                    else:
                        non_working.append((url, "small", size))
                else:
                    non_working.append((url, f"HTTP_{r.status_code}", 0))
            except Exception as e:
                non_working.append((url, str(e)[:20], 0))
            
            if (i+1) % 10 == 0:
                print(f"  --- progress: {i+1}/{len(movie_links)} ---")
                await asyncio.sleep(0.5)  # rate limit break
            else:
                await asyncio.sleep(0.1)
        
        print(f"\nWorking movies with iframe: {len(working_urls)}")
        print(f"Non-working: {len(non_working)}")
        
        # Save working movies
        working_slugs = {}
        for url in working_urls:
            slug = url.rstrip('/').split('/')[-1]
            working_slugs[url] = slug
        
        # Now load our 113 films and try to match
        print("\n=== MATCHING WITH OUR 113 FILMS ===")
        db = sqlite3.connect(db_path)
        db.row_factory = sqlite3.Row
        cur = db.execute("SELECT id, title FROM content WHERE type='movie' ORDER BY id")
        films = [dict(r) for r in cur.fetchall()]
        
        # For each film, try to find a matching slug in working_urls
        import urllib.parse
        matched = []
        unmatched = []
        
        for film in films:
            title = film['title']
            title_lower = title.lower()
            
            # Normalize title for matching
            title_norm = re.sub(r'[^a-z0-9çğıöşü\s]', '', title_lower)
            title_norm = title_norm.replace(' ', '-')
            
            # Try to find slug containing the title or vice versa
            found = False
            for url in working_urls:
                slug = url.rstrip('/').split('/')[-1]
                slug_lower = slug.lower()
                
                # Check if normalised title appears in slug
                title_parts = title_norm.split('-')
                slug_parts = slug_lower.split('-')
                
                # Check for title words in slug (at least 2 significant words match)
                significant = [p for p in title_parts if len(p) > 2]
                matches = sum(1 for p in significant if p in slug_parts)
                
                if matches >= 2 and matches >= len(significant) * 0.5:
                    matched.append((film['id'], title, url))
                    found = True
                    break
                    
                # Also check if any slug-part matches title (for English titles)
                if title_lower in slug_lower or slug_lower in title_lower:
                    matched.append((film['id'], title, url))
                    found = True
                    break
            
            if not found:
                unmatched.append((film['id'], title))
        
        print(f"\nMatched films: {len(matched)}")
        for m in matched:
            slug = m[2].rstrip('/').split('/')[-1]
            print(f"  ✅ {m[1][:40]:40s} -> {slug[:50]}")
        
        print(f"\nUnmatched films: {len(unmatched)}")
        for u in unmatched:
            print(f"  ❌ {u[1]}")
        
        # Save results
        with open(os.path.join(script_dir, "sohbet160_hdfc_matched.json"), "w", encoding="utf-8") as f:
            json.dump([{"id": m[0], "title": m[1], "url": m[2]} for m in matched], f, ensure_ascii=False, indent=2)
        with open(os.path.join(script_dir, "sohbet160_hdfc_unmatched.json"), "w", encoding="utf-8") as f:
            json.dump([{"id": u[0], "title": u[1]} for u in unmatched], f, ensure_ascii=False, indent=2)
        
        print(f"\nResults saved to JSON files")

if __name__ == "__main__":
    asyncio.run(main())
