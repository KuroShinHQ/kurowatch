"""Deep test filmmodu.org"""
import asyncio, httpx, re

async def check(client, url, label):
    try:
        r = await client.get(url, timeout=15, follow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                     'Accept-Language': 'tr-TR,tr;q=0.9'})
        iframes = len(re.findall(r'<iframe', r.text))
        embeds = re.findall(r'(?:src|href)="([^"]*embed[^"]*)"', r.text)
        players = re.findall(r'(?:src|href)="([^"]*player[^"]*)"', r.text)
        videos = re.findall(r'(?:src|href)="([^"]*\.m3u8[^"]*)"', r.text)
        sources = re.findall(r'(?:src|href)="([^"]*)"', r.text)[:10]
        return {"label": label, "status": r.status_code, "size": len(r.text), "ok": r.status_code == 200, 
                "iframes": iframes, "embeds": embeds, "players": players, "videos": videos,
                "body": r.text[:500]}
    except Exception as e:
        return {"label": label, "status": None, "error": str(e)[:60]}

async def main():
    async with httpx.AsyncClient(timeout=15, limits=httpx.Limits(max_keepalive_connections=5, max_connections=5)) as cl:
        print("=== FILMMODU DEEP TEST ===")
        tests = [
            ("https://filmmodu.org/", "homepage"),
            ("https://filmmodu.org/film/esaretin-bedeli-izle/", "Esaretin Bedeli"),
            ("https://filmmodu.org/film/fight-club-izle/", "Fight Club"),
            ("https://filmmodu.org/film/inception-izle/", "Inception"),
            ("https://filmmodu.org/film/the-dark-knight-izle/", "The Dark Knight"),
            ("https://filmmodu.org/film/interstellar-izle/", "Interstellar"),
            ("https://filmmodu.org/film/pulp-fiction-izle/", "Pulp Fiction"),
            ("https://filmmodu.org/film/forrest-gump-izle/", "Forrest Gump"),
            ("https://filmmodu.org/film/the-matrix-izle/", "The Matrix"),
            ("https://filmmodu.org/film/the-shawshank-redemption-izle/", "Shawshank"),
            ("https://filmmodu.org/film/fast-and-furious-izle/", "Fast & Furious"),
            ("https://filmmodu.org/film/fetih-1453-izle/", "Fetih 1453"),
            ("https://filmmodu.org/film/harry-potter-izle/", "Harry Potter"),
            ("https://filmmodu.org/film/iron-man-izle/", "Iron Man"),
            ("https://filmmodu.org/film/spider-man-izle/", "Spider-Man"),
            ("https://filmmodu.org/film/avatar-izle/", "Avatar"),
            ("https://filmmodu.org/film/titanic-izle/", "Titanic"),
            ("https://filmmodu.org/film/the-wolf-of-wall-street-izle/", "Wolf of WS"),
            ("https://filmmodu.org/film/gladiator-izle/", "Gladiator"),
            ("https://filmmodu.org/film/the-godfather-izle/", "Godfather"),
        ]

        for url, label in tests:
            await asyncio.sleep(0.3)
            r = await check(cl, url, label)
            icon = "✅" if r.get("ok") else "❌"
            extras = []
            if r.get("iframes"): extras.append(f"iframe:{r['iframes']}")
            if r.get("embeds"): extras.append(f"embed:{len(r['embeds'])}")
            if r.get("players"): extras.append(f"player:{len(r['players'])}")
            if r.get("videos"): extras.append(f"video:{len(r['videos'])}")
            print(f"  {icon} {label:40s} HTTP {r.get('status')} ({r.get('size')}B) {' '.join(extras)}")

if __name__ == "__main__":
    asyncio.run(main())
