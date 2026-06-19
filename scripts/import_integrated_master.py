"""
kurowatch_integrated_master.md → KuroWatch DB import

Sadece [YENİ] ve [GÜNCELLE] etiketli içerikleri işler.
[KORU] → dokunma. [ÇAKIŞMA] → atla (manuel kontrol gerekli).

Çalıştır (WSL veya Windows Python):
  python3 scripts/import_integrated_master.py
  python3 scripts/import_integrated_master.py --dry-run   (sadece parse, API çağrısı yok)
"""

import re
import json
import sys
import os
import time
import urllib.request
import urllib.error

# --- Yol ---
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_PATH = os.path.normpath(
    os.path.join(_SCRIPT_DIR, "..", "..", "kuroshin-downloads",
                 "kurowatch_data_sources", "kurowatch_integrated_master.md")
)
# WSL path fallback
if not os.path.exists(MASTER_PATH):
    MASTER_PATH = "/mnt/c/Kuroshin/kuroshin-downloads/kurowatch_data_sources/kurowatch_integrated_master.md"

API = "http://localhost:8099/api"
DRY_RUN = "--dry-run" in sys.argv
DELAY = 0.05  # saniye, rate-limit önleme


# --- API Helpers ---

def api_get(path):
    req = urllib.request.Request(f"{API}/{path.lstrip('/')}")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def api_post(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{API}/{path.lstrip('/')}",
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def api_patch(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{API}/{path.lstrip('/')}",
        data=data,
        method="PATCH",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


# --- Parse Helpers ---

def clean_title(t):
    """Dedup için normalize et."""
    t = t.lower()
    t = re.sub(r"[\(\[\{\)\]\}]", " ", t)
    t = re.sub(r"[^a-z0-9\s]", "", t)
    return " ".join(t.split())


def parse_rating(rating_str):
    """'8.5/10' → 8.5, '0.0/10' → None, '—' → None"""
    if not rating_str or rating_str in ("—", "0.0/10"):
        return None
    m = re.match(r"(\d+\.?\d*)/10", rating_str.strip())
    if m:
        val = float(m.group(1))
        return val if val > 0 else None
    return None


def parse_progress(progress_str, ctype):
    """
    'B.243' → (243, 'watching')
    'E.5'   → (5, 'watching')
    'Completed' → (0, 'completed')
    'Planning'  → (0, 'planning')
    '—' / ''    → (0, 'planning')
    """
    if not progress_str or progress_str in ("—", "", "None"):
        return 0, "planning"
    s = progress_str.strip()
    if s in ("Completed", "Tamamlandı"):
        return 0, "completed"
    if s in ("Planning", "İzlenecek", "Okunacak"):
        return 0, "planning"
    # B.243 veya E.5
    m = re.search(r"[BbEe]\.(\d+)", s)
    if m:
        n = int(m.group(1))
        status = "watching" if n > 0 else "planning"
        return n, status
    # Sadece sayı
    m = re.search(r"(\d+)", s)
    if m:
        n = int(m.group(1))
        return n, "watching" if n > 0 else "planning"
    return 0, "planning"


def parse_sites(sites_str):
    """'[MangaŞehri](url) · [Site2](url2)' → [{'name':..,'url':..}]"""
    if not sites_str:
        return []
    links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", sites_str)
    return [{"name": n.strip(), "url": u.strip()} for n, u in links if u.strip()]


def parse_master_md(path):
    """
    MD dosyasını parse et.
    Return: list of dicts with keys:
        tag, title, ctype, rating, progress_str, sites, tags_list
    """
    with open(path, encoding="utf-8") as f:
        content = f.read()

    items = []
    current_type = None

    type_map = {
        "MANGA": "manga",
        "ANİME": "anime",
        "OYUN": "game",
        "GAME": "game",
    }

    for line in content.splitlines():
        line = line.strip()

        # Kategori başlığı
        if line.startswith("## "):
            header = line[3:].upper()
            for key, val in type_map.items():
                if key in header:
                    current_type = val
                    break
            continue

        if current_type is None:
            continue

        # Tablo ayırıcısı ve başlık satırı
        if not line.startswith("|") or "|---|" in line or "| Durum |" in line:
            continue

        # Sütunları ayır
        parts = [p.strip() for p in line.split("|")]
        parts = [p for p in parts if p != ""]
        if len(parts) < 5:
            continue

        # Etiket
        tag_match = re.search(r"\[([A-ZÇİŞÜÖĞ]+)\]", parts[0])
        if not tag_match:
            continue
        tag = tag_match.group(1)

        # Başlık
        title_match = re.search(r"\*\*(.*?)\*\*", parts[1])
        if not title_match:
            continue
        title = title_match.group(1).strip()

        rating_str = parts[2].strip() if len(parts) > 2 else "—"
        progress_str = parts[3].strip() if len(parts) > 3 else "—"
        sites_str = parts[4].strip() if len(parts) > 4 else ""

        # Etiketleri çıkar (Etiketler: ... kısmından)
        tags_match = re.search(r"Etiketler:\s*(.*?)(?:\*|$)", sites_str)
        tags_list = []
        if tags_match:
            tags_list = [t.strip() for t in tags_match.group(1).split(",") if t.strip()]

        items.append({
            "tag": tag,
            "title": title,
            "ctype": current_type,
            "rating_str": rating_str,
            "progress_str": progress_str,
            "sites_str": sites_str,
            "tags_list": tags_list,
        })

    return items


# --- Main ---

def main():
    print(f"Master dosyası: {MASTER_PATH}")
    if not os.path.exists(MASTER_PATH):
        print(f"HATA: Dosya bulunamadı: {MASTER_PATH}", file=sys.stderr)
        sys.exit(1)

    if DRY_RUN:
        print("--- DRY RUN MODU (API çağrısı yok) ---\n")

    # 1. Backend erişim kontrolü
    if not DRY_RUN:
        try:
            existing_raw = api_get("content")
            print(f"Backend OK — mevcut içerik: {len(existing_raw)}\n")
        except Exception as e:
            print(f"HATA: Backend'e erişilemiyor ({e})", file=sys.stderr)
            print("Başlatmak için: Kuroshin.bat [10] → [1]", file=sys.stderr)
            sys.exit(1)

        # Mevcut başlıkları normalize et → id map
        existing_map = {}
        for item in existing_raw:
            norm = clean_title(item["title"])
            existing_map[norm] = item
    else:
        existing_raw = []
        existing_map = {}

    # 2. Master listesini parse et
    items = parse_master_md(MASTER_PATH)
    print(f"Parse edilen toplam kayıt: {len(items)}")

    yeni_items = [i for i in items if i["tag"] == "YENİ"]
    guncelle_items = [i for i in items if i["tag"] == "GÜNCELLE"]
    koru_items = [i for i in items if i["tag"] == "KORU"]

    print(f"  [YENİ]: {len(yeni_items)}")
    print(f"  [GÜNCELLE]: {len(guncelle_items)}")
    print(f"  [KORU]: {len(koru_items)} (atlanıyor)")
    print()

    added = 0
    updated = 0
    skipped = 0
    failed = 0

    # 3. [GÜNCELLE] — var olanları güncelle
    print("=== [GÜNCELLE] İşlemleri ===")
    for item in guncelle_items:
        title = item["title"]
        norm = clean_title(title)
        rating = parse_rating(item["rating_str"])
        progress_val, status = parse_progress(item["progress_str"], item["ctype"])
        sites = parse_sites(item["sites_str"])

        existing = existing_map.get(norm)
        if not existing:
            # Fuzzy match dene
            for k, v in existing_map.items():
                if k in norm or norm in k:
                    existing = v
                    break

        if not existing:
            print(f"  ⚠️  [GÜNCELLE] {title}: DB'de bulunamadı → yeni eklenecek")
            # Bulunamazsa yeni olarak ekle
            yeni_items.append(item)
            continue

        cid = existing["id"]
        patch_body = {}
        if rating is not None:
            patch_body["my_score"] = rating
        # Progress sadece yüksekse güncelle
        if progress_val > (existing.get("my_progress") or 0):
            patch_body["my_progress"] = progress_val
            patch_body["status"] = status

        if DRY_RUN:
            print(f"  [DRY] PATCH /content/{cid} {title} → {patch_body}")
        else:
            try:
                if patch_body:
                    api_patch(f"content/{cid}", patch_body)
                # Yeni siteleri ekle
                existing_site_names = {s["site_name"].lower() for s in existing.get("sites", [])}
                for site in sites:
                    if site["name"].lower() not in existing_site_names:
                        api_post(f"content/{cid}/sites", {
                            "site_name": site["name"],
                            "site_url": site["url"],
                            "is_primary": False,
                        })
                print(f"  ✅ {title} (id:{cid}) güncellendi — skor:{rating}")
                updated += 1
                time.sleep(DELAY)
            except Exception as e:
                print(f"  ❌ {title}: {e}", file=sys.stderr)
                failed += 1

    print()

    # 4. [YENİ] — yeni içerikler ekle
    print("=== [YENİ] İşlemleri ===")
    for item in yeni_items:
        title = item["title"]
        norm = clean_title(title)
        ctype = item["ctype"]
        rating = parse_rating(item["rating_str"])
        progress_val, status = parse_progress(item["progress_str"], ctype)
        sites = parse_sites(item["sites_str"])

        # Zaten DB'de var mı?
        if norm in existing_map:
            print(f"  ⏭️  {title}: Zaten mevcut (atlanıyor)")
            skipped += 1
            continue

        create_body = {
            "title": title,
            "type": ctype,
            "status": status,
            "my_progress": progress_val,
        }
        if rating is not None:
            create_body["my_score"] = rating

        if DRY_RUN:
            site_count = len(sites)
            print(f"  [DRY] POST /content {title} ({ctype}) + {site_count} site")
            added += 1
            continue

        try:
            created = api_post("content", create_body)
            cid = created["id"]
            # existing_map'e ekle (tekrar eklemesini önle)
            existing_map[norm] = created

            # Siteleri ekle
            for i, site in enumerate(sites):
                api_post(f"content/{cid}/sites", {
                    "site_name": site["name"],
                    "site_url": site["url"],
                    "is_primary": (i == 0),
                })

            site_info = f"{len(sites)} site" if sites else "site yok"
            print(f"  ✅ [{ctype}] {title} (id:{cid}) — {site_info}, skor:{rating}")
            added += 1
            time.sleep(DELAY)

        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            print(f"  ❌ {title}: HTTP {e.code} — {body[:120]}", file=sys.stderr)
            failed += 1
        except Exception as e:
            print(f"  ❌ {title}: {e}", file=sys.stderr)
            failed += 1

    print()
    print("=" * 55)
    print(f"Tamamlandı!")
    print(f"  Eklendi   : {added}")
    print(f"  Güncellendi: {updated}")
    print(f"  Atlandı   : {skipped}")
    print(f"  Başarısız : {failed}")
    if not DRY_RUN:
        try:
            final = api_get("content")
            print(f"  DB toplam : {len(final)}")
        except Exception:
            pass


if __name__ == "__main__":
    main()
