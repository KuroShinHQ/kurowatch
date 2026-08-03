"""Search for working Turkish movie sources"""
import asyncio, httpx, re

async def check(client, url, label):
    try:
        r = await client.get(url, timeout=15, follow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                     'Accept-Language': 'tr-TR,tr;q=0.9'})
        has_iframe = '<iframe' in r.text
        has_embed = 'embed' in r.text.lower()
        has_player = 'video' in r.text.lower() or 'player' in r.text.lower()
        has_movie = 'izle' in r.text.lower() or 'film' in r.text.lower()
        return {"label": label, "status": r.status_code, "size": len(r.text), "ok": r.status_code == 200 and len(r.text) > 10000, "iframe": has_iframe, "embed": has_embed, "player": has_player, "movie": has_movie}
    except Exception as e:
        return {"label": label, "status": None, "size": 0, "ok": False, "error": str(e)[:60]}

async def main():
    async with httpx.AsyncClient(timeout=15, limits=httpx.Limits(max_keepalive_connections=5, max_connections=5)) as cl:
        sites = [
            # hdfilmcehennemi variants with different patterns
            ("https://www.hdfilmcehennemi.sh/film/esaretin-bedeli-izle/", "hdfc.sh yeni pattern film/esaretin-bedeli-izle"),
            ("https://www.hdfilmcehennemi.sh/film/esaretin-bedeli/", "hdfc.sh film/esaretin-bedeli"),
            ("https://www.hdfilmcehennemi.sh/esaretin-bedeli-izle/", "hdfc.sh esaretin-bedeli-izle"),
            ("https://www.hdfilmcehennemi.sh/esaretin-bedeli/", "hdfc.sh esaretin-bedeli"),
            ("https://www.hdfilmcehennemi.sh/inception-izle/", "hdfc.sh inception-izle"),
            # .nl with different patterns
            ("https://www.hdfilmcehennemi.nl/esaretin-bedeli/", "hdfc.nl esaretin-bedeli"),
            ("https://www.hdfilmcehennemi.nl/film/esaretin-bedeli-izle/", "hdfc.nl film/esaretin-bedeli-izle"),
            # filmmodu
            ("https://filmmodu.org/", "filmmodu.org homepage"),
            ("https://filmmodu.org/film/esaretin-bedeli-izle/", "filmmodu film"),
            ("https://filmmodu.org/film/esaretin-bedeli/", "filmmodu slug"),
            ("https://filmmodu.org/esaretin-bedeli-izle/", "filmmodu no-prefix"),
            # dizimag film
            ("https://dizimag.com.tr/film/esaretin-bedeli/", "dizimag film"),
            ("https://dizimag.com.tr/film/esaretin-bedeli-izle/", "dizimag film-izle"),
            # yabancidizi
            ("https://www.yabancidizi.tv/film/esaretin-bedeli/", "yabancidizi film"),
            # diziyou
            ("https://www.diziyou.com/film/", "diziyou film"),
            # filmizlesene
            ("https://www.filmizlesene.pro/", "filmizlesene.pro"),
            ("https://www.filmizlesene.pro/film/esaretin-bedeli-izle/", "filmizlesene film"),
            # filmcehenne
            ("https://www.filmcehennemim.net/", "filmcehennemim.net"),
            ("https://www.filmcehennemim.net/film/esaretin-bedeli/", "filmcehennemim film"),
            # diziroll
            ("https://diziroll.com/film/", "diziroll film"),
            # jetfilmizle
            ("https://jetfilmizle.lol/", "jetfilmizle"),
            ("https://jetfilmizle.lol/film/esaretin-bedeli-izle/", "jetfilmizle film"),
            # 1080pizle
            ("https://1080pizle.com/", "1080pizle"),
            ("https://1080pizle.com/film/esaretin-bedeli-izle/", "1080pizle film"),
            # turkcealtyazi
            ("https://www.turkcealtyazi.org/film/esaretin-bedeli/", "turkcealtyazi"),
            # fullfilmizle
            ("https://www.fullfilmizle.video/", "fullfilmizle.video"),
            # fullhdfilmizlesene alternate patterns
            ("https://www.fullhdfilmizlesene.pw/esaretin-bedeli-izle/", "fullhd alt pattern"),
            # fullhd movies
            ("https://www.fullhdfilmizlesene.pw/esaretin-bedeli/", "fullhd esaretin"),
        ]

        print("=== NEW MOVIE SOURCE SEARCH ===")
        for url, label in sites:
            await asyncio.sleep(0.5)
            r = await check(cl, url, label)
            icon = "✅" if r.get("ok") and (r.get("iframe") or r.get("player")) else "❌"
            extras = []
            if r.get("iframe"): extras.append("iframe")
            if r.get("embed"): extras.append("embed")
            if r.get("player"): extras.append("player")
            print(f"  {icon} {label:55s} HTTP {r.get('status')} ({r.get('size')}B) {' '.join(extras)}")

if __name__ == "__main__":
    asyncio.run(main())
