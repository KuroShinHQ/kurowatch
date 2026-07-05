"""www.tranimaci.com → tranimaci.com URL migration (8654 ep)"""
import asyncio, sys
sys.path.insert(0, '.')
from backend.database import AsyncSessionLocal
from sqlalchemy import text

async def fix():
    async with AsyncSessionLocal() as db:
        # Once say
        r = await db.execute(text("""
            SELECT COUNT(*) FROM episode WHERE url LIKE 'https://www.tranimaci.com/%'
        """))
        cnt = r.scalar()
        print(f"www. olan ep sayisi: {cnt}")

        if cnt == 0:
            print("Duzeltilecek ep yok.")
            return

        # Ornek
        r2 = await db.execute(text("""
            SELECT url FROM episode WHERE url LIKE 'https://www.tranimaci.com/%' LIMIT 3
        """))
        print("Ornekler:")
        for row in r2.fetchall():
            print(f"  {row[0]}")
            old = row[0]
            new = old.replace('https://www.tranimaci.com/', 'https://tranimaci.com/')
            print(f"  -> {new}")

        # Guncelle
        await db.execute(text("""
            UPDATE episode
            SET url = REPLACE(url, 'https://www.tranimaci.com/', 'https://tranimaci.com/')
            WHERE url LIKE 'https://www.tranimaci.com/%'
        """))
        await db.commit()
        print(f"\n{cnt} URL guncellendi: www.tranimaci.com -> tranimaci.com")

        # Dogrula
        r3 = await db.execute(text("""
            SELECT COUNT(*) FROM episode WHERE url LIKE 'https://www.tranimaci.com/%'
        """))
        remaining = r3.scalar()
        print(f"Kalan www. URL: {remaining}")

asyncio.run(fix())
