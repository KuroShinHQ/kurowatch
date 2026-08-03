"""Broader Turkish movie site search"""
import asyncio, httpx, re

async def check(client, url, label):
    try:
        r = await client.get(url, timeout=15, follow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'tr-TR,tr;q=0.9'})
        has_iframe = '<iframe' in r.text
        has_embed = 'embed' in r.text.lower()
        has_player = 'player' in r.text.lower() or 'video' in r.text.lower()
        has_movie = 'izle' in r.text.lower() or 'film' in r.text.lower()
        is_parked = 'hugedomains' in r.text.lower() or 'for sale' in r.text.lower() or 'buy this domain' in r.text.lower()
        size = len(r.text)
        return {"label": label, "status": r.status_code, "size": size, 
                "ok": r.status_code == 200 and size > 10000 and not is_parked,
                "iframe": has_iframe, "embed": has_embed, "player": has_player,
                "parked": is_parked, "movie": has_movie}
    except Exception as e:
        return {"label": label, "ok": False, "error": str(e)[:60]}

async def main():
    async with httpx.AsyncClient(timeout=15, limits=httpx.Limits(max_keepalive_connections=5, max_connections=5)) as cl:
        tests = [
            # Turkish movie sites
            ("https://www.hdfilmcehennemi.sh/", "hdfc.sh homepage"),
            ("https://www.hdfilmcehennemi.sh/american-psycho/", "hdfc.sh known good"),
            ("https://www.hdfilmcehennemi.sh/inception/", "hdfc.sh inception"),
            ("https://www.hdfilmcehennemi.sh/fight-club/", "hdfc.sh fight club"),
            ("https://www.hdfilmcehennemi.sh/esaretin-bedeli/", "hdfc.sh esaretin"),
            ("https://www.hdfilmcehennemi.net/american-psycho/", "hdfc.net known good"),
            ("https://www.hdfilmcehennemi.io/", "hdfc.io homepage"),
            ("https://www.hdfilmcehennemi.io/american-psycho/", "hdfc.io known good"),
            # Try iframe URL directly
            ("https://hdfilmcehennemi.mobi/", "hdfc.mobi embed domain"),
            # New sites to try
            ("https://www.dizibox.plus/", "dizibox.plus"),
            ("https://www.dizibox.plus/film/", "dizibox film"),
            ("https://www.tranimeizle.org.tr/film/", "tranimeizle film"),
            ("https://dizimag.com.tr/", "dizimag homepage"),
            ("https://www.turkish123.com/", "turkish123"),
            ("https://www.diziyou.film/", "diziyou film"),
            ("https://www.diziyou.com/", "diziyou"),
            # Check what api/endpoint hdfc sites use
            ("https://www.hdfilmcehennemi.sh/wp-json/", "hdfc.sh api"),
            ("https://www.hdfilmcehennemi.sh/api/", "hdfc.sh api2"),
            # Try the embed URL directly
            ("https://hdfilmcehennemi.mobi/embed/", "hdfc.mobi embed"),
            # yabancidizi
            ("https://www.yabancidizi.pw/", "yabancidizi.pw"),
            # Full film izle
            ("https://www.fullhdfilmizlesene.de/", "fullhd.de"),
            # Try without www
            ("https://hdfilmcehennemi.sh/", "hdfc.sh no-www"),
            ("https://hdfilmcehennemi.sh/american-psycho/", "hdfc.sh no-www movie"),
        ]
        print("=== MOVIE SOURCE SEARCH ===")
        for url, label in tests:
            await asyncio.sleep(0.5)
            r = await check(cl, url, label)
            if not r.get("ok"):
                icon = "❌"
            else:
                icon = "✅"
                if r.get("parked"): icon = "⚠️ parked"
                if r.get("iframe"): icon = "🎬 iframe"
                if r.get("embed"): icon = "🎬 embed"
                if r.get("player"): icon = "🎬 player"
            extras = []
            if r.get("iframe"): extras.append("iframe")
            if r.get("embed"): extras.append("embed")
            if r.get("player"): extras.append("player")
            if r.get("parked"): extras.append("PARKED")
            if r.get("error"): extras.append(r["error"])
            print(f"  {icon} {label:50s} HTTP {r.get('status')} ({r.get('size')}B) {' '.join(extras)}")

if __name__ == "__main__":
    asyncio.run(main())
