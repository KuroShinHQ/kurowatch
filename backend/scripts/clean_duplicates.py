"""
SOHBET-151 — Tüm medya türlerinde duplicate episode/chapter kayıtlarını temizle.
Her (content_id, season, number) grubundan sadece 1 kayıt bırak, en eski (min id) olanı koru.
Eğer bir kaydın url'i varsa onu tercih et.
"""
import sqlite3
import os

DB = os.path.join(os.path.dirname(__file__), '..', '..', 'memory', 'kurowatch.db')

def clean():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    cur = db.cursor()

    # Find all duplicate groups
    dupes = cur.execute("""
        SELECT content_id, season, number, COUNT(*) as cnt,
               GROUP_CONCAT(id ORDER BY id) as ids
        FROM episode
        GROUP BY content_id, season, number
        HAVING cnt > 1
    """).fetchall()

    total_deleted = 0
    total_groups = len(dupes)
    by_type = {}

    for d in dupes:
        cid = d['content_id']
        ids = [int(x) for x in d['ids'].split(',')]

        # Find which ones have URLs - prefer keeping one with URL
        rows = cur.execute(
            "SELECT id, url FROM episode WHERE id IN ({})".format(','.join('?' * len(ids))),
            ids
        ).fetchall()

        # Strategy: keep row with non-null URL if exists, else keep lowest id
        with_url = [r for r in rows if r['url']]
        keep_id = with_url[0]['id'] if with_url else min(ids)

        delete_ids = [x for x in ids if x != keep_id]

        # Delete extras
        for did in delete_ids:
            cur.execute("DELETE FROM episode WHERE id=?", (did,))

        total_deleted += len(delete_ids)

        # Track by type
        t = cur.execute("SELECT type FROM content WHERE id=?", (cid,)).fetchone()
        if t:
            by_type[t['type']] = by_type.get(t['type'], 0) + len(delete_ids)

    db.commit()

    print(f"=== DUPLICATE EPISODE TEMİZLİĞİ ===")
    print(f"İncelenen grup: {total_groups}")
    print(f"Silinen kayıt: {total_deleted}")
    print(f"Kalan kayıt: {total_deleted} (1'er tane bırakıldı)")
    print(f"\nTür bazında silinen:")
    for t, cnt in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {t}: {cnt}")

    # Verify
    remaining = cur.execute("""
        SELECT COUNT(*) as cnt FROM (
            SELECT content_id, season, number, COUNT(*) as cnt
            FROM episode GROUP BY content_id, season, number HAVING cnt > 1
        )
    """).fetchone()['cnt']
    print(f"\nKalan duplicate grup: {remaining}")
    if remaining == 0:
        print("✅ TÜM DUPLICATE'LER TEMİZLENDİ")
    else:
        print(f"⚠️ {remaining} grup kaldı (yabancı anahtar engeli olabilir)")

    db.close()
    return total_deleted

if __name__ == '__main__':
    clean()
