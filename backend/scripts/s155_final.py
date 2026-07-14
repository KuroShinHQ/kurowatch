#!/usr/bin/env python3
"""SOHBET-155 Final: Tests what actually works, documents failures."""

import asyncio, json, os, re, sys, time
from datetime import datetime

BASE = '/mnt/c/Kuroshin/kurowatch/downloads/s155'
RESULTS = []
SITES_STATUS = {}

# Test manifest: only test things that have a chance of working
TEST_PLAN = [
    # Manga - MangaDex (known working)
    {'id': 1, 'title': 'Martial Peak', 'type': 'manga', 'url': 'https://mangadex.org/chapter/1e9f55cb-edc3-4ef7-bc70-64111089f18a', 'method': 'mangadex'},
    # Games - FitGirl (known working)
    {'id': 128, 'title': 'Cult of the Lamb', 'type': 'game', 'url': 'https://fitgirl-repacks.site/cult-of-the-lamb/', 'method': 'fitgirl'},
    {'id': 127, 'title': 'Frostpunk 2', 'type': 'game', 'url': 'https://fitgirl-repacks.site/frostpunk-2/', 'method': 'fitgirl'},
    # Manhwa - find and test from DB
    {'id': 24, 'title': 'Hardcore Leveling Warrior', 'type': 'manhwa', 'method': 'check_sites'},
    {'id': 69, 'title': 'Solo Leveling', 'type': 'manhwa', 'method': 'check_sites'},
    # Series - test what sites exist
    {'id': 469, 'title': 'Game of Thrones', 'type': 'series', 'method': 'check_sites'},
    {'id': 15, 'title': 'Breaking Bad', 'type': 'series', 'method': 'check_sites'},
    # Movies - test hdfilmcehennemi
    {'id': 203, 'title': '3 Idiots', 'type': 'movie', 'url': 'https://www.hdfilmcehennemi.nl/film/3-aptal-2009-izle-2/', 'method': 'stream'},
    {'id': 311, 'title': 'Fight Club', 'type': 'movie', 'url': 'https://www.hdfilmcehennemi.nl/film/dovus-kulubu-1999-izle-2/', 'method': 'stream'},
    {'id': 315, 'title': 'The Silence of the Lambs', 'type': 'movie', 'method': 'check_sites'},
    # Anime via stream_finder
    {'id': 233, 'title': 'Naruto', 'type': 'anime', 'url': 'https://tranimaci.com/naruto-1-bolum-izle', 'method': 'stream'},
]

def log_result(item, status, details=None, duration=None):
    r = {'id': item['id'], 'title': item['title'], 'type': item['type'], 'method': item.get('method'), 'status': status}
    if details:
        r['details'] = str(details)[:200]
    if duration:
        r['duration'] = round(duration, 1)
    RESULTS.append(r)
    icon = 'OK' if status == 'OK' else 'FAIL'
    print(f'  [{icon}] {item["title"]}: {status} {details or ""}')

async def test_mangadex(item):
    from backend.downloader.manga import download_manga_chapter
    out = os.path.join(BASE, f'manga_{item["id"]}', 'ch01')
    os.makedirs(out, exist_ok=True)
    t0 = time.time()
    try:
        files = await asyncio.wait_for(download_manga_chapter(item['url'], out), timeout=60)
        valid = [f for f in files if os.path.exists(f) and os.path.getsize(f) > 0]
        # Quick validation
        from PIL import Image
        verified = 0
        for f in valid[:3]:
            try:
                Image.open(f).verify()
                verified += 1
            except:
                pass
        # Cleanup
        for f in files:
            try: os.remove(f)
            except: pass
        try: os.rmdir(out)
        except: pass
        dur = time.time() - t0
        if valid:
            log_result(item, 'OK', f'{len(valid)} pages, {verified} verified', dur)
        else:
            log_result(item, 'FAILED', '0 valid pages', dur)
    except asyncio.TimeoutError:
        log_result(item, 'FAILED', 'timeout 60s', time.time()-t0)
    except Exception as e:
        log_result(item, 'FAILED', str(e)[:100], time.time()-t0)

async def test_fitgirl(item):
    import httpx
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as cl:
            r = await cl.get(item['url'], headers={'User-Agent': 'Mozilla/5.0'})
            if r.status_code != 200:
                log_result(item, 'FAILED', f'HTTP {r.status_code}', time.time()-t0)
                return
            mags = re.findall(r'magnet:\?xt=urn:btih:[a-zA-Z0-9]{32,}', r.text)
            if mags:
                log_result(item, 'OK', f'{len(mags)} magnet links', time.time()-t0)
            else:
                log_result(item, 'FAILED', 'no magnet links found', time.time()-t0)
    except Exception as e:
        log_result(item, 'FAILED', str(e)[:100], time.time()-t0)

async def test_stream(item):
    from backend.downloader.stream_finder import find_stream_url_with_tags
    t0 = time.time()
    try:
        stream, tags = await asyncio.wait_for(find_stream_url_with_tags(item['url'], 'anime'), timeout=90)
        if stream and stream != item['url']:
            log_result(item, 'OK', f'stream={stream[:60]} tags={tags}', time.time()-t0)
        else:
            log_result(item, 'FAILED', 'stream URL bulunamadi', time.time()-t0)
    except asyncio.TimeoutError:
        log_result(item, 'FAILED', 'timeout 90s', time.time()-t0)
    except Exception as e:
        log_result(item, 'FAILED', str(e)[:100], time.time()-t0)

async def test_check_sites(item):
    """List available sites for this content."""
    from backend.database import AsyncSessionLocal
    from backend.models import Content
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    t0 = time.time()
    try:
        async with AsyncSessionLocal() as db:
            r = await db.execute(select(Content).options(selectinload(Content.sites)).where(Content.id == item['id']))
            c = r.scalar_one_or_none()
            if not c or not c.sites:
                log_result(item, 'FAILED', 'DB site yok', time.time()-t0)
                return
            working = []
            dead = []
            for s in c.sites:
                if s.is_dead or 'setfilmizle' in (s.site_url or '') or 'dizipod' in (s.site_url or ''):
                    dead.append(f'{s.site_name} (dead)')
                else:
                    working.append(f'{s.site_name}={s.site_url[:60]}')
            details = f'{len(working)} live, {len(dead)} dead'
            if not working:
                log_result(item, 'FAILED', details, time.time()-t0)
            else:
                log_result(item, 'WARN', details + ' | ' + ' | '.join(working[:3]), time.time()-t0)
    except Exception as e:
        log_result(item, 'FAILED', str(e)[:100], time.time()-t0)

async def run():
    os.makedirs(BASE, exist_ok=True)
    print('=== SOHBET-155 FINAL TEST ===')
    print(f'Started: {datetime.now().isoformat()}\n')

    for item in TEST_PLAN:
        method = item.get('method')
        print(f'\n--- {item["title"]} ({item["type"]}) [{method}] ---')
        if method == 'mangadex':
            await test_mangadex(item)
        elif method == 'fitgirl':
            await test_fitgirl(item)
        elif method == 'stream':
            await test_stream(item)
        elif method == 'check_sites':
            await test_check_sites(item)
        else:
            log_result(item, 'SKIP', f'unknown method: {method}')

    # Summary
    print('\n' + '=' * 50)
    print('SUMMARY')
    print('=' * 50)
    ok = sum(1 for r in RESULTS if r['status'] == 'OK')
    warn = sum(1 for r in RESULTS if r['status'] == 'WARN')
    fail = sum(1 for r in RESULTS if r['status'] == 'FAILED')
    print(f'OK={ok}  WARN={warn}  FAIL={fail}  Total={len(RESULTS)}')

    # Save report
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {'ok': ok, 'warn': warn, 'fail': fail, 'total': len(RESULTS)},
        'results': RESULTS,
        'sites_status': SITES_STATUS,
    }
    report_path = '/mnt/c/Kuroshin/kurowatch/docs/S155_RESULTS.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f'\nReport: {report_path}')

if __name__ == '__main__':
    asyncio.run(run())
