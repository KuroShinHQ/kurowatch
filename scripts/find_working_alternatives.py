"""
For each failed item, check ALL existing site records for working alternatives.
Test each alternative site URL to see if it resolves.
"""
import asyncio, sys, os, time, re, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from backend.tools.url_ping import http_ping

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory", "kurowatch.db")
import sqlite3

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# Get all failed items from the previous test
failed_items = [
    (679, 'anime', '5 Centimeters per Second'),
    (3, 'manga', 'Above All Gods'),
    (6, 'manga', 'Jujutsu Kaisen'),
    (7, 'manga', 'Release That Witch'),
    (14, 'manga', 'Solo Leveling'),
    (15, 'manga', "The Scholar's Reincarnation"),
    (13, 'manga', "Dünyanın En İyi Mühendisi"),
    (17, 'manga', 'The Tutorial Tower of the Advanced Player'),
    (11, 'manga', "Bilge Okuyucunun Bakış Açısı"),
    (12, 'manga', 'Above Ten Thousand People'),
    (16, 'manga', 'The Beginning After the End'),
    (21, 'manga', "World's Apocalypse Online"),
    (22, 'manga', 'Juujika no Rokunin'),
    (31, 'manga', 'Kill the Hero'),
    (27, 'manga', "Kılıç Kralının Fantezi Dünyasında Hayatta Kalma Hikayesi"),
    (32, 'manga', 'The Max Level Hero Has Returned'),
    (26, 'manga', 'Deli Mühendis'),
    (34, 'manga', 'Top Tier Providence'),
    (36, 'manga', 'Player Who Returned 10,000 Years Later'),
    (38, 'manga', "Soylu Ailenin İşe Yaramaz Oğlu"),
    (39, 'manga', 'Back to Rule Again'),
    (41, 'manga', 'Strongest Fighter'),
    (51, 'manga', 'I Reincarnated as the Crazed Heir'),
    (43, 'manga', 'Şamanın Yolu'),
    (54, 'manga', 'I Just Want to Be Killed'),
    (45, 'manga', "Kılıç Hanesinin Genç Efendisi"),
    (29, 'manga', 'Tower Into the Clouds'),
    (33, 'manga', 'Rise from the Rubble'),
    (58, 'manga', 'The World After the End'),
    (59, 'manga', "Mağdur Sıralamacının Dönüşü"),
    (60, 'manga', 'Kahraman Döndü'),
    (37, 'manga', 'I Am the Fated Villain'),
    (65, 'manga', 'O Gerçekten Bir Kahraman mı?'),
    (66, 'manga', 'The Dungeon Master'),
    (61, 'manga', 'Return of the Shattered Constellation'),
    (68, 'manga', 'Sokakta Hayatta Kalma Kılavuzu'),
    (69, 'manga', 'Overpowered Sword'),
    (35, 'manga', 'Kaderin Zirvesi'),
    (81, 'manga', 'I Can Snatch 999 Types of Abilities'),
    (85, 'manga', 'Şeytani Egemenin Halefi'),
    (71, 'manga', 'Damn Reincarnation'),
    (76, 'manga', 'Kage no Jitsuryokusha ni Naritakute'),
    (72, 'manga', 'Fukushuu o Koinegau Saikyou Yuusha'),
    (82, 'manga', 'Tanrıçanın Kulu'),
    (93, 'manga', "Forced to Become the Villain's Son-in-Law"),
    (84, 'manga', "Library of Heaven's Path"),
    (90, 'manga', 'Sémalarin Kilici'),
    (78, 'manga', 'Im Not That Kind of Talent'),
    (88, 'manga', 'Yıldırım Bıçağı Ustası'),
    (30, 'manhwa', 'Return to Player'),
    (40, 'manhwa', 'Bug Player'),
    (28, 'manhwa', 'Return of the Unrivaled Spear Knight'),
    (47, 'manhwa', 'Return of the Mount Hua Sect'),
    (50, 'manhwa', 'Heavenly Demon Instructor'),
    (57, 'manhwa', 'SSS-Class Suicide Hunter'),
    (63, 'manhwa', 'Seoul Station Necromancer'),
    (46, "manhwa", "Ranker's Return (Remake)"),
    (48, 'manhwa', "The Heavenly Demon Can't Live a Normal Life"),
    (79, 'manhwa', 'Villain Unrivaled'),
    (53, 'manhwa', 'Memorize'),
    (49, 'manhwa', 'Reverse Villain'),
    (83, 'manhwa', 'Regressing with the King\'s Power'),
    (52, 'manhwa', "Reincarnation of the Murim Clan's Former Ranker"),
    (73, 'manhwa', 'Revenge of the Iron-Blooded Sword Hound'),
    (80, 'manhwa', 'Never Die Extra'),
    (87, 'manhwa', 'Raising Newbie Heroes in Another World'),
    (75, 'manhwa', 'I Became the Tyrant of a Defense Game'),
    (86, 'manhwa', 'My Insanely Competent Underlings'),
]

WORKING_DOMAINS = [
    'mangatr.net',      # 77/77 confirmed working
    'turkmanga.net',     # 4/4 confirmed working 
    'mangadenizi.com',   # was 301, likely working
    'mangawow.com',      # was 301, likely working
    'merlintoon.com',    # 200 confirmed
]

def slugify(title):
    s = title.lower().strip()
    tr_map = str.maketrans("şçğğıöüıŞÇĞĞİÖÜİ", "scggioiuSCGGIOUI")
    s = s.translate(tr_map)
    s = re.sub(r"[^a-z0-9\- ]", "", s)
    s = re.sub(r"\s+", "-", s).strip("-")
    s = re.sub(r"-+", "-", s)
    return s

def extract_slug_from_url(url):
    """Extract slug from URL like mangaokutr.com/slug-bolum-N/ or mangatr.net/manga/slug/bolum-N/"""
    if not url:
        return None
    # mangatr.net/manga/slug/bolum-N/ → slug
    m = re.search(r'/manga/([^/]+)', url)
    if m:
        return m.group(1)
    # mangaokutr.com/slug-bolum-N/ → slug
    m = re.search(r'\.com?/([^/]+)-bolum', url)
    if m:
        return m.group(1)
    # hayalistic.com.tr/manga/slug/ → slug
    m = re.search(r'/manga/([^/]+)', url)
    if m:
        return m.group(1)
    return None

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

print(f"Checking {len(failed_items)} failed items for working alternatives...\n")

async def main():
    for cid, ctype, title in failed_items:
        # Get the current episode 1 URL
        ep1 = conn.execute("SELECT url FROM episode WHERE content_id=? AND number=1 AND season=1", (cid,)).fetchone()
        old_url = ep1['url'] if ep1 else None
        
        # Get all site records for this item
        sites = conn.execute("SELECT id, site_name, site_url, is_primary FROM site WHERE content_id=?", (cid,)).fetchall()
        
        print(f"\n#{cid} [{ctype}] {title[:50]}")
        if old_url:
            print(f"  Current ep1 URL: {old_url[:100]}")
        
        print(f"  Site records ({len(sites)}):")
        for s in sites:
            mark = "⭐" if s['is_primary'] else " "
            print(f"    {mark} {s['site_name']}: {s['site_url'][:90]}")
        
        # Test existing alternative sites
        working_alt = None
        for s in sites:
            if is_working_domain(s['site_url']):
                result = await http_ping(s['site_url'], timeout=8.0)
                if result.is_ok():
                    working_alt = s
                    print(f"  ✅ WORKS: {s['site_name']} ({result.status})")
                    break
                else:
                    print(f"  ❌ {s['site_name']}: {result.status}")
        
        if not working_alt:
            print(f"  ⚠ No working alternative found in existing sites")
            
print(f"\nDone.")

asyncio.run(main())
conn.close()
