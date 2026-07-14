"""Find monomanga API endpoint for chapter data"""
import asyncio, httpx, re, os, json

async def main():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
               'Referer': 'https://monomanga.com.tr/',
               'Accept-Language': 'tr-TR,tr;q=0.9'}
    
    async with httpx.AsyncClient(timeout=15, follow_redirects=True, headers=headers) as cl:
        
        # Check for Next.js data endpoint
        print("=== API DISCOVERY ===")
        endpoints = [
            "/_next/data/",
            "/_next/data/build-id.json",
            "/api/",
            "/api/manga/",
            "/api/chapter/",
            "/wp-json/",
            "/graphql",
        ]
        
        for ep in endpoints:
            r = await cl.get(f"https://monomanga.com.tr{ep}")
            print(f"  {ep:30s} HTTP {r.status_code} ({len(r.text)}B)")
            if r.status_code == 200:
                print(f"    Body: {r.text[:200]}")
            await asyncio.sleep(0.2)
        
        # Check the listing page for API calls  
        r = await cl.get("https://monomanga.com.tr/manga/solo-leveling/")
        text = r.text
        
        # Find __NEXT_DATA__ or similar
        next_data = re.search(r'__NEXT_DATA__\s*=\s*({[^<]+})', text)
        if next_data:
            data = json.loads(next_data.group(1))
            print(f"\n__NEXT_DATA__ found:")
            print(f"  Build ID: {data.get('buildId', 'N/A')}")
            print(f"  Keys: {list(data.keys())}")
            # Check page props
            props = data.get('props', {})
            page_props = props.get('pageProps', {})
            print(f"  pageProps keys: {list(page_props.keys())}")
            if page_props:
                print(f"  pageProps: {json.dumps(page_props, ensure_ascii=False, indent=2)[:500]}")
        else:
            # Check for rsc (React Server Components)
            rsc = re.search(r'__NEXT_DATA__', text)
            if rsc:
                print("__NEXT_DATA__ referenced but not found in script tag")
            
            # Check for self.__next_f.push (turbopack streaming)
            next_f = re.findall(r'self\.__next_f\.push\(([^)]+)\)', text)
            print(f"\n__next_f.push calls: {len(next_f)}")
            
            # Look for the chapter data in the turbopack chunks
            chunks = re.findall(r'/_next/static/chunks/([^"]+)', text)
            print(f"Turbopack chunks in HTML: {len(chunks)}")
            for c in chunks[:10]:
                print(f"  _next/static/chunks/{c[:60]}")
            
            # Maybe the data is embedded differently in Next.js 15+
            # Check for data-post-id or chapter data
            data_attrs = re.findall(r'data-([^=]*)="([^"]*)"', text)
            print(f"\nData attributes: {len(data_attrs)}")
            for k, v in data_attrs[:20]:
                print(f"  data-{k}=\"{v}\"")
            
            # Check for JSON in script tags
            scripts = re.findall(r'<script[^>]*type="application/json"[^>]*>([^<]+)</script>', text)
            print(f"\nJSON script tags: {len(scripts)}")
            for s in scripts[:5]:
                print(f"  {s[:200]}")

        # Save page for analysis
        save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tmp_monomanga_listing.html")
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"\nSaved listing page to {save_path}")

if __name__ == "__main__":
    asyncio.run(main())
