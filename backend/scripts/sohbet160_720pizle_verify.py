"""Retry 720pizle for failed films with rate-limit-safe approach + content check"""
import sqlite3, os, asyncio, httpx, re, json, time

script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, "..", "..", "memory", "kurowatch.db")
db_path = os.path.normpath(db_path)

# Load fails
fails_path = os.path.join(script_dir, "sohbet160_720pizle_fails.json")
with open(fails_path, "r", encoding="utf-8") as f:
    fails = json.load(f)

# Also load all films for slugs we already know work from deep test
KNOWN_WORKING = {
    "esaretin-bedeli",
    "fight-club",
    "the-shawshank-redemption",
    "inception",
    "interstellar",
    "the-dark-knight",
    "forrest-gump",
    "the-matrix",
    "dovus-kulubu",
    "yesil-yol",
    "pulp-fiction",
}

async def check_url(client, url, timeout=15):
    try:
        r = await client.get(url, timeout=timeout, follow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                     'Accept-Language': 'tr-TR,tr;q=0.9'})
        has_iframe = '<iframe' in r.text or 'embed' in r.text.lower()
        has_player = 'video' in r.text.lower() or 'player' in r.text.lower() or 'm3u8' in r.text
        return r.status_code, len(r.text), has_iframe, has_player, r.text[:2000]
    except Exception as e:
        return None, 0, False, False, str(e)[:200]

async def main():
    async with httpx.AsyncClient(timeout=15, limits=httpx.Limits(max_keepalive_connections=2, max_connections=2)) as cl:
        # First verify known working URLs
        print("=== VERIFY KNOWN WORKING ===")
        verifies = [
            "https://720pizle.com/film/esaretin-bedeli-izle/",
            "https://720pizle.com/film/fight-club-izle/",
            "https://720pizle.com/film/inception-izle/",
            "https://720pizle.com/film/interstellar-izle/",
            "https://720pizle.com/film/the-dark-knight-izle/",
            "https://720pizle.com/film/the-shawshank-redemption-izle/",
            "https://720pizle.com/film/pulp-fiction-izle/",
            "https://720pizle.com/film/the-matrix-izle/",
            "https://720pizle.com/film/forrest-gump-izle/",
            "https://720pizle.com/film/dovus-kulubu-izle/",
            "https://720pizle.com/film/yesil-yol-izle/",
        ]
        for url in verifies:
            status, size, iframe, player, text = await check_url(cl, url)
            await asyncio.sleep(1.5)  # slow
            print(f"  {url} -> HTTP {status} {size}B iframe={iframe} player={player}")

        # Check a few random pages for their actual content
        print("\n=== CHECK CONTENT ===")
        samples = [
            "https://720pizle.com/film/3-idiots-izle/",
            "https://720pizle.com/film/avatar-izle/",
            "https://720pizle.com/film/batman-serisi-kara-valye-ve-tm-filmler-izle/",
        ]
        for url in samples:
            status, size, iframe, player, text = await check_url(cl, url)
            await asyncio.sleep(1.0)
            print(f"  {url}")
            print(f"    Status={status} Size={size}B iframe={iframe} player={player}")
            # Print first 500 chars
            print(f"    Content: {text[:300]}")
            # Check for video sources
            srcs = re.findall(r'src="([^"]+)"', text)
            print(f"    src=: {[s for s in srcs[:5]]}")

if __name__ == "__main__":
    asyncio.run(main())
