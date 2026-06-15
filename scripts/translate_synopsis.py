"""
synopsis_tr: AniList synopsis'leri Türkçe'ye çevirir (MyMemory free API).
Kullanım:
  cd /mnt/c/Kuroshin/kurowatch
  python3 scripts/translate_synopsis.py
"""
import asyncio, json, re, time, urllib.request, urllib.parse
import sys
sys.path.insert(0, '/mnt/c/Kuroshin/kurowatch')

from sqlalchemy import select, update
from backend.database import AsyncSessionLocal
from backend.models import Content

MYMEMORY_URL = "https://api.mymemory.translated.net/get"
DELAY = 1.5  # saniye — rate limit
MAX_CHARS = 500  # MyMemory tek istek limiti


def _clean_html(text: str) -> str:
    return re.sub(r'<[^>]+>', '', text).strip()


def _translate(text: str) -> str:
    """Metni EN→TR çevirir, başarısız olursa orijinali döner."""
    text = text[:MAX_CHARS]
    params = urllib.parse.urlencode({"q": text, "langpair": "en|tr"})
    url = f"{MYMEMORY_URL}?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "KuroWatch/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        tr = data.get("responseData", {}).get("translatedText", "")
        if tr and data.get("responseStatus") == 200:
            return tr
    except Exception as e:
        print(f"  [HATA] {e}")
    return text


async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Content).where(
                Content.synopsis.isnot(None),
                Content.synopsis != "",
                Content.synopsis_tr.is_(None),
            )
        )
        items = result.scalars().all()
        print(f"{len(items)} içerik çevrilecek (synopsis_tr boş).")

        for i, item in enumerate(items, 1):
            clean = _clean_html(item.synopsis)
            if not clean:
                continue
            print(f"[{i}/{len(items)}] {item.title[:50]}... ", end="", flush=True)
            tr = _translate(clean)
            item.synopsis_tr = tr
            print("✓" if tr != clean else "HATA(aynı)")
            time.sleep(DELAY)

        await db.commit()
        print(f"\nTamamlandı. {len(items)} özet çevrildi.")


if __name__ == "__main__":
    asyncio.run(main())
