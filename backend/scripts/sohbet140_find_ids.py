"""Find specific content IDs."""
import sqlite3, os

db = os.path.join(os.path.dirname(__file__), "..", "..", "memory", "kurowatch.db")
conn = sqlite3.connect(db)
cur = conn.execute("SELECT id, title, type FROM content WHERE title LIKE '%naruto%' OR title LIKE '%Martial Peak%' OR title LIKE '%Solo Leveling%' OR title LIKE '%3 Idiots%' OR title LIKE '%Cult of the Lamb%' OR title LIKE '%3 idiots%'")
for r in cur.fetchall():
    # Check episodes
    ep_cur = conn.execute("SELECT COUNT(*) as cnt, COUNT(url) FILTER(WHERE url IS NOT NULL AND url != '') as ucnt FROM episode WHERE content_id = ?", (r[0],))
    ec = ep_cur.fetchone()
    site_cur = conn.execute("SELECT COUNT(*) FROM site WHERE content_id = ?", (r[0],))
    sc = site_cur.fetchone()
    print(f"  #{r[0]} '{r[1]}' ({r[2]}): eps={ec[0]}, urls={ec[1]}, sites={sc[0]}")
conn.close()
