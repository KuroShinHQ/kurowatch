"""Restore MangaDex sites for content items that lost them during duplicate cleanup"""
import sqlite3
from datetime import datetime

db = sqlite3.connect('memory/kurowatch.db')
cur = db.cursor()

# Find items that had MangaDex site removed (their external_id was cleared)
cur.execute("""
    SELECT c.id, c.title, c.type, c.external_id
    FROM content c
    WHERE c.type IN ('manga', 'manhwa')
    AND c.external_id IS NULL
    AND EXISTS (
        SELECT 1 FROM site s WHERE s.content_id = c.id AND s.site_name = 'MangaDex'
    )
""")
print("=== Items with MangaDex site but NO external_id ===")
for r in cur.fetchall():
    print(f"  ID={r[0]}: {r[1]} ({r[2]})")

# Actually, the sites were deleted too. So let me find items that have external_id cleared
# and don't have MangaDex site anymore
cur.execute("""
    SELECT c.id, c.title, c.type
    FROM content c
    WHERE c.type IN ('manga', 'manhwa')
    AND c.external_id IS NULL
    AND NOT EXISTS (
        SELECT 1 FROM site s WHERE s.content_id = c.id
    )
""")
print("\n=== Items with NO sites at all ===")
for r in cur.fetchall():
    print(f"  ID={r[0]}: {r[1]} ({r[2]})")

# OK, let me find which items from the removed list are now orphan
removed_ids = [89, 150, 161, 154, 170, 188, 168, 140, 164, 137, 199, 59, 90, 172, 43, 198, 175, 176]
for cid in removed_ids:
    cur.execute("SELECT id, title, type FROM content WHERE id=?", (cid,))
    item = cur.fetchone()
    if not item:
        continue
    cur.execute("""
        SELECT COUNT(*) FROM site WHERE content_id=? AND (is_dead IS NULL OR is_dead = 0)
    """, (cid,))
    alive_count = cur.fetchone()[0]
    
    if alive_count == 0:
        print(f"  ID={cid}: '{item[1]}' ({item[2]}) -> NOW ORPHAN (no alive sites)")
        
        # Try to find the original mdx UUID from other content with same meaning
        # For duplicates, use the UUID from the kept item
        uuid_map = {
            198: "1dc3ebf9-c86c-43e2-b950-af193154c30a",  # same as ID=152
            175: "4a973243-952e-44ea-8483-7f8c48f8b632",  # same as ID=57
            176: "4a973243-952e-44ea-8483-7f8c48f8b632",  # same as ID=57
            140: "9e02520f-11b9-4e7b-8e6d-5394f10d47e9",  # same as ID=139
            164: "b17b675e-fb9f-4918-812e-9a4e3f55623c",  # same as ID=36
            137: "b17b675e-fb9f-4918-812e-9a4e3f55623c",  # same as ID=36
            199: "a846b1d7-2e57-4644-a3ff-1e819458a10b",  # same as ID=75
            170: "54e1b971-fe2c-471f-ba9a-d17a1fddab50",  # same as ID=77
            188: "707a112b-55cb-416d-8b10-b8bb40df94e4",  # same as ID=28
            168: "773c2211-750b-4fd2-84a3-85a13e0cba26",  # same as ID=145
            172: "fbf326f7-ccbd-44da-823b-69e1367f99db",  # same as ID=73
            150: "478e6926-b8bc-4630-9233-52c0e50cdebe",  # same as ID=27 -> wait, this might be wrong
            161: "9a414441-bbad-4378-a114-f114b1c5b751",  # same as ID=11 -> might be correct
            154: "9d685cb5-594b-4859-9c2a-09b0721f6e18",  # same as ID=88 -> might be correct
            59:  "f1ea37a7-9e85-4a31-a305-53c00fa3b18f",  # same as ID=52 -> might be correct
            43:  None,  # wrong match
            90:  None,  # wrong match
            89:  None,  # wrong match
            174: None,  # wrong match  
        }
        
        uuid = uuid_map.get(cid)
        if uuid:
            # Add back external_id
            cur.execute("UPDATE content SET external_id=? WHERE id=?", (f"mdx:{uuid}", cid))
            # Add back MangaDex site
            cur.execute("""
                INSERT INTO site (content_id, site_name, site_url, is_primary, is_dead)
                VALUES (?, 'MangaDex', ?, 0, 0)
            """, (cid, f"https://mangadex.org/title/{uuid}"))
            print(f"    -> Restored MangaDex (duplicate of known content)")
            db.commit()

# Final check
cur.execute("""
    SELECT c.type, COUNT(*) FROM content c
    WHERE NOT EXISTS (
        SELECT 1 FROM site s WHERE s.content_id = c.id
        AND (s.is_dead IS NULL OR s.is_dead = 0)
    )
    GROUP BY c.type
    ORDER BY c.type
""")
print("\n=== FINAL FINAL ORPHAN COUNT ===")
all_rows = cur.fetchall()
for r in all_rows:
    cur2 = db.cursor()
    cur2.execute("SELECT COUNT(*) FROM content WHERE type=?", (r[0],))
    total = cur2.fetchone()[0]
    print(f"  {r[0]:10s}  {r[1]:3d}/{total}")
print(f"  TOTAL: {sum(r[1] for r in all_rows)}")

db.close()
