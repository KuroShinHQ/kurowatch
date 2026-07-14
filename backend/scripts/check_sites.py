#!/usr/bin/env python3
import requests, re

sites = [
    ('mangasehri.net', 'https://mangasehri.net/manga/the-beginning-after-the-end/bolum-1/?style=list'),
    ('mangakurdo.com', 'https://mangakurdo.com/manga/the-beginning-after-the-end/bolum-1/'),
    ('hdfilmcehennemi.nl', 'https://www.hdfilmcehennemi.nl/film/3-aptal-2009-izle-2/'),
    ('monomanga.com.tr', 'https://monomanga.com.tr/manga/hardcore-leveling-warrior/bolum-1/'),
    ('merlintoon.com', 'https://merlintoon.com/manga/hardcore-leveling-warrior/bolum-1/'),
    ('dizipub.com', 'https://dizipub.com/'),
]

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
for name, url in sites:
    try:
        r = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        print(f'{name}: status={r.status_code} len={len(r.text)}')
        if len(r.text) < 800:
            print(f'  SHORT: {r.text[:200]}')
        elif 'domain is for sale' in r.text.lower():
            print('  -> DOMAIN FOR SALE')
        elif 'cloudflare' in r.text.lower() and 'checking' in r.text.lower():
            print('  -> CF CHALLENGE')
        elif 'reading-content' in r.text or 'chapter-img' in r.text:
            imgs = re.findall(r'<img[^>]+>', r.text)
            print(f'  -> HAS CONTENT ({len(imgs)} img tags)')
        else:
            sample = r.text[200:400].replace('\n',' ').strip()[:100]
            print(f'  -> Unknown: {sample}...')
    except Exception as e:
        print(f'{name}: ERROR {str(e)[:80]}')
