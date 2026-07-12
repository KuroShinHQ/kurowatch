"""Update Naruto ep1 URL from tranimaci to animexe"""
import sqlite3
conn = sqlite3.connect("memory/kurowatch.db")
c = conn.cursor()

# Check current value
c.execute("SELECT id, number, url FROM episode WHERE content_id=469 AND number=1")
row = c.fetchone()
print(f"Before: id={row[0]} num={row[1]} url={row[2]}")

# Update
new_url = "https://animexe.com/watch/naruto/1/1"
c.execute("UPDATE episode SET url=? WHERE content_id=469 AND number=1", (new_url,))
conn.commit()

# Verify
c.execute("SELECT id, number, url FROM episode WHERE content_id=469 AND number=1")
row = c.fetchone()
print(f"After:  id={row[0]} num={row[1]} url={row[2]}")

conn.close()
