import sqlite3, re
from urllib.parse import urlparse

conn = sqlite3.connect('/mnt/c/Kuroshin/kurowatch/memory/kurowatch.db')

# İçerik tiplerine göre site domain'lerini say
rows = conn.execute(
    "SELECT c.type, s.site_url FROM site s JOIN content c ON c.id = s.content_id WHERE s.site_url IS NOT NULL"
).fetchall()

from collections import defaultdict, Counter
by_type = defaultdict(list)
for ctype, url in rows:
    try:
        domain = urlparse(url).netloc.lstrip('www.')
        by_type[ctype].append(domain)
    except:
        pass

for ctype in sorted(by_type):
    counts = Counter(by_type[ctype])
    print(f"\n=== {ctype.upper()} ({len(counts)} farklı domain) ===")
    for domain, n in counts.most_common():
        print(f"  {n:3d} içerik  {domain}")

conn.close()
