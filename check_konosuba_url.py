import asyncio, sys
sys.path.insert(0, '.')
from backend.database import AsyncSessionLocal
from sqlalchemy import text

async def check():
    async with AsyncSessionLocal() as db:
        # KONOSUBA episode URL'leri
        r = await db.execute(text("""
            SELECT c.title, e.number, e.url
            FROM episode e JOIN content c ON c.id = e.content_id
            WHERE (c.title LIKE '%KonoSuba%' OR c.title LIKE '%Konosuba%' OR c.title LIKE '%konosuba%')
            AND e.url LIKE '%tranimaci%'
            ORDER BY e.number
            LIMIT 5
        """))
        rows = r.fetchall()
        print("KONOSUBA tranimaci ep URL'leri:")
        for row in rows:
            print(f"  {row[0][:50]} Ep{row[1]}: {row[2]}")

        # Toplam tranimaci count
        r2 = await db.execute(text("""
            SELECT COUNT(*) FROM episode WHERE url LIKE '%tranimaci%'
        """))
        cnt = r2.scalar()
        print(f"\nToplam tranimaci ep: {cnt}")

        # www.tranimaci vs tranimaci (www olmadan)
        r3 = await db.execute(text("""
            SELECT
                SUM(CASE WHEN url LIKE '%www.tranimaci%' THEN 1 ELSE 0 END) as www_count,
                SUM(CASE WHEN url LIKE '%tranimaci%' AND url NOT LIKE '%www.tranimaci%' THEN 1 ELSE 0 END) as nowww_count
            FROM episode WHERE url LIKE '%tranimaci%'
        """))
        row = r3.fetchone()
        print(f"www. olanlar: {row[0]}, www. olmayanlar: {row[1]}")

asyncio.run(check())
