#!/usr/bin/env python3
"""
SOHBET-156: Alternatif site bulucu ve test edici.
Bulunan alternatifleri test eder, çalışanları JSON'a kaydeder.
"""

import asyncio, json, os, sys
from datetime import datetime

RESULTS_FILE = '/mnt/c/Kuroshin/kurowatch/docs/sohbet156_alts.json'

# Alternative sites to test, grouped by category
ALT_CANDIDATES = {
    'anime': [
        ('Anizm (tranimeizle.org.tr)', 'https://tranimeizle.org.tr/naruto-1-bolum-izle', 'anime'),
        ('OpenAnime', 'https://openani.me/', 'anime'),
        ('AniTurk', 'https://www.aniturk.co/', 'anime'),
        ('turkanime.co', 'https://www.turkanime.co/', 'anime'),
        ('animexe.com', 'https://animexe.com/watch/naruto/1/1', 'anime'),
    ],
    'movie': [
        ('hdfilmcehennemi.io', 'https://www.hdfilmcehennemi.io/', 'movie'),
        ('hdfilmcehennemi.sh', 'https://www.hdfilmcehennemi.sh/', 'movie'),
        ('hdfilmcehennemi.net', 'https://www.hdfilmcehennemi.net/', 'movie'),
    ],
    'series': [
        ('dizimag.com.tr', 'https://www.dizimag.com.tr/', 'series'),
        ('netdizi.live', 'https://www.netdizi.live/', 'series'),
        ('dizibox.vip', 'https://dizibox.vip/', 'series'),
        ('roketdizi.com', 'https://www.roketdizi.com/', 'series'),
    ],
    'manga': [
        ('monomanga.com.tr', 'https://monomanga.com.tr/manga/hardcore-leveling-warrior/bolum-1/', 'manga'),
        ('mangawow.org', 'https://mangawow.org/', 'manga'),
        ('majorscans.com', 'https://www.majorscans.com/', 'manga'),
    ],
    'manhwa': [
        ('monomanga.com.tr', 'https://monomanga.com.tr/manga/hardcore-leveling-warrior/bolum-1/', 'manhwa'),
        ('majorscans.com', 'https://www.majorscans.com/', 'manhwa'),
    ],
}

async def test_site(name: str, url: str, ctype: str) -> dict:
    """Test a candidate site with both requests and curl_cffi."""
    result = {
        'name': name,
        'url': url[:100],
        'type': ctype,
        'status': 'unknown',
        'http_status': None,
        'cf_detected': False,
        'response_time': None,
        'content_length': 0,
    }
    
    import time, httpx
    t0 = time.time()
    
    # Try httpx first
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as cl:
            r = await cl.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
            })
            dt = round(time.time() - t0, 2)
            text_lower = (r.text or '').lower()
            
            result['http_status'] = r.status_code
            result['response_time'] = dt
            result['content_length'] = len(r.text)
            
            cf_detected = any(x in text_lower[:1000] for x in ['cloudflare', 'just a moment', 'checking your browser'])
            result['cf_detected'] = cf_detected
            
            if r.status_code == 200 and not cf_detected and len(r.text) > 1000:
                result['status'] = 'alive'
            elif r.status_code == 200 and cf_detected:
                result['status'] = 'cf_blocked'
            elif r.status_code == 200 and len(r.text) < 500:
                result['status'] = 'dead_short'
            elif r.status_code == 404:
                result['status'] = 'dead_404'
            elif r.status_code == 403:
                result['status'] = 'cf_blocked'
            else:
                result['status'] = f'http_{r.status_code}'
                
    except httpx.TimeoutException:
        result['status'] = 'dead_timeout'
        result['response_time'] = round(time.time() - t0, 2)
    except Exception as e:
        result['status'] = 'dead_error'
        result['error'] = str(e)[:80]
        result['response_time'] = round(time.time() - t0, 2)
    
    return result

async def main():
    print('=== SOHBET-156: ALTERNATIF SITE TEST ===\n')
    
    all_results = {}
    summary = {'alive': 0, 'cf_blocked': 0, 'dead': 0}
    
    for category, sites in ALT_CANDIDATES.items():
        print(f'\n--- {category.upper()} ---')
        category_results = []
        for name, url, ctype in sites:
            print(f'  Testing {name} ...', end=' ', flush=True)
            result = await test_site(name, url, ctype)
            icon = '✅' if result['status'] == 'alive' else '🔒' if 'cf' in result['status'] else '❌'
            print(f'{icon} {result["status"]} (HTTP {result["http_status"]}) {result.get("response_time","")}s')
            category_results.append(result)
            
            if result['status'] == 'alive':
                summary['alive'] += 1
            elif 'cf' in result['status']:
                summary['cf_blocked'] += 1
            else:
                summary['dead'] += 1
        
        all_results[category] = category_results
        await asyncio.sleep(0.3)
    
    print(f'\n=== SUMMARY ===')
    print(f'Alive: {summary["alive"]}  CF: {summary["cf_blocked"]}  Dead: {summary["dead"]}')
    
    # Save
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': summary,
        'categories': all_results,
    }
    with open(RESULTS_FILE, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f'\nSaved: {RESULTS_FILE}')

if __name__ == '__main__':
    asyncio.run(main())
