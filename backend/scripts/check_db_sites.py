import asyncio
from backend.database import AsyncSessionLocal
from backend.models import Content
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def q():
    async with AsyncSessionLocal() as s:
        for cid in [469, 15, 315, 233, 203, 311]:
            r = await s.execute(select(Content).options(selectinload(Content.sites)).where(Content.id == cid))
            c = r.scalar_one_or_none()
            if c:
                print('ID={} {} ({})'.format(cid, c.title, c.type))
                for site in (c.sites or []):
                    url = (site.site_url or '')[:80]
                    print('  {}: {} (dead={})'.format(site.site_name, url, site.is_dead))

asyncio.run(q())
