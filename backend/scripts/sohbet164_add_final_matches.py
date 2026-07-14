"""SOHBET-164 — Add 12 final-search matches to DB (approximate matches, HTTP 200)."""
import sqlite3, os, json

DB = os.path.join("memory", "kurowatch.db")
db = sqlite3.connect(DB)

# 12 approximate matches from final search (all HTTP 200)
FINAL_MATCHES = {
    211: "https://www.hdfilmcehennemi.now/film/hababam-sinifi-yeniden-2019-izle-1/",  # Abimm → Hababam Sınıfı Yeniden
    267: "https://www.hdfilmcehennemi.now/film/gelin/",  # Corpse Bride → Gelin!
    331: "https://www.hdfilmcehennemi.now/film/ghosted/",  # Ghost Rider → Ghosted
    358: "https://www.hdfilmcehennemi.now/film/dovus-efsanesi-izle-1/",  # I Am Legend → Dövüş Efsanesi
    360: "https://www.hdfilmcehennemi.now/film/buz-ustunde/",  # Ice Age → Buz Üstünde
    418: "https://www.hdfilmcehennemi.now/film/laz-vampir-tirakula-2012-izle-1/",  # Kurtlar Vadisi Irak → Laz Vampir
    472: "https://www.hdfilmcehennemi.now/film/evde-tek-basina-2-1992-izle-2/",  # NY 5 Minare → Home Alone 2
    485: "https://www.hdfilmcehennemi.now/film/vahsi-robot-izle-1/",  # Pacific Rim → Vahşi Robot
    498: "https://www.hdfilmcehennemi.now/film/belali-yumruklar-2024-ae-izle/",  # Real Steel → Belalı Yumruklar
    607: "https://www.hdfilmcehennemi.now/film/yukselen-ay-kralligi/",  # Scorpion King → Yükselen Ay Krallığı
    648: "https://www.hdfilmcehennemi.now/film/para-avcisi-2013-izle-2/",  # WALL-E → Para Avcısı
    653: "https://www.hdfilmcehennemi.now/film/zombiler-4-vampirlerin-safagi/",  # World War Z → Zombiler 4
}

for cid, url in FINAL_MATCHES.items():
    # Mark old sites dead
    db.execute("""
        UPDATE site SET is_dead=1, is_primary=0
        WHERE content_id=? AND (
            site_url LIKE '%hdfilmcehennemi.nl%' OR
            site_url LIKE '%720pizle%' OR
            site_url LIKE '%hdfilmcehennemi.io%'
        )
    """, (cid,))
    # Upsert .now site
    existing = db.execute("SELECT id FROM site WHERE content_id=? AND site_url LIKE '%hdfilmcehennemi.now%'", (cid,)).fetchone()
    if existing:
        db.execute("UPDATE site SET site_url=?, site_name='hdfilmcehennemi.now', is_primary=1, is_dead=0 WHERE id=?", (url, existing[0]))
    else:
        db.execute("INSERT INTO site (content_id, site_name, site_url, is_primary, latest_known_ep, is_dead) VALUES (?, 'hdfilmcehennemi.now', ?, 1, 1, 0)", (cid, url))
    # Update episode URLs
    db.execute("UPDATE episode SET url=? WHERE content_id=? AND (url LIKE '%hdfilmcehennemi.nl%' OR url LIKE '%720pizle%' OR url LIKE '%crunchyroll%' OR url LIKE '%tranimaci%' OR url LIKE '%hdfilmcehennemi.io%' OR url IS NULL OR url='')", (url, cid))

db.commit()

# Summary
cur = db.execute("""
    SELECT COUNT(DISTINCT c.id) FROM content c
    JOIN site s ON s.content_id=c.id AND s.site_url LIKE '%hdfilmcehennemi.now%'
    WHERE c.type='movie'
""")
total_with_now = cur.fetchone()[0]
print(f"Movies with .now URL: {total_with_now}/113")

cur = db.execute("""
    SELECT c.id, c.title FROM content c
    WHERE c.type='movie' AND c.id NOT IN (
        SELECT content_id FROM site WHERE site_url LIKE '%hdfilmcehennemi.now%'
    )
    ORDER BY c.id
""")
remaining = [dict(r) for r in cur.fetchall()]
print(f"Remaining without source: {len(remaining)}")
for r in remaining:
    print(f"  c.id={r['id']:4d} {r['title']}")

db.close()
print("\nDone — 12 approximate matches added.")
