import asyncio
from backend.database import AsyncSessionLocal
from backend.models import Content, Site
from sqlalchemy import select, distinct, join

async def categorize():
    async with AsyncSessionLocal() as db:
        # Get all unique domains with their content types
        r = await db.execute(
            select(Site.site_url, Content.type)
            .join(Content, Site.content_id == Content.id)
            .where(Site.site_url != None)
            .where(Site.site_url != '')
            .distinct()
        )
        rows = r.fetchall()
    
    # Group by domain
    domain_types = {}
    for site_url, ctype in rows:
        from urllib.parse import urlparse
        try:
            domain = urlparse(site_url).netloc.lower()
        except:
            domain = site_url
        if domain not in domain_types:
            domain_types[domain] = set()
        domain_types[domain].add(ctype or 'unknown')
    
    # Known English sites
    known_en = {'mangadex.org', 'fitgirl-repacks.site', 'anilist.co', 'myanimelist.net'}
    
    # Turkish keywords in domain
    tr_keywords = ['izle', 'dizi', 'film', 'manga', 'anime', 'turkanime', 'tranimaci',
                   'ragnarscans', 'merlintoon', 'monomanga', 'mangasehri', 'mangatr',
                   'mangagezgini', 'mangaokutr', 'manhwahentai', 'setfilmizle', 'dizipod',
                   'dizibox', 'dizimag', 'dizipal', 'hdfilmcehennemi', 'fullhdfilmizlesene',
                   'sezonlukdizi', 'dizigom', 'asurascans', 'arcanescans', 'mangakurdo',
                   'hayalistic', 'mangatepesi', 'ruyamanga', 'majorscans']
    
    print('=== ALL DOMAINS BY TYPE ===')
    print()
    
    tr_domains = []
    en_domains = []
    other_domains = []
    
    for domain, types in sorted(domain_types.items()):
        is_tr = any(kw in domain for kw in tr_keywords) or domain.endswith('.com.tr')
        is_en = domain in known_en
        
        type_str = ','.join(sorted(types))
        label = '🇹🇷 TR' if is_tr else '🇬🇧 EN' if is_en else '❓ ?'
        
        print('{} {:40s} [{}]'.format(label, domain, type_str))
        
        if is_tr:
            tr_domains.append(domain)
        elif is_en:
            en_domains.append(domain)
        else:
            other_domains.append(domain)
    
    print()
    print('=' * 50)
    print('TR domains:  {}'.format(len(tr_domains)))
    print('EN domains:  {}'.format(len(en_domains)))
    print('Other:       {}'.format(len(other_domains)))
    print('Total:       {}'.format(len(domain_types)))

asyncio.run(categorize())
