"""MangaDex - sayfasi olan chapter bul ve indir"""
import asyncio, httpx, os, sys
sys.path.insert(0, '/mnt/c/Kuroshin/kurowatch')
from backend.downloader.manga import _mangadex_chapter

MANGAS = [
    ("Vinland Saga", "c52b2ce3-7f95-469c-96b0-479524fb7a1a"),
    ("One Punch Man", "d8a959f7-648e-4c8d-8f23-f1f3f8e129f3"),
    ("Blue Lock",    "8b5a00b4-ee5e-4ef7-88cf-6a82b2b7a4c0"),
]

async def main():
    async with httpx.AsyncClient(timeout=15) as c:
        for title, manga_id in MANGAS:
            r = await c.get(f"https://api.mangadex.org/manga/{manga_id}/feed",
                params={"translatedLanguage[]": "en", "order[chapter]": "asc",
                        "limit": 5, "contentRating[]": ["safe","suggestive","erotica"]})
            chs = r.json().get("data", [])
            valid = [ch for ch in chs if ch["attributes"].get("pages", 0) > 0]
            print(f"{title}: {len(chs)} ch, {len(valid)} sayfali")

            if valid:
                ch = valid[0]
                ch_id = ch["id"]
                ch_num = ch["attributes"].get("chapter")
                print(f"  Test: bolum {ch_num} | {ch_id}")

                OUT = "/tmp/kw_manga_final"
                os.makedirs(OUT, exist_ok=True)
                ch_url = f"https://mangadex.org/chapter/{ch_id}"

                def prog(cur, total):
                    if cur % 5 == 0 or cur == total:
                        print(f"    Sayfa {cur}/{total}")

                try:
                    files = await _mangadex_chapter(ch_url, OUT, prog)
                    print(f"  BASARILI: {len(files)} sayfa indirildi")
                    for f in files[:2]:
                        print(f"    {os.path.basename(f)} ({os.path.getsize(f)} B)")
                    return  # ilk basarili siteden cik
                except Exception as e:
                    print(f"  HATA: {e}")

asyncio.run(main())
