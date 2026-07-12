"""Test a sample of updated URLs"""
import sqlite3
import httpx
import re

db = sqlite3.connect('memory/kurowatch.db')
cur = db.cursor()

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# Test ragnarscans.net URLs
print("=== ragnarscans.net sample test ===")
cur.execute("""
    SELECT e.url FROM episode e 
    WHERE e.url LIKE '%ragnarscans.net%' AND e.url NOT LIKE '%ragnarscans.com%'
    LIMIT 5
""")
for row in cur.fetchall():
    url = row[0]
    try:
        r = httpx.head(url, headers=headers, follow_redirects=True, timeout=10)
        print(f"  [{r.status_code}] {url[:90]}")
    except Exception as e:
        print(f"  [ERR] {url[:90]} -> {str(e)[:40]}")

# Test mangatr.app URLs
print("\n=== mangatr.app sample test ===")
cur.execute("""
    SELECT e.url FROM episode e 
    WHERE e.url LIKE '%mangatr.app%' AND e.url NOT LIKE '%mangatr.net%'
    LIMIT 5
""")
for row in cur.fetchall():
    url = row[0]
    try:
        r = httpx.head(url, headers=headers, follow_redirects=True, timeout=10)
        print(f"  [{r.status_code}] {url[:90]}")
    except Exception as e:
        print(f"  [ERR] {url[:90]} -> {str(e)[:40]}")

db.close()
