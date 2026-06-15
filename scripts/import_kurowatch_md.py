"""KuroWatch_Listesi.md → KuroWatch DB import.
Kullanım: cd /mnt/c/Kuroshin/kurowatch && python3 scripts/import_kurowatch_md.py
"""
import re
import json
import sys
import os
import urllib.request

MD_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "kuroshin-downloads", "KuroWatch_Listesi.md")
API = "http://localhost:8099/api"


def api_post(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{API}/{path.lstrip('/')}",
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


_RESET = "_RESET_"


def get_section_info(header):
    """### başlığından (type, status) döndür. _RESET → current_section sıfırla. None → değiştirme."""
    h = header.upper()
    if "İSTATİSTİK" in h:
        return _RESET
    if "CAPTCHA" in h:
        return ("anime", "on_hold")
    if "BATI DİZİLERİ" in h:
        return ("anime", "watching")
    if "ZİRVE TAKİBİ" in h or "YÜKSEK SEVİYE" in h or "ORTA SEVİYE" in h:
        return ("manga", "watching")
    if "YENİ BAŞLADIM" in h:
        return ("manga", "planning")
    if "ANİME" in h:
        return ("anime", "watching")
    if "OYUN" in h:
        return ("game", "planning")
    return None


def parse_progress(cell):
    m = re.search(r"[BE]\.(\d+)", cell)
    return int(m.group(1)) if m else 0


def main():
    if not os.path.exists(MD_PATH):
        print(f"HATA: MD dosyası bulunamadı: {MD_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(MD_PATH, encoding="utf-8") as f:
        lines = f.readlines()

    current_section = None
    imported = 0
    failed = 0

    for line in lines:
        stripped = line.strip()

        # Bölüm başlığı (## veya ###)
        if stripped.startswith("#"):
            info = get_section_info(stripped)
            if info == _RESET:
                current_section = None
            elif info:
                current_section = info
            continue

        if current_section is None:
            continue

        # Sadece tablo satırları
        if not stripped.startswith("|"):
            continue

        # Başlık ve ayırıcı satırları atla
        if "|---|" in stripped or "| Başlık" in stripped or "| Oyun" in stripped:
            continue

        cols = [c.strip() for c in stripped.split("|")]
        cols = [c for c in cols if c != ""]

        if not cols:
            continue

        # Başlık
        title_m = re.search(r"\*\*(.*?)\*\*", cols[0])
        if not title_m:
            continue
        title = title_m.group(1).strip()

        ctype, status = current_section

        # İlerleme
        progress = 0
        if len(cols) >= 2:
            progress = parse_progress(cols[1])

        # Siteler (oyunlarda yok)
        sites = []
        if ctype != "game" and len(cols) >= 3:
            sites = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", cols[2])

        # İçeriği oluştur
        try:
            content = api_post("content", {
                "title": title,
                "type": ctype,
                "status": status,
                "my_progress": progress,
            })
            cid = content["id"]
        except Exception as e:
            print(f"  ❌ [{ctype}] {title}: {e}", file=sys.stderr)
            failed += 1
            continue

        # Siteleri ekle
        for i, (site_name, site_url) in enumerate(sites):
            try:
                api_post(f"content/{cid}/sites", {
                    "site_name": site_name,
                    "site_url": site_url,
                    "is_primary": i == 0,
                })
            except Exception as e:
                print(f"    ⚠️  Site ({site_name}): {e}", file=sys.stderr)

        site_info = f"{len(sites)} site" if sites else "site yok"
        print(f"  ✅ [{ctype}] {title} (B/E.{progress}) — {site_info}")
        imported += 1

    print(f"\n{'=' * 50}")
    print(f"Tamamlandı: {imported} içerik, {failed} başarısız.")


if __name__ == "__main__":
    main()
