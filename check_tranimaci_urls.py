import asyncio, sys
sys.path.insert(0, '.')
from backend.database import AsyncSessionLocal
from sqlalchemy import text

async def check():
    async with AsyncSessionLocal() as db:
        r = await db.execute(text("""
            SELECT c.title, e.number, e.url
            FROM episode e JOIN content c ON c.id = e.content_id
            WHERE e.url LIKE '%tranimaci%'
            ORDER BY c.title, e.number
            LIMIT 20
        """))
        rows = r.fetchall()
        for row in rows:
            print(f"{row[0][:40]} Ep{row[1]}: {row[2][:80]}")

asyncio.run(check())
