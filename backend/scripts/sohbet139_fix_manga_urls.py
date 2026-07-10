"""SOHBET-139 SORUN 1: mangaokutr.com → ragnarscans.net episode URL replace"""
import sqlite3, os, re
from urllib.parse import urlparse, urlunparse

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "memory", "kurowatch.db")

DEAD_DOMAIN = "mangaokutr.com"
LIVE_DOMAIN = "ragnarscans.net"

conn = sqlite3.connect(DB_PATH)

# Find all episodes with mangaokutr.com URLs
rows = list(conn.execute(
    "SELECT e.[id], e.content_id, e.url, c.title "
    "FROM episode e "
    "JOIN content c ON c.id = e.content_id "
    "WHERE e.url LIKE ? ORDER BY e.content_id, e.number", (f"%{DEAD_DOMAIN}%",)
))
print(f"Total episodes with {DEAD_DOMAIN} URLs: {len(rows)}")

updated = 0
seen = set()
for ep_id, cid, url, title in rows:
    new_url = url.replace(DEAD_DOMAIN, LIVE_DOMAIN)
    if not new_url.startswith("http"):
        new_url = "https://" + new_url
    conn.execute("UPDATE episode SET url = ? WHERE [id] = ?", (new_url, ep_id))
    updated += 1
    seen.add(cid)
    print(f"  content#{cid} ('{title}'): {url[:60]}... -> {new_url[:60]}...")

conn.commit()
print(f"\nUpdated {updated} episodes across {len(seen)} contents")
conn.close()
