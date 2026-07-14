"""SOHBET-157: DB exploration - understand URL patterns and site distribution"""
import sqlite3
from collections import Counter

db = sqlite3.connect('memory/kurowatch.db')
cur = db.cursor()

# Type distribution
cur.execute("SELECT type, COUNT(*) FROM content GROUP BY type ORDER BY type")
print("=== CONTENT TYPE DISTRIBUTION ===")
for row in cur.fetchall():
    print(f"  {row[0]:10s}  {row[1]}")

print()

# Alive sites per content type
cur.execute("""
    SELECT c.type, s.site_name, COUNT(*) as cnt
    FROM site s
    JOIN content c ON c.id = s.content_id
    WHERE s.is_dead IS NULL OR s.is_dead = 0
    GROUP BY c.type, s.site_name
    ORDER BY c.type, cnt DESC
""")
print("=== ALIVE SITES PER CONTENT TYPE ===")
for row in cur.fetchall():
    print(f"  {row[0]:10s}  {row[1]:30s}  {row[2]}")

print()

# For each content type, count how many have at least one alive site
cur.execute("""
    SELECT c.type, COUNT(DISTINCT c.id)
    FROM content c
    JOIN site s ON s.content_id = c.id AND (s.is_dead IS NULL OR s.is_dead = 0)
    GROUP BY c.type
    ORDER BY c.type
""")
print("=== CONTENT WITH AT LEAST 1 ALIVE SITE ===")
total_with = 0
total_all = 0
for row in cur.fetchall():
    cur2 = db.cursor()
    cur2.execute("SELECT COUNT(*) FROM content WHERE type=?", (row[0],))
    total = cur2.fetchone()[0]
    print(f"  {row[0]:10s}  {row[1]:3d}/{total} ({100*row[1]//total}%)")
    total_with += row[1]
    total_all += total
print(f"  {'TOTAL':10s}  {total_with}/{total_all} ({100*total_with//total_all}%)")

print()

# Show sample tranimaci site URLs (anime)
print("=== SAMPLE TRANIMACI URLS (anime) ===")
cur.execute("""
    SELECT c.title, s.site_url
    FROM site s
    JOIN content c ON c.id = s.content_id
    WHERE s.site_name = 'tranimaci' AND c.type = 'anime'
    LIMIT 10
""")
for row in cur.fetchall():
    print(f"  {row[0]:40s}  {row[1]}")

print()

# Show sample hdfilmcehennemi URLs (movie)
print("=== SAMPLE HDFILMCEHENNEMI URLS (movie) ===")
cur.execute("""
    SELECT c.title, s.site_url
    FROM site s
    JOIN content c ON c.id = s.content_id
    WHERE s.site_name LIKE 'hdfilmcehennemi%' AND c.type = 'movie'
    LIMIT 10
""")
for row in cur.fetchall():
    print(f"  {row[0]:40s}  {row[1]}")

print()

# Show sample setfilmizle URLs (series)
print("=== SAMPLE SETFILMIZLE URLS (series) ===")
cur.execute("""
    SELECT c.title, s.site_url
    FROM site s
    JOIN content c ON c.id = s.content_id
    WHERE s.site_name LIKE 'setfilmizle%' AND c.type = 'series'
    LIMIT 10
""")
for row in cur.fetchall():
    print(f"  {row[0]:40s}  {row[1]}")

print()

# Show sample monomanga URLs (manga)
print("=== SAMPLE MONOMANGA URLS (manga) ===")
cur.execute("""
    SELECT c.title, s.site_url
    FROM site s
    JOIN content c ON c.id = s.content_id
    WHERE s.site_name LIKE 'monomanga%'
    LIMIT 10
""")
for row in cur.fetchall():
    print(f"  {row[0]:40s}  {row[1]}")

print()

# Show sample mangawow URLs (manhwa)
print("=== SAMPLE MANGAWOW URLS (manhwa) ===")
cur.execute("""
    SELECT c.title, s.site_url
    FROM site s
    JOIN content c ON c.id = s.content_id
    WHERE s.site_name LIKE 'mangawow%'
    LIMIT 10
""")
for row in cur.fetchall():
    print(f"  {row[0]:40s}  {row[1]}")

print()

# Content with NO alive sites
cur.execute("""
    SELECT c.id, c.title, c.type
    FROM content c
    WHERE NOT EXISTS (
        SELECT 1 FROM site s 
        WHERE s.content_id = c.id AND (s.is_dead IS NULL OR s.is_dead = 0)
    )
    ORDER BY c.type, c.title
    LIMIT 20
""")
print("=== CONTENT WITH NO ALIVE SITES (sample) ===")
for row in cur.fetchall():
    print(f"  ID={row[0]:3d}  {row[2]:10s}  {row[1]}")

cur.execute("""
    SELECT COUNT(*)
    FROM content c
    WHERE NOT EXISTS (
        SELECT 1 FROM site s 
        WHERE s.content_id = c.id AND (s.is_dead IS NULL OR s.is_dead = 0)
    )
""")
orphan_count = cur.fetchone()[0]
print(f"\n  Total orphan content: {orphan_count}")

print()

# Show unique site_name values that are still alive
cur.execute("""
    SELECT site_name, COUNT(DISTINCT content_id) as cnt
    FROM site
    WHERE is_dead IS NULL OR is_dead = 0
    GROUP BY site_name
    ORDER BY cnt DESC
""")
print("=== ALIVE SITE NAMES (by content count) ===")
for row in cur.fetchall():
    print(f"  {row[0]:30s}  {row[1]}")

db.close()
