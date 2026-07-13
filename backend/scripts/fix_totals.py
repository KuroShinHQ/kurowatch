"""
SOHBET-151 — Tüm içeriklerde total_episodes/total_chapters değerlerini
episode tablosundaki MAX(number)'a göre güncelle.
"""
import sqlite3, os

DB = os.path.join(os.path.dirname(__file__), '..', '..', 'memory', 'kurowatch.db')

def fix():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    cur = db.cursor()

    updated = 0
    by_type = {}

    contents = cur.execute("""
        SELECT c.id, c.type, c.total_episodes, c.total_chapters
        FROM content c
    """).fetchall()

    for c in contents:
        cid = c['id']
        ctype = c['type']
        max_num = cur.execute(
            "SELECT MAX(number) as mx FROM episode WHERE content_id=?", (cid,)
        ).fetchone()['mx']

        if max_num is None:
            continue

        if ctype in ('manga', 'manhwa'):
            if c['total_chapters'] != max_num:
                cur.execute("UPDATE content SET total_chapters=? WHERE id=?", (max_num, cid))
                updated += 1
                by_type[ctype] = by_type.get(ctype, 0) + 1
        else:
            if c['total_episodes'] != max_num:
                cur.execute("UPDATE content SET total_episodes=? WHERE id=?", (max_num, cid))
                updated += 1
                by_type[ctype] = by_type.get(ctype, 0) + 1

    db.commit()
    print(f"=== TOTAL_EPISODES/CHAPTERS DÜZELTİLDİ ===")
    print(f"Güncellenen içerik: {updated}")
    for t, cnt in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {t}: {cnt}")

    # Verify remaining NULLs
    nulls = cur.execute("""
        SELECT type, COUNT(*) FROM content 
        WHERE (type IN ('manga','manhwa') AND total_chapters IS NULL)
           OR (type NOT IN ('manga','manhwa') AND total_episodes IS NULL)
        GROUP BY type
    """).fetchall()
    if nulls:
        print(f"\nKalan NULL değerler (episode kaydı olmayan içerikler):")
        for n in nulls:
            print(f"  {n['type']}: {n['COUNT(*)']}")

    db.close()
    return updated

if __name__ == '__main__':
    fix()
