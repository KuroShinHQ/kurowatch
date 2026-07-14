"""SOHBET-157: Test alternative site URL patterns"""
import asyncio
import httpx
import sqlite3
from urllib.parse import urlparse

async def check_url(url, label=""):
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as cl:
        try:
            r = await cl.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept-Language': 'tr-TR,tr;q=0.9'
            })
            print(f"  {label:50s} HTTP {r.status_code} ({len(r.text)} bytes)")
            return r.status_code == 200
        except Exception as e:
            print(f"  {label:50s} ERROR: {e}")
            return False

async def main():
    print("=== HDFILMCEHENNEMI.IO URL PATTERNS ===")
    # Test various URL patterns on .io mirror
    base_io = "https://www.hdfilmcehennemi.io"
    patterns = [
        ("/film/3-aptal-2009-izle-2/", "old /film/ pattern"),
        ("/film/dovus-kulubu-1999-izle-2/", "old /film/ fight club"),
        ("/3-aptal-2009-izle-2/", "no /film/ with -2"),
        ("/3-aptal-2009-izle/", "no /film/ izle"),
        ("/3-aptal-izle/", "no /film/ short"),
        ("/3-aptal/", "no /film/ just slug"),
        ("/american-psycho/", "no /film/ american psycho"),
        ("/fight-club-1999-izle/", "no /film/ fight club"),
        ("/film/300/", "old /film/ 300"),
    ]
    for path, label in patterns:
        await check_url(base_io + path, label)

    print()
    print("=== DIZIMAG.COM.TR URL PATTERNS ===")
    base_dm = "https://www.dizimag.com.tr"
    d_patterns = [
        ("/", "homepage"),
        ("/dizi/breaking-bad/", "/dizi/ pattern"),
        ("/breaking-bad/", "just slug"),
        ("/diziler/breaking-bad/", "/diziler/ pattern"),
    ]
    for path, label in d_patterns:
        await check_url(base_dm + path, label)

    print()
    print("=== TRANIMEIZLE.ORG.TR URL PATTERNS ===")
    base_tm = "https://tranimeizle.org.tr"
    t_patterns = [
        ("/naruto-1-bolum-izle", "naruto bolum"),
        ("/solo-leveling-1-bolum-izle", "solo leveling bolum"),
    ]
    for path, label in t_patterns:
        await check_url(base_tm + path, label)

    print()
    print("=== OPENANIME URL PATTERNS ===")
    base_oa = "https://openani.me"
    oa_patterns = [
        ("/", "homepage"),
    ]
    for path, label in oa_patterns:
        await check_url(base_oa + path, label)

    print()
    print("=== ANITURK URL PATTERNS ===")
    base_at = "https://www.aniturk.co"
    at_patterns = [
        ("/", "homepage"),
    ]
    for path, label in at_patterns:
        await check_url(base_at + path, label)

    print()
    print("=== HDFILMCEHENNEMI.SH PATTERNS ===")
    base_sh = "https://www.hdfilmcehennemi.sh"
    sh_patterns = [
        ("/film/3-aptal-2009-izle-2/", "old /film/ pattern"),
        ("/3-aptal/", "just slug"),
    ]
    for path, label in sh_patterns:
        await check_url(base_sh + path, label)

asyncio.run(main())
