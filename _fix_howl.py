import sqlite3
db = sqlite3.connect('memory/kurowatch.db')
cur = db.cursor()

# Fix Howl's Moving Castle site URL
cur.execute("""
    UPDATE site SET site_url = 'https://www.hdfilmcehennemi.nl/howl-s-moving-castle/'
    WHERE content_id IN (SELECT id FROM content WHERE title LIKE '%Howl%Moving%Castle%')
    AND site_url LIKE '%hdfilmcehennemi%'
""")
print(f'Howl site updated: {cur.rowcount}')
db.commit()

# Fix the episode URL too (ensure it uses www.)
cur.execute("""
    UPDATE episode SET url = 'https://www.hdfilmcehennemi.nl/howl-s-moving-castle/'
    WHERE content_id IN (SELECT id FROM content WHERE title LIKE '%Howl%Moving%Castle%')
    AND url LIKE '%hdfilmcehennemi%'
""")
print(f'Howl episode updated: {cur.rowcount}')
db.commit()

# Also WALL-E site URL
cur.execute("""
    UPDATE site SET site_url = 'https://www.hdfilmcehennemi.nl/wall-e/'
    WHERE content_id IN (SELECT id FROM content WHERE title = 'WALL-E')
    AND site_url LIKE '%hdfilmcehennemi%'
""")
print(f'WALL-E site updated: {cur.rowcount}')
db.commit()

db.close()
