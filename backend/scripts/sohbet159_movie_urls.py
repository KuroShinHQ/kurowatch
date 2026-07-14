"""Analyze movie URL patterns to determine which might still work"""
import sqlite3
db = sqlite3.connect('memory/kurowatch.db')
cur = db.cursor()

# Check .nl URLs - with/without /film/ prefix
cur.execute("""
    SELECT c.id, c.title, s.site_url, s.is_dead
    FROM content c JOIN site s ON s.content_id = c.id
    WHERE c.type = 'movie'
    AND s.site_url LIKE '%hdfilmcehennemi.nl%'
    ORDER BY s.site_url
""")
movies = cur.fetchall()
print(f"Total .nl movie sites: {len(movies)}")

with_film = 0
without_film = 0
for cid, title, url, dead in movies:
    if '/film/' in url:
        with_film += 1
    else:
        without_film += 1

print(f"  With /film/ prefix: {with_film}")
print(f"  Without /film/ prefix: {without_film}")
print(f"  Dead already: {sum(1 for m in movies if m[3] == 1)}")

# Show a few from each category
print("\n=== SAMPLE WITHOUT /film/ ===")
for cid, title, url, dead in movies:
    if '/film/' not in url:
        print(f"  ID={cid} {url}")

print("\n=== SAMPLE WITH /film/ (first 5) ===")
count = 0
for cid, title, url, dead in movies:
    if '/film/' in url:
        print(f"  ID={cid} {url}")
        count += 1
        if count >= 5:
            break

db.close()
