"""
bulk_add_eslesmeyen.py
ESLESMEYEN.md analizi sonucu bulunan URL'leri DB'ye toplu ekle.

Turkanime: 27 anime + 2 manga site
site_name = turkanime.tv / ragnarscans.net / hayalistic.blog
"""
import sqlite3
from pathlib import Path

DB_PATH = "/mnt/c/Kuroshin/kurowatch/memory/kurowatch.db"
TA_BASE = "https://www.turkanime.tv/video"
RG_BASE = "https://ragnarscans.net/manga"
HY_BASE = "https://hayalistic.blog/manga"

# (content_id, slug, site_name)
TURKANIME_ADDS = [
    (102,  "isekai-shikkaku",                                                           "turkanime.tv"),
    (224,  "saikyou-no-shokugyou-wa-yuusha-demo-kenja-demo-naku-kanteishi-kari-rashii-desu-yo", "turkanime.tv"),
    (237,  "back-street-girls-gokudolls",                                                "turkanime.tv"),
    (336,  "back-street-girls-gokudolls",                                                "turkanime.tv"),
    (238,  "baki",                                                                       "turkanime.tv"),
    (239,  "baki",                                                                       "turkanime.tv"),
    (678,  "baki-dou",                                                                   "turkanime.tv"),
    (271,  "dungeon-ni-deai-wo-motomeru-no-wa-machigatteiru-darou-ka",                  "turkanime.tv"),
    (277,  "mahoutsukai-reimeiki",                                                       "turkanime.tv"),
    (284,  "maou-2099",                                                                  "turkanime.tv"),
    (285,  "kimetsu-no-yaiba",                                                           "turkanime.tv"),
    (302,  "hazurewaku-no",                                                              "turkanime.tv"),
    (303,  "saihate-no-paladin",                                                         "turkanime.tv"),
    (591,  "saihate-no-paladin",                                                         "turkanime.tv"),
    (305,  "noumin-kanren-no-skill-bakka-agetetara-nazeka-tsuyoku-natta",                "turkanime.tv"),
    (308,  "fate-stay-night",                                                            "turkanime.tv"),
    (315,  "sousou-no-frieren",                                                          "turkanime.tv"),
    (318,  "kyuukyoku-shinka-shita-full-dive-rpg-ga-genjitsu-yori-mo-kusoge-dattara",   "turkanime.tv"),
    (387,  "jojo-s-bizarre-adventure-2012",                                              "turkanime.tv"),
    (406,  "kiseijuu-sei-no-kakuritsu",                                                  "turkanime.tv"),
    (450,  "mo-dao-zu-shi",                                                              "turkanime.tv"),
    (464,  "isekai-mokushiroku-mynoghra-hametsu-no-bunmei-de-hajimeru-sekai-seifuku",   "turkanime.tv"),
    (480,  "yahari-ore-no-seishun-love-come-wa-machigatteiru",                          "turkanime.tv"),
    (521,  "sekai-saikou-no-ansatsusha-isekai-kizoku-ni-tensei-suru",                   "turkanime.tv"),
    (525,  "sentouin-hakenshimasu",                                                      "turkanime.tv"),
    (551,  "ore-dake-level-up-na-ken",                                                   "turkanime.tv"),
    (566,  "tales-of-zestiria-the-x",                                                   "turkanime.tv"),
    (588,  "kage-no-jitsuryokusha-ni-naritakute",                                       "turkanime.tv"),
    (638,  "isekai-ojisan",                                                              "turkanime.tv"),
    (669,  "youkoso-jitsuryoku-shijou-shugi-no-kyoushitsu-e-tv",                        "turkanime.tv"),
]

# Manga — sadece Türkçe isim tam eşleşen, kesin doğrular
MANGA_ADDS = [
    # (content_id, url, site_name)
    (4,   "https://ragnarscans.net/manga/buyu-imparatoru/",   "ragnarscans.net"),
    (4,   "https://hayalistic.blog/manga/buyu-imparatoru/",   "hayalistic.blog"),
    (23,  "https://ragnarscans.net/manga/seckinin-ikinci-yasami/", "ragnarscans.net"),
    (23,  "https://hayalistic.blog/manga/seckinin-ikinci-yasami/", "hayalistic.blog"),
    (64,  "https://ragnarscans.net/manga/regressor-instruction-manual/", "ragnarscans.net"),
    (83,  "https://ragnarscans.net/manga/a-dragonslayers-peerless-regression/", "ragnarscans.net"),
]

def add_site(conn, content_id: int, url: str, site_name: str):
    exists = conn.execute(
        "SELECT 1 FROM site WHERE content_id=? AND site_url=?", (content_id, url)
    ).fetchone()
    if exists:
        return "SKIP"
    # content var mı?
    title = conn.execute("SELECT title FROM content WHERE id=?", (content_id,)).fetchone()
    if not title:
        return "NO_CONTENT"
    conn.execute(
        "INSERT INTO site (content_id, site_name, site_url, is_primary, is_dead) VALUES (?,?,?,0,0)",
        (content_id, site_name, url),
    )
    return f"OK: {title[0]}"

def main():
    conn = sqlite3.connect(DB_PATH)
    added = skipped = errors = 0

    print("=== TURKANIME EKLEMELER ===")
    for content_id, slug, site_name in TURKANIME_ADDS:
        url = f"{TA_BASE}/{slug}-1-bolum"
        result = add_site(conn, content_id, url, site_name)
        if result.startswith("OK"):
            added += 1
            print(f"  + [{content_id}] {result} → {slug}")
        elif result == "SKIP":
            skipped += 1
            print(f"  ~ [{content_id}] SKIP (zaten var)")
        else:
            errors += 1
            print(f"  ! [{content_id}] {result}")

    print()
    print("=== MANGA EKLEMELER ===")
    for content_id, url, site_name in MANGA_ADDS:
        result = add_site(conn, content_id, url, site_name)
        if result.startswith("OK"):
            added += 1
            print(f"  + [{content_id}] {result} → {site_name}")
        elif result == "SKIP":
            skipped += 1
            print(f"  ~ [{content_id}] SKIP (zaten var)")
        else:
            errors += 1
            print(f"  ! [{content_id}] {result}")

    conn.commit()
    conn.close()
    print()
    print(f"TOPLAM: +{added} eklendi | {skipped} atlandı | {errors} hata")

if __name__ == "__main__":
    main()
