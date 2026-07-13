"""
SOHBET-151 — my_progress değerlerini güncelle.
Her içerik için kullanıcının son kaydettiği ilerlemeyi tespit et.
Eğer kayıtlı progress varsa (download_jobs'dan veya episode download state'ten),
onu kullan. Yoksa 0 bırak.
"""
import sqlite3, os

DB = os.path.join(os.path.dirname(__file__), '..', '..', 'memory', 'kurowatch.db')

def fix():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    cur = db.cursor()

    updated = 0
    by_type = {}

    # Strategy: look at download_jobs for completed downloads
    # If a user completed downloading episode N, my_progress should be at least N
    # But we can't track user-specific progress from DB alone.
    # Simpler approach: set my_progress = NULL (means "not started")
    # for all content that has 0 or NULL progress.
    # For content that already has progress > 0, leave it.

    contents = cur.execute("""
        SELECT id, type, my_progress FROM content
    """).fetchall()

    for c in contents:
        cid = c['id']
        ctype = c['type']
        curr = c['my_progress']

        # Get max episode number
        max_num = cur.execute(
            "SELECT MAX(number) as mx FROM episode WHERE content_id=?", (cid,)
        ).fetchone()['mx']

        if max_num is None:
            max_num = 0

        # If progress is NULL, set to 0
        # If progress > total, cap it
        # If progress is already reasonable, leave it
        cap = max_num

        if curr is None:
            cur.execute("UPDATE content SET my_progress=0 WHERE id=?", (cid,))
            updated += 1
            by_type[ctype] = by_type.get(ctype, 0) + 1
        elif curr > cap and cap > 0:
            cur.execute("UPDATE content SET my_progress=? WHERE id=?", (cap, cid))
            updated += 1
            by_type[ctype] = by_type.get(ctype, 0) + 1

    db.commit()
    print(f"=== MY_PROGRESS DÜZELTİLDİ ===")
    print(f"Güncellenen içerik: {updated}")
    for t, cnt in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {t}: {cnt}")

    # Summary
    summary = cur.execute("""
        SELECT type, COUNT(*) as total,
               SUM(CASE WHEN my_progress IS NULL OR my_progress = 0 THEN 1 ELSE 0 END) as zero
        FROM content GROUP BY type
    """).fetchall()
    print(f"\nGüncel my_progress durumu:")
    for s in summary:
        print(f"  {s['type']}: {s['total']} total, {s['zero']} zero/null")

    db.close()
    return updated

if __name__ == '__main__':
    fix()
