"""
Oyunlara Steam arama API'si ile cover_url ekler (ücretsiz, kayıt gerekmez).
Kullanım:
  cd /mnt/c/Kuroshin/kurowatch
  python3 scripts/enrich_games.py
"""
import asyncio, json, re, time, urllib.request, urllib.parse
import sys
sys.path.insert(0, '/mnt/c/Kuroshin/kurowatch')

from sqlalchemy import select
from backend.database import AsyncSessionLocal
from backend.models import Content

STEAM_SEARCH = "https://store.steampowered.com/api/storesearch/"
STEAM_COVER  = "https://cdn.akamai.steamstatic.com/steam/apps/{appid}/library_600x900.jpg"
DELAY = 1.2


def _steam_search(name: str) -> tuple[int | None, str | None]:
    """Steam'de oyun arar, (appid, cover_url) döner."""
    params = urllib.parse.urlencode({"term": name, "cc": "us", "l": "english"})
    url = f"{STEAM_SEARCH}?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "KuroWatch/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        items = data.get("items", [])
        if not items:
            return None, None
        # İlk sonuç — isim benzerliği basit kontrol
        best = None
        name_l = name.lower()
        for it in items[:5]:
            it_name = it.get("name", "").lower()
            if name_l in it_name or it_name in name_l:
                best = it
                break
        if not best:
            best = items[0]
        appid = best["id"]
        cover = STEAM_COVER.format(appid=appid)
        return appid, cover
    except Exception as e:
        print(f"  [HATA] {e}")
        return None, None


async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Content).where(
                Content.type == "game",
                Content.cover_url.is_(None),
            )
        )
        games = result.scalars().all()
        print(f"{len(games)} oyun için cover aranacak.")

        found = 0
        for i, g in enumerate(games, 1):
            print(f"[{i}/{len(games)}] {g.title[:40]}... ", end="", flush=True)
            appid, cover = _steam_search(g.title)
            if cover:
                g.cover_url = cover
                if not g.external_id:
                    g.external_id = f"steam:{appid}"
                found += 1
                print(f"✓ appid={appid}")
            else:
                print("bulunamadı")
            time.sleep(DELAY)

        await db.commit()
        print(f"\nTamamlandı. {found}/{len(games)} oyun kapağı bulundu.")


if __name__ == "__main__":
    asyncio.run(main())
