#!/usr/bin/env python3
"""SOHBET-155: Pratik %5 test — çalışan türlere odaklan."""

import asyncio, json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database import AsyncSessionLocal
from backend.models import Content
from sqlalchemy import select
from sqlalchemy.orm import selectinload

BASE = '/mnt/c/Kuroshin/kurowatch/downloads/s155'
RESULTS = []

CONTENT = {
    'manga':  [1],      # Martial Peak
    'manhwa': [24, 10],  # HLW, Returner
    'series': [287],     # Dexter (hdfilmcehennemi.nl canli)
    'movie':  [203, 311], # 3 Idiots, Fight Club
    'game':   [128, 127],# Cult of the Lamb, Frostpunk 2
}

async def run():
    os.makedirs(BASE, exist_ok=True)
    print('=== S155 TEST ===\n')

    for ctype, ids in CONTENT.items():
        if not ids:
            continue
        async with AsyncSessionLocal() as db:
            for cid in ids:
                r = await db.execute(select(Content).options(selectinload(Content.sites)).where(Content.id == cid))
                c = r.scalar_one_or_none()
                if not c:
                    print(f'SKIP ID={cid}')
                    continue

                sites = sorted([s for s in (c.sites or []) if not s.is_dead and s.site_url], key=lambda s: 0 if s.is_primary else 1)
                if not sites:
                    RESULTS.append({'id': cid, 'title': c.title, 'type': ctype, 'status': 'FAILED', 'error': 'site yok'})
                    print(f'FAIL {c.title}: site yok')
                    continue

                site = sites[0]
                print(f'TEST {c.title} ({ctype}) -> {site.site_name}')

                t0 = time.time()
                try:
                    if ctype == 'game':
                        res = await test_game(c, site)
                    elif ctype in ('manga', 'manhwa'):
                        res = await test_manga(c, site)
                    elif ctype in ('series', 'movie'):
                        res = await test_video(c, site)
                    else:
                        res = {'status': 'SKIP', 'error': 'bilinmeyen tip'}
                    
                    dur = time.time() - t0
                    res['duration'] = round(dur, 1)
                    RESULTS.append(res)
                    print(f'  -> {res["status"]} ({dur:.0f}s)')
                    
                except Exception as e:
                    RESULTS.append({'id': cid, 'title': c.title, 'type': ctype, 'status': 'FAILED', 'error': str(e)[:150], 'duration': round(time.time()-t0, 1)})
                    print(f'  -> FAILED: {str(e)[:80]}')
                
                await asyncio.sleep(0.5)

    # Report
    print('\n' + '='*40)
    ok = sum(1 for r in RESULTS if r['status'] == 'OK')
    fail = sum(1 for r in RESULTS if r['status'] == 'FAILED')
    print(f'OK: {ok}  FAIL: {fail}  TOTAL: {len(RESULTS)}')
    
    report = {
        'results': RESULTS,
        'summary': {'ok': ok, 'fail': fail, 'total': len(RESULTS)},
    }
    with open('/mnt/c/Kuroshin/kurowatch/docs/S155_RESULTS.json', 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print('Rapor: docs/S155_RESULTS.json')

async def test_manga(c, site):
    from backend.routers.episodes import _derive_ep_url, _extract_ep_from_url
    ep = _extract_ep_from_url(site.site_url) or 1
    url = _derive_ep_url(site.site_url, ep, 1) if ep else site.site_url
    if not url:
        return {'id': c.id, 'title': c.title, 'type': c.type, 'status': 'FAILED', 'error': 'url tureme hatasi'}
    
    out = os.path.join(BASE, f'{c.type}_{c.id}', 'ep001')
    os.makedirs(out, exist_ok=True)
    
    from backend.downloader.manga import download_manga_chapter
    files = await asyncio.wait_for(download_manga_chapter(url, out), timeout=60)
    
    valid = [(f, os.path.getsize(f)) for f in files[:2] if os.path.exists(f) and os.path.getsize(f) > 0]
    if not valid:
        return {'id': c.id, 'title': c.title, 'type': c.type, 'status': 'FAILED', 'error': 'sayfa yok'}
    
    # Cleanup
    for f in files:
        try: os.remove(f)
        except: pass
    try: os.rmdir(out)
    except: pass
    
    return {'id': c.id, 'title': c.title, 'type': c.type, 'status': 'OK', 'files': len(valid), 'bytes': sum(s for _, s in valid)}

async def test_video(c, site):
    dead = ('setfilmizle.uk', 'dizipod.com')
    if any(d in site.site_url.lower() for d in dead):
        return {'id': c.id, 'title': c.title, 'type': c.type, 'status': 'FAILED', 'error': 'site kaldirilmis'}
    
    from backend.routers.episodes import _derive_ep_url, _extract_ep_from_url
    ep = _extract_ep_from_url(site.site_url) or 1
    url = _derive_ep_url(site.site_url, ep, 1) if ep else site.site_url
    if not url:
        return {'id': c.id, 'title': c.title, 'type': c.type, 'status': 'FAILED', 'error': 'url tureme hatasi'}
    
    from backend.downloader.stream_finder import find_stream_url_with_tags
    stream, _ = await asyncio.wait_for(find_stream_url_with_tags(url, 'anime'), timeout=90)
    if not stream or stream == url:
        return {'id': c.id, 'title': c.title, 'type': c.type, 'status': 'FAILED', 'error': 'stream url yok'}
    
    return {'id': c.id, 'title': c.title, 'type': c.type, 'status': 'OK', 'stream_url': stream[:80]}

async def test_game(c, site):
    import httpx
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as cl:
        r = await cl.get(site.site_url, headers={'User-Agent': 'Mozilla/5.0'})
        if r.status_code != 200:
            return {'id': c.id, 'title': c.title, 'type': c.type, 'status': 'FAILED', 'error': f'HTTP {r.status_code}'}
        mag = re.findall(r'magnet:\?xt=urn:btih:[a-zA-Z0-9]{32,40}', r.text)
        if not mag:
            return {'id': c.id, 'title': c.title, 'type': c.type, 'status': 'FAILED', 'error': 'magnet yok'}
    return {'id': c.id, 'title': c.title, 'type': c.type, 'status': 'OK', 'magnets': len(mag)}

if __name__ == '__main__':
    asyncio.run(run())
