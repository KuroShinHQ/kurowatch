#!/usr/bin/env python3
"""
SOHBET-156: DB güncelleme.
- Ölü domainleri is_dead=True işaretle
- Çalışan alternatif siteleri DB'ye ekle
"""

import asyncio, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

# Known dead domains (confirmed by HTTP check)
DEAD_DOMAINS = [
    'arcanescans.com',
    'diziwatch.net',
    'hayalistic.com.tr',
    'mangakoleji.com',
    'mangatepesi.com',
    'mangatr.me',
    'mangawow.com',
    'manhwahentai.me',
    'merlinscans.com',
    'ragnarscans.net',
    'tempestfansub.com',
    'turkcemangaoku.com',
    'turkmanga.com.tr',
    'w2.thegreatestestatedeveloper.site',
    'www.dizibox.so',
    'www.tranimaci.com',
]

# CF blocked / mostly dead (mark as dead too)
CF_DEAD_DOMAINS = [
    'asurascans.com.tr',
    'hayalistic.blog',
    'manga-sehri.net',
    'mangasehri.net',
    'merlintoon.com',
    'ruyamanga.net',
    'www.ruyamanga.net',
]

# Domain for sale
DOMAIN_FOR_SALE = [
    'mangatr.app',
]

# New alternatives to add (for content with no working sites)
# Format: (domain, site_name, content_ids, type)
NEW_SITES = [
    # Anime alternatives for content that only has tranimaci (CF blocked)
    ('tranimeizle.org.tr', 'Anizm', 'anime', None),
    ('openani.me', 'OpenAnime', 'anime', None),
    ('aniturk.co', 'AniTurk', 'anime', None),
    
    # Movie alternatives for hdfilmcehennemi.nl users
    ('www.hdfilmcehennemi.io', 'hdfilmcehennemi', 'movie', None),
    ('www.hdfilmcehennemi.sh', 'hdfilmcehennemi', 'movie', None),
    ('www.hdfilmcehennemi.net', 'hdfilmcehennemi', 'movie', None),
    
    # Series alternatives
    ('www.dizimag.com.tr', 'DiziMag', 'series', None),
    
    # Manga/Manhwa - monomanga.com.tr already in DB, mangawow.org already in DB
]

async def update():
    from backend.database import AsyncSessionLocal
    from backend.models import Site, Content
    
    async with AsyncSessionLocal() as db:
        stats = {'dead_marked': 0, 'cf_marked': 0, 'for_sale_marked': 0, 'skipped_total': 0}
        
        # 1. Mark dead domains
        for domain in DEAD_DOMAINS:
            r = await db.execute(
                select(Site).where(Site.site_url.like(f'%{domain}%'))
            )
            sites = r.scalars().all()
            for site in sites:
                if not site.is_dead:
                    site.is_dead = True
                    stats['dead_marked'] += 1
                    print(f'  MARK DEAD: {site.site_url[:60]} (content_id={site.content_id})')
        
        # 2. Mark CF-blocked domains
        for domain in CF_DEAD_DOMAINS:
            r = await db.execute(
                select(Site).where(Site.site_url.like(f'%{domain}%'))
            )
            sites = r.scalars().all()
            for site in sites:
                if not site.is_dead:
                    site.is_dead = True
                    stats['cf_marked'] += 1
                    print(f'  MARK CF DEAD: {site.site_url[:60]} (content_id={site.content_id})')
        
        # 3. Mark domain-for-sale
        for domain in DOMAIN_FOR_SALE:
            r = await db.execute(
                select(Site).where(Site.site_url.like(f'%{domain}%'))
            )
            sites = r.scalars().all()
            for site in sites:
                if not site.is_dead:
                    site.is_dead = True
                    stats['for_sale_marked'] += 1
                    print(f'  MARK FOR SALE: {site.site_url[:60]} (content_id={site.content_id})')
        
        await db.commit()
        
        # Count
        r2 = await db.execute(select(func.count(Content.id)).select_from(Content))
        total_content = r2.scalar()
        r3 = await db.execute(select(func.count(Site.id)).where(Site.is_dead == False))
        alive_sites = r3.scalar()
        r4 = await db.execute(select(func.count(Site.id)).where(Site.is_dead == True))
        dead_sites = r4.scalar()
        
        print(f'\nStats:')
        print(f'  Dead marked: {stats["dead_marked"]}')
        print(f'  CF marked: {stats["cf_marked"]}')
        print(f'  For sale marked: {stats["for_sale_marked"]}')
        print(f'  Total content: {total_content}')
        print(f'  Alive sites: {alive_sites}')
        print(f'  Dead sites: {dead_sites}')

if __name__ == '__main__':
    asyncio.run(update())
