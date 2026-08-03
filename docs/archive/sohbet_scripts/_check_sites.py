import httpx
import re

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# mangatr.app URL yapısı
r = httpx.get('https://mangatr.app/', headers=headers, follow_redirects=True, timeout=15)
links = re.findall(r'href=["\'](https?://mangatr\.app[^"\']+)', r.text)
print('=== mangatr.app links ===')
for l in links[:15]:
    print(f'  {l}')

# setfilmizle.uk
r2 = httpx.get('https://www.setfilmizle.uk/', headers=headers, follow_redirects=True, timeout=15)
links2 = re.findall(r'href=["\']([^"\']+)', r2.text)
print()
print('=== setfilmizle.uk dizi/bolum links ===')
for l in links2:
    if 'setfilmizle' in l and ('/dizi/' in l.lower() or '/bolum' in l.lower() or 'sezon' in l.lower()):
        print(f'  {l}')

# hdfilmcehennemi.now film URL yapısı
print()
print('=== hdfilmcehennemi.now film URL pattern ===')
r3 = httpx.get('https://www.hdfilmcehennemi.now/', headers=headers, follow_redirects=True, timeout=15)
links3 = re.findall(r'href=["\']([^"\']+)', r3.text)
for l in links3:
    if 'hdfilmcehennemi.now' in l and ('/film/' in l.lower()):
        print(f'  {l}')
        break
for l in links3:
    if 'hdfilmcehennemi.now' in l and ('/dizi/' in l.lower()):
        print(f'  {l}')
        break
