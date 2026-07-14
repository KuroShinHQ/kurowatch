"""SOHBET-165 — Fix season data: Rick&Morty remove S8+S9 (only 7 seasons real)."""
import sqlite3, os

DB = os.path.join("memory", "kurowatch.db")
db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row

# Rick and Morty (c.id=505) — only 7 seasons real, S8+S9 are fake
print("=== Rick and Morty (505) BEFORE ===")
cur = db.execute("SELECT season, COUNT(*) as cnt FROM episode WHERE content_id=505 GROUP BY season ORDER BY season")
for r in cur.fetchall():
    print(f"  season={r['season']} eps={r['cnt']}")

# Delete S8 and S9 episodes
deleted = db.execute("DELETE FROM episode WHERE content_id=505 AND season IN (8, 9)").rowcount
print(f"\nDeleted {deleted} fake episodes (S8+S9)")

# Update total_episodes
db.execute("UPDATE content SET total_episodes=71 WHERE id=505")  # 11+10+10+10+10+10+10 = 71
# Update season_number to 7 (max real season)
db.execute("UPDATE content SET season_number=7 WHERE id=505")

# Also fix child content (113 Rick&Morty S7) — parent_id=505, season=7
# This is correct, leave as is

print("\n=== Rick and Morty (505) AFTER ===")
cur = db.execute("SELECT season, COUNT(*) as cnt FROM episode WHERE content_id=505 GROUP BY season ORDER BY season")
for r in cur.fetchall():
    print(f"  season={r['season']} eps={r['cnt']}")

cur = db.execute("SELECT id, title, season_number, total_episodes FROM content WHERE id=505")
r = cur.fetchone()
print(f"  Content: season={r['season_number']} total_ep={r['total_episodes']}")

# Dexter (c.id=287) — verify 8 seasons correct
print("\n=== Dexter (287) — verify ===")
cur = db.execute("SELECT season, COUNT(*) as cnt FROM episode WHERE content_id=287 GROUP BY season ORDER BY season")
for r in cur.fetchall():
    print(f"  season={r['season']} eps={r['cnt']}")

# Dexter (287) total_ep should be 96 (8*12)
db.execute("UPDATE content SET total_episodes=96 WHERE id=287")
db.execute("UPDATE content SET season_number=8 WHERE id=287")

# Child Dexter S8 (112) — parent_id=287, season=8, only 3 episodes
# This is fine — it's a "latest season" shortcut
print("\n=== Dexter S8 (112) child ===")
cur = db.execute("SELECT id, title, season_number, total_episodes, parent_id FROM content WHERE id=112")
r = cur.fetchone()
print(f"  c.id={r['id']} season={r['season_number']} total_ep={r['total_episodes']} parent={r['parent_id']}")

# Cult of the Lamb (128) — game, season_number=1 but should be NULL/0
print("\n=== Cult of the Lamb (128) — game fix ===")
cur = db.execute("SELECT id, title, type, season_number, total_episodes FROM content WHERE id=128")
r = cur.fetchone()
print(f"  BEFORE: type={r['type']} season={r['season_number']} total_ep={r['total_episodes']}")

# Game should have season_number=0 (no seasons)
db.execute("UPDATE content SET season_number=0, total_episodes=0 WHERE type='game' AND season_number > 0")

# Verify all games
print("\n=== ALL games season fix ===")
cur = db.execute("SELECT id, title, season_number, total_episodes FROM content WHERE type='game' ORDER BY id")
for r in cur.fetchall():
    print(f"  c.id={r['id']:4d} season={r['season_number'] or 0:3d} total_ep={r['total_episodes'] or 0:4d} {r['title'][:40]}")

# Check for any episodes on games (should be 0)
cur = db.execute("SELECT c.id, c.title, COUNT(e.id) as ep_count FROM content c LEFT JOIN episode e ON e.content_id=c.id WHERE c.type='game' GROUP BY c.id HAVING ep_count > 0")
game_eps = cur.fetchall()
print(f"\nGames with episodes: {len(game_eps)}")
for r in game_eps:
    print(f"  c.id={r['id']:4d} {r['title'][:40]} eps={r['ep_count']}")
    # Delete these episodes
    db.execute("DELETE FROM episode WHERE content_id=?", (r['id'],))

db.commit()
print(f"\n=== DONE — Season fixes applied ===")

# Final verification
print("\n=== FINAL VERIFICATION ===")
cur = db.execute("SELECT id, title, season_number, total_episodes FROM content WHERE id IN (505, 287, 112, 128)")
for r in cur.fetchall():
    print(f"  c.id={r['id']:4d} season={r['season_number'] or 0:3d} total_ep={r['total_episodes'] or 0:4d} {r['title'][:40]}")

db.close()
