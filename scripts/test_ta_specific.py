"""Bilinen Japon animelerini turkanime'de direkt slug ile test et."""
import asyncio, aiohttp, re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
}

# (title, [slug candidates to try])
TESTS = [
    ("Assassination Classroom", ["ansatsu-kyoushitsu", "assassination-classroom", "ansatsu"]),
    ("Bofuri",                  ["bofuri", "bofuri-itai"]),
    ("Code Geass",              ["code-geass", "code-geass-hangyaku"]),
    ("DanMachi",                ["danmachi", "dungeon-ni-deai", "is-it-wrong-to-try"]),
    ("Classroom of the Elite",  ["youkoso-jitsuryoku", "classroom-of-the-elite", "youkoso"]),
    ("100-man no Inochi",       ["100-man-no-inochi", "100-man", "hyakuman-no-inochi"]),
    ("Arifureta",               ["arifureta", "arifureta-shokugyou"]),
    ("Assassination Classroom", ["ansatsu-kyoushitsu", "ansatsu-kyoshitsu"]),
    ("Combatants Will Be Dispatched", ["combatants-will-be-dispatched", "sentai-daibakuhatsu", "sentai"]),
    ("DanMachi Season 4",       ["danmachi-4", "dungeon-ni-deai-wo-motomeru-no-wa-machigatteiru"]),
    ("Baki",                    ["baki", "baki-hanma"]),
    ("Attack on Titan",         ["shingeki-no-kyojin", "attack-on-titan"]),
]

async def main():
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        for title, slugs in TESTS:
            found = None
            for slug in slugs:
                url = f"https://www.turkanime.tv/video/{slug}-1-bolum"
                try:
                    async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=8)) as r:
                        if r.status == 200:
                            txt = await r.text(errors="ignore")
                            if any(k in txt for k in ("video-js", "jwplayer", "player", "turkanime")):
                                found = slug
                                break
                except Exception:
                    pass
                await asyncio.sleep(0.2)

            status = "✅ " + found if found else "❌"
            print(f"  {title[:40]:40} → {status}")

asyncio.run(main())
