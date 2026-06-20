"""
Tüm içerikler için external_score çeker.
external_id varsa → AniList idMal ile
external_id yoksa → başlık ile Jikan araması
"""
import asyncio
import re
import sqlite3
import aiohttp

DB_PATH = "/mnt/c/Kuroshin/kurowatch/memory/kurowatch.db"
JIKAN_URL = "https://api.jikan.moe/v4"

def title_variants(title):
    variants = [title]
    no_paren = re.sub(r'\s*\([^)]*\)', '', title).strip()
    if no_paren and no_paren != title:
        variants.append(no_paren)
    for p in re.findall(r'\(([^)]+)\)', title):
        if len(p) > 3:
            variants.append(p.strip())
    if ':' in title:
        variants.append(title.split(':')[0].strip())
    variants.append(re.sub(r'\s*(Serisi|Serileri)\b', '', title, flags=re.IGNORECASE).strip())
    return list(dict.fromkeys(v for v in variants if v and len(v) > 2))

def get_items():
    con = sqlite3.connect(DB_PATH)
    rows = con.execute(
        "SELECT id, title, type, external_id FROM content "
        "WHERE external_score IS NULL OR external_score = 0"
    ).fetchall()
    con.close()
    return rows

def set_score(cid, score):
    con = sqlite3.connect(DB_PATH)
    con.execute("UPDATE content SET external_score=? WHERE id=?", (score, cid))
    con.commit()
    con.close()

async def jikan_score_by_title(session, title, ctype):
    ep = "manga" if ctype == "manga" else "anime"
    for variant in title_variants(title):
        try:
            async with session.get(
                f"{JIKAN_URL}/{ep}",
                params={"q": variant, "limit": 1},
                timeout=aiohttp.ClientTimeout(total=7),
            ) as r:
                if r.status == 429:
                    await asyncio.sleep(2)
                    continue
                if r.status != 200:
                    continue
                d = await r.json()
                items = d.get("data", [])
                if items and items[0].get("score"):
                    return round(float(items[0]["score"]), 1)
        except Exception:
            pass
        await asyncio.sleep(0.8)
    return None

async def main():
    rows = get_items()
    total = len(rows)
    print(f"external_score eksik: {total} içerik\n")

    found = 0
    async with aiohttp.ClientSession() as session:
        for i, (cid, title, ctype, ext_id) in enumerate(rows, 1):
            label = title[:50] + "..." if len(title) > 50 else title
            print(f"[{i:03d}/{total}] {label:53s} ", end="", flush=True)

            score = await jikan_score_by_title(session, title, ctype)

            if score:
                set_score(cid, score)
                found += 1
                print(f"✅ {score:4.1f}")
            else:
                print("⚠️  yok")
            await asyncio.sleep(0.3)

    print(f"\n✅ {found}/{total} external_score yazıldı")

if __name__ == "__main__":
    asyncio.run(main())
