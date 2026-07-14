"""Search for m3u8 video URL in hdfc page"""
import asyncio, httpx, re, os

async def main():
    async with httpx.AsyncClient(timeout=15, follow_redirects=True,
        headers={'User-Agent': 'Mozilla/5.0'}) as cl:
        
        r = await cl.get("https://www.hdfilmcehennemi.nl/american-psycho-6/")
        
        # Find iframe src
        iframes = re.findall(r'<iframe[^>]+src="([^"]*)"', r.text)
        print(f"iframes: {iframes}")
        
        # Find all embeddable URLs
        for pat in [r'data-player[^=]*=\s*"([^"]*)"', 
                    r'data-video[^=]*=\s*"([^"]*)"',
                    r'data-src\s*=\s*"([^"]*)"']:
            matches = re.findall(pat, r.text)
            if matches:
                print(f"Pattern '{pat[:20]}': {matches[:5]}")
        
        # If there's an iframe, try to get the content from it
        for url in iframes:
            try:
                r2 = await cl.get(url, timeout=10)
                print(f"\nIframe {url}: HTTP {r2.status_code} ({len(r2.text)}B)")
                # Search for m3u8 in iframe
                m3u8s = re.findall(r'(https?://[^"\']*\.m3u8[^"\']*)', r2.text)
                print(f"  m3u8: {m3u8s}")
                mp4s = re.findall(r'(https?://[^"\']*\.mp4[^"\']*)', r2.text)
                print(f"  mp4: {mp4s}")
                # Save iframe content
                save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tmp_hdfc_iframe.html")
                with open(save_path, "w") as f:
                    f.write(r2.text)
                print(f"  Saved to {save_path}")
            except Exception as e:
                print(f"Iframe error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
