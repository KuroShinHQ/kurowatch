"""Tüm Content + bağlı tablolarını (Site, Episode, Update, ContentTag) siler."""
import asyncio
from sqlalchemy import delete, select, func
from backend.database import AsyncSessionLocal
from backend.models import Content, ContentTag, Episode, Site, Update


async def main():
    async with AsyncSessionLocal() as s:
        count = (await s.execute(select(func.count()).select_from(Content))).scalar()
        # Bağlı tablolar önce silinmeli (FK sıralaması)
        await s.execute(delete(ContentTag))
        await s.execute(delete(Update))
        await s.execute(delete(Episode))
        await s.execute(delete(Site))
        await s.execute(delete(Content))
        await s.commit()
        print(f"{count} içerik + bağlı kayıtlar silindi.")


asyncio.run(main())
