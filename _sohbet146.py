"""
SOHBET-146: hdfilmcehennemi domain güncellemesi (107 film)
"""
import sqlite3
import httpx
import re
from urllib.parse import urlparse

db = sqlite3.connect('memory/kurowatch.db')
cur = db.cursor()

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
HEADERS = {"User-Agent": UA}

print("=" * 60)
print("SOHBET-146 — hdfilmcehennemi Domain Güncellemesi")
print("=" * 60)

# Step 1: Analyze current episode URL patterns
print("\n--- 1. Mevcut hdfilmcehennemi URL pattern'leri ---")
cur.execute("""
    SELECT e.url, c.title, c.type
    FROM episode e
    JOIN content c ON c.id = e.content_id
    WHERE e.url LIKE '%hdfilmcehennemi%'
    LIMIT 20
""")
urls = []
for row in cur.fetchall():
    urls.append(row[0])
    print(f"  [{row[2]}] {row[1][:40]:40s} -> {row[0][:80]}")

# Extract path patterns
print("\n  Path patterns:")
for u in urls:
    parsed = urlparse(u)
    print(f"    {parsed.path}")

# Step 2: Check hdfilmcehennemi.nl URL structure
print("\n--- 2. hdfilmcehennemi.nl URL yapısı testi ---")

# Try to get a movie listing from .nl
r = httpx.get("https://www.hdfilmcehennemi.nl/", headers=HEADERS, follow_redirects=True, timeout=15)
print(f"  .nl homepage: {r.status_code} ({len(r.text)} bytes)")

# Find movie links on .nl
movie_links = re.findall(r'href=["\'](https?://www\.hdfilmcehennemi\.nl[^"\']+)', r.text)
print(f"  Found {len(movie_links)} links on .nl")
for l in movie_links[:10]:
    print(f"    {l}")

# Check if /film/ path exists on .nl
r2 = httpx.get("https://www.hdfilmcehennemi.nl/film/", headers=HEADERS, follow_redirects=True, timeout=15)
print(f"\n  .nl/film/: {r2.status_code}")

# Check the actual DB episodes to understand .now URL pattern vs .nl
print("\n--- 3. hdfilmcehennemi URL comparison ---")
# Get a sample .now URL and check if .nl equivalent exists
cur.execute("""
    SELECT e.url, c.title
    FROM episode e
    JOIN content c ON c.id = e.content_id
    WHERE e.url LIKE '%hdfilmcehennemi.now%'
    LIMIT 5
""")
for row in cur.fetchall():
    old_url = row[0]
    # Replace .now with .nl
    new_url = old_url.replace('hdfilmcehennemi.now', 'hdfilmcehennemi.nl')
    try:
        r3 = httpx.head(new_url, headers=HEADERS, follow_redirects=True, timeout=10)
        print(f"  [{r3.status_code}] {row[1][:30]:30s} {new_url[:80]}")
    except Exception as e:
        print(f"  [ERR] {row[1][:30]:30s} {str(e)[:40]}")

db.close()
