#!/usr/bin/env python3
"""
SOHBET-156: Tüm sitelerin güncel durum keşfi.
- DB'deki tüm unique domainleri listele
- Her domaine HTTP HEAD/GET (curl_cffi ile)
- Cloudflare tespiti
- Sonuçları JSON'a kaydet
"""

import asyncio, json, os, re, sys, time
from datetime import datetime
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

RESULTS_FILE = '/mnt/c/Kuroshin/kurowatch/docs/sohbet156_discovery.json'
DOMAIN_INFO = {}

async def check_domain(domain: str, sample_urls: list[str]) -> dict:
    """Check a single domain using curl_cffi and requests."""
    result = {
        'domain': domain,
        'status': 'unknown',
        'http_status': None,
        'cf_detected': False,
        'response_time': None,
        'error': None,
        'sample_results': [],
        'content_preview': None,
    }

    # Skip non-Turkish domains
    en_domains = {'mangadex.org', 'fitgirl-repacks.site'}
    if domain in en_domains:
        result['status'] = 'skipped_en'
        return result

    # Try each sample URL or the domain itself
    urls_to_try = sample_urls[:3] if sample_urls else [f'https://{domain}/']

    for url in urls_to_try:
        t0 = time.time()
        try:
            # Try curl_cffi first (handles CF better)
            from curl_cffi import requests as curl_requests
            r = curl_requests.get(url, impersonate='chrome131', timeout=10, allow_redirects=True)
            dt = round(time.time() - t0, 2)
            
            headers = dict(r.headers)
            headers_lower = {k.lower(): v for k, v in headers.items()}
            text_lower = (r.text or '').lower()
            
            cf_detected = (
                'cf-ray' in headers_lower or
                'cf-cache-status' in headers_lower or
                'cloudflare' in headers_lower.get('server', '') or
                'cloudflare' in text_lower[:500] or
                'just a moment' in text_lower[:500] or
                'checking your browser' in text_lower[:500]
            )
            
            status_category = 'ok' if r.status_code == 200 else \
                             'redirect' if r.status_code in (301, 302, 307, 308) else \
                             'cf_blocked' if (r.status_code == 403 and cf_detected) else \
                             'not_found' if r.status_code == 404 else \
                             'error' if r.status_code >= 500 else \
                             f'http_{r.status_code}'
            
            entry = {
                'url': url,
                'http_status': r.status_code,
                'cf_detected': cf_detected,
                'response_time': dt,
                'content_length': len(r.text),
                'status_category': status_category,
            }
            result['sample_results'].append(entry)
            
            # Update aggregate
            if cf_detected:
                result['cf_detected'] = True
            if r.status_code and (result['http_status'] is None or r.status_code < result['http_status']):
                result['http_status'] = r.status_code
            if result['response_time'] is None or dt < result['response_time']:
                result['response_time'] = dt
            
            # Content preview (first 300 chars non-whitespace)
            if r.text and len(r.text) > 500:
                clean = re.sub(r'\s+', ' ', r.text[:300]).strip()
                result['content_preview'] = clean[:200]

        except Exception as e:
            dt = round(time.time() - t0, 2)
            result['sample_results'].append({
                'url': url,
                'error': str(e)[:100],
                'response_time': dt,
            })
            if not result['error']:
                result['error'] = str(e)[:100]

    # Determine aggregate status
    statuses = [s.get('status_category', 'error') for s in result['sample_results']]
    if 'ok' in statuses:
        result['status'] = 'alive'
    elif 'redirect' in statuses:
        result['status'] = 'redirect'
    elif 'cf_blocked' in statuses:
        result['status'] = 'cf_blocked'
    elif all(s == 'not_found' for s in statuses if s):
        result['status'] = 'dead_404'
    elif all(s == 'error' for s in statuses if s) or all(s.get('error') for s in result['sample_results']):
        result['status'] = 'dead_dns'
    else:
        result['status'] = 'unknown'

    return result


async def main():
    from backend.database import AsyncSessionLocal
    from backend.models import Site
    from sqlalchemy import select, distinct

    async with AsyncSessionLocal() as db:
        # Get all unique domains
        r = await db.execute(select(distinct(Site.site_url)).where(Site.site_url != None).where(Site.site_url != ''))
        all_urls = [row[0] for row in r.fetchall()]

    # Extract unique domains and their sample URLs
    domain_map = {}
    for url in all_urls:
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain not in domain_map:
                domain_map[domain] = []
            if len(domain_map[domain]) < 5:
                domain_map[domain].append(url)
        except:
            pass

    print(f'Total unique domains found: {len(domain_map)}')
    print(f'Total site records: {len(all_urls)}')
    print()

    domains_list = sorted(domain_map.keys())
    results = []

    for i, domain in enumerate(domains_list):
        samples = domain_map[domain]
        print(f'[{i+1}/{len(domains_list)}] {domain} ({len(samples)} URLs) ...', end=' ', flush=True)
        result = await check_domain(domain, samples)
        results.append(result)
        icon = '✅' if result['status'] == 'alive' else \
               '⚠️' if result['status'] == 'redirect' else \
               '🔒' if result['status'] == 'cf_blocked' else \
               '❌'
        print(f'{icon} {result["status"]} (HTTP {result["http_status"]}) {result.get("response_time", "?")}s')
        DOMAIN_INFO[domain] = result
        await asyncio.sleep(1)  # rate limit

    # Summary
    alive = sum(1 for r in results if r['status'] == 'alive')
    redirect = sum(1 for r in results if r['status'] == 'redirect')
    cf_blocked = sum(1 for r in results if r['status'] == 'cf_blocked')
    dead = sum(1 for r in results if r['status'] in ('dead_dns', 'dead_404', 'unknown'))

    print()
    print('=' * 50)
    print('DISCOVERY SUMMARY')
    print('=' * 50)
    print(f'Alive:       {alive}')
    print(f'Redirect:    {redirect}')
    print(f'CF Blocked:  {cf_blocked}')
    print(f'Dead:        {dead}')
    print(f'Total:       {len(results)}')
    print()

    # Save
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_domains': len(results),
        'total_site_records': len(all_urls),
        'summary': {
            'alive': alive,
            'redirect': redirect,
            'cf_blocked': cf_blocked,
            'dead': dead,
        },
        'domains': results,
    }
    with open(RESULTS_FILE, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f'Report saved: {RESULTS_FILE}')


if __name__ == '__main__':
    asyncio.run(main())
