import asyncio
from backend.database import AsyncSessionLocal
from backend.models import Content
from sqlalchemy import select

keywords = [
    'dexter', 'hannibal', 'rick and morty', 'black butler', 'marvel',
    'kaguya', 'komi', 'konosuba', 'kakegurui', 'hell', 'high school of the dead',
    'quanzhi', 'jojo', 'kabaneri', 'by the grace', 'vending machine',
    'daily life of the immortal', 'isekai cheat magician', 'blood blockade',
    'no longer allowed', 'shangri-la', 'what if', 'sokakta hayatta kalma',
    'king\'s avatar',
]

async def find():
    async with AsyncSessionLocal() as db:
        for kw in keywords:
            r = await db.execute(
                select(Content.id, Content.title, Content.type, Content.title_tr)
                .where(Content.title.ilike(f'%{kw}%'))
            )
            for row in r:
                print(f"ID={row[0]} | {row[2]:8} | {str(row[3] or '-'):30} | {row[1]}")

asyncio.run(find())
