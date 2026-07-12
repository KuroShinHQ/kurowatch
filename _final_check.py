"""
Final check: current state of hdfilmcehennemi URLs in DB
"""
import sqlite3

db = sqlite3.connect('memory/kurowatch.db')
cur = db.cursor()

cur.execute("""
    SELECT 
        CASE 
            WHEN e.url LIKE '%.nl/%' THEN '.nl'
            WHEN e.url LIKE '%/film/%' THEN '/film/ (now)'
            WHEN e.url LIKE '%hdfilmcehennemi%' THEN 'OLD SLUG'
        END as category,
        COUNT(DISTINCT e.content_id) as content_count,
        COUNT(*) as episode_count
    FROM episode e
    WHERE e.url LIKE '%hdfilmcehennemi%'
    GROUP BY category
    ORDER BY category
""")

total_content = 0
total_episodes = 0
for cat, ccnt, ecnt in cur.fetchall():
    total_content += ccnt
    total_episodes += ecnt
    print(f"  {cat:20s}: {ccnt:2d} content, {ecnt:3d} episodes")

# Also show detailed status
cur.execute("""
    SELECT e.url, c.title, c.id
    FROM episode e
    JOIN content c ON c.id = e.content_id
    WHERE e.url LIKE '%hdfilmcehennemi%'
    GROUP BY c.id
    ORDER BY c.title
""")
print(f"\n{'Content':<45} {'URL Status':<20}")
print('-'*65)
for url, title, cid in cur.fetchall():
    if '/film/' in url:
        status = '/film/ OK'
    elif '.nl/' in url:
        status = '.nl OK'
    else:
        status = 'OLD SLUG 🔴'
    print(f"  {title[:42]:42s} {status}")

print(f"\nTotal: {total_content} contents, {total_episodes} episodes")
db.close()
