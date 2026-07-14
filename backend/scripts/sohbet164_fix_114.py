"""SOHBET-164 — Add Marvel What If (114) to dizimag + final series fix."""
import sqlite3, os

DB = os.path.join("memory", "kurowatch.db")
db = sqlite3.connect(DB)

# 114 Marvel What If → dizimag WHAT / IF (HTTP 200, approximate match)
cid = 114
url = "https://www.dizimag.com.tr/what-if/"

# Mark old dizibox.so site as dead
db.execute("UPDATE site SET is_dead=1, is_primary=0 WHERE content_id=? AND site_url LIKE '%dizibox%'", (cid,))

# Add/update dizimag site
existing = db.execute("SELECT id FROM site WHERE content_id=? AND site_url LIKE '%dizimag%'", (cid,)).fetchone()
if existing:
    db.execute("UPDATE site SET site_url=?, site_name='dizimag.com.tr', is_primary=1, is_dead=0 WHERE id=?", (url, existing[0]))
else:
    db.execute("INSERT INTO site (content_id, site_name, site_url, is_primary, latest_known_ep, is_dead) VALUES (?, 'dizimag.com.tr', ?, 1, 1, 0)", (cid, url))

# Update episode URLs
db.execute("UPDATE episode SET url=? WHERE content_id=? AND (url LIKE '%dizibox%' OR url IS NULL OR url='')", (url, cid))

db.commit()

# Verify
cur = db.execute("SELECT site_name, site_url, is_primary, is_dead FROM site WHERE content_id=?", (cid,))
for r in cur.fetchall():
    print(f"  c.id={cid} site={r[0]} url={r[1]} primary={r[2]} dead={r[3]}")

db.close()
print("Done — Marvel What If added to dizimag.")
