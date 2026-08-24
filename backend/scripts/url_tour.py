"""URL KEŞİF TURU (DEVAM-430 spec): ⚠C şüpheli kayıtlar için web araması → bağlam doğrulama → site upsert.

Akış: DDG arama ("<baslik> izle") → whitelist domain filtre → sayfa başlığı çek
→ normalize benzerlik (≥0.8 PASS, 0.6-0.8 ⚠kontrol, <0.6 red) → --apply ile
POST /api/content/{id}/sites (primary) + eski yanlış primary PATCH mark-dead.
Kanıt: logs/url_tour.log + logs/url_tour_state.json.
"""
import argparse
import difflib
import json
import logging
import os
import re
import sys
import time
import unicodedata
import urllib.parse
from pathlib import Path

import requests

try:
    from curl_cffi import requests as cr
except ImportError:
    cr = None

ROOT = Path(__file__).resolve().parents[2]
LISTE = ROOT / "docs" / "MEDIA_LISTE.md"
LOGF = ROOT / "logs" / "url_tour.log"
STATE = ROOT / "logs" / "url_tour_state.json"
API = os.environ.get("KW_API", "http://localhost:8099")

ANIME_DOMAINS = {
    "tranimaci.com", "tranimeizle.co", "tranimeizle.xyz", "turkanime.tv",
    "turkanime.co", "turkanime.com.tr", "anizm.net", "animexe.com",
}
FILM_DOMAINS = {
    "dizibox.so", "dizibox.live", "hdfilmcehennemi.name", "hdfilmcehennemi.nl",
    "hdfilmcehennemi.art", "hdfilmcehennemi.tv", "hdfilmcehennemi.com",
    "hdfilmcehennemi.gg", "hdfilmcehennemi.ws", "dizigom.info", "dizigom.com",
    "dizigom.vip", "dizigom.net", "dizigom.tv", "sezonlukdizi.net",
    "sezonlukdizi.com", "fullhdfilmizlesene.de", "fullhdfilmizlesene.com",
    "fullhdfilmizlesene.pro",
}
ALL_DOMAINS = ANIME_DOMAINS | FILM_DOMAINS
BRAND = {}
for d in ALL_DOMAINS:
    BRAND[d] = d.split(".")[0]

ANIME_TYPES = {"anime", "manga", "manhwa"}
ALIAS = {
    "house m d": ["doktor house"],
    "cars": ["arabalar"],
    "i am legend ben efsaneyim": ["ben efsaneyim", "i am legend"],
    "dawn of the witch": ["mahoutsukai reimeiki"],
    "demon slayer": ["kimetsu no yaiba"],
    "chihiro gidisi": ["ruhlarin kacisi", "spirited away"],
    "cem yilmaz fundamentals": ["cm101mmxi fundamentals"],
    "ghost rider hayalet surucu": ["hayalet surucu", "ghost rider"],
    "hababam sinifi yeni nesil": ["hababam sinifi yeniden"],
    "matrix serisi": ["the matrix"],
    "the godfather": ["godfather baba", "baba serisi"],
    "3 idiots": ["3 ahmak"],
    "aladdin cizgi dizi": ["aladdin turkce izle"],
    "fight club": ["dovus kulubu"],
    "joker 2019": ["joker izle"],
    "shrek": ["srek"],
    "toy story": ["oyuncak hikayesi"],
    "pirates of the caribbean karayip korsanlari serisi": ["karayip korsanlari"],
    "the shawshank redemption esaretin bedeli": ["esaretin bedeli izle", "esaretin bedeli"],
    "a beautiful mind akil oyunlari": ["akil oyunlari", "beautiful mind"],
}
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

log = logging.getLogger("url_tour")


def setup_logging():
    LOGF.parent.mkdir(exist_ok=True)
    log.setLevel(logging.INFO)
    fh = logging.FileHandler(LOGF, encoding="utf-8")
    sh = logging.StreamHandler(sys.stdout)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fh.setFormatter(fmt)
    sh.setFormatter(fmt)
    log.addHandler(fh)
    log.addHandler(sh)


def norm(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.casefold().replace("ı", "i").replace("ş", "s").replace("ğ", "g")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def title_score(rec_title, page_title):
    names = [rec_title] + ALIAS.get(norm_key(rec_title), [])
    best, bkind = 0.0, "none"
    for name in names:
        s, k = single_score(name, page_title)
        if s > best:
            best, bkind = s, k
    return best, bkind


def norm_key(s):
    return re.sub(r"\s+", " ", norm(s))


def single_score(rec_title, page_title):
    r, p = norm(rec_title), norm(page_title)
    if not r or not p:
        return 0.0, "empty"
    if r == p or r in p:
        return 1.0, "substring"
    rt = set(r.split())
    pt = set(p.split())
    if rt and rt <= pt:
        return 1.0, "tokens-subset"
    matched = sum(len(t) for t in rt if t in pt)
    cov = matched / len(r.replace(" ", ""))
    inter = len(rt & pt)
    f1 = 2 * inter / (len(rt) + len(pt)) if rt and pt else 0.0
    ratio = difflib.SequenceMatcher(None, r, p).ratio()
    best = max(cov, f1, ratio)
    kind = ("cov" if cov >= f1 and cov >= ratio else
            ("token-f1" if f1 >= ratio else "seq"))
    return best, kind


def extract_suspects():
    rows = {}
    section = None
    for ln in LISTE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^## ([A-ZÇĞİÖŞÜ]+)", ln)
        if m:
            section = m.group(1).lower()
        m = re.match(r"^\| (\d+) \| (.+?) \| .+? \| .+? \| .+? \| .+? \| .+? \| (\S+?) \| .*⚠ C \|", ln)
        if m:
            rows[int(m.group(1))] = {
                "id": int(m.group(1)), "title": m.group(2).strip(),
                "type": section, "current_url": m.group(3),
            }
    return rows


def ddg_search(q, n=10):
    url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(q)
    try:
        resp = requests.get(url, headers={"User-Agent": UA}, timeout=15)
    except Exception as e:
        log.warning("DDG hata %s: %s", q[:60], e)
        return []
    links = []
    for m in re.finditer(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', resp.text, re.S):
        href = urllib.parse.unquote(m.group(1))
        u = urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get("uddg", [href])[0]
        title = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        links.append((u, title))
    return links[:n]


def fetch_page_title(url):
    try:
        resp = requests.get(url, headers={"User-Agent": UA}, timeout=12,
                            allow_redirects=True)
        html = resp.text[:200000]
        src = f"http-{resp.status_code}"
    except Exception:
        if cr is None:
            return None, "fetch-fail"
        try:
            resp = cr.get(url, impersonate="chrome", timeout=15,
                          headers={"Accept-Language": "tr-TR,tr;q=0.9"})
            html = resp.text[:200000]
            src = f"curl-{resp.status_code}"
        except Exception as e:
            return None, f"fetch-fail: {type(e).__name__}"
    for pat in (r'<meta property="og:title" content="([^"]+)"',
                r"<title[^>]*>(.*?)</title>",
                r"<h1[^>]*>(.*?)</h1>"):
        m = re.search(pat, html, re.S | re.I)
        if m:
            t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(1))).strip()
            if t:
                return t, src
    return None, src + "-no-title"


def pick_candidates(record):
    ttype = record["type"]
    pref = ANIME_DOMAINS if ttype in ANIME_TYPES else FILM_DOMAINS
    queries = [f'{record["title"]} izle', f'{record["title"]} 1 bölüm izle']
    cands, seen = [], set()
    for q in queries:
        for u, stitle in ddg_search(q):
            host = urllib.parse.urlparse(u).netloc.lower().replace("www.", "")
            dom = next((d for d in ALL_DOMAINS if host == d or host.endswith("." + d)), None)
            if not dom or u in seen:
                continue
            seen.add(u)
            cands.append({"url": u, "domain": dom,
                          "pref": dom in pref, "serp_title": stitle})
        time.sleep(1.5)
    cands.sort(key=lambda c: -c["pref"])
    return cands


def api(path, method="GET", body=None):
    fn = {"GET": requests.get, "POST": requests.post, "PATCH": requests.patch}[method]
    r = fn(API + path, json=body, timeout=15)
    return r.status_code, (r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text)


_SITES_BY_CONTENT = {}


def sites_index():
    if not _SITES_BY_CONTENT:
        code, body = api("/api/sites")
        if code != 200 or not isinstance(body, list):
            raise RuntimeError(f"/api/sites {code}")
        for s in body:
            _SITES_BY_CONTENT.setdefault(s["content_id"], []).append(s)
    return _SITES_BY_CONTENT


BLOCK_PAT = ("451", "yasal", "just a moment", "attention required", "erişime kapalı",
             "bulunamadı", "not found", "403", "404")


def looks_blocked(t):
    t = t.lower()
    return any(p in t for p in BLOCK_PAT)


def process(record, apply_, preset_url=None):
    cid, title = record["id"], record["title"]
    log.info("=== ID %s [%s] '%s' mevcut=%s", cid, record["type"], title, record["current_url"][:70])
    if preset_url:
        u, _, st = preset_url.partition("|")
        force = st.endswith("!")
        if force:
            st = st[:-1]
        cands = [{"url": u,
                  "domain": urllib.parse.urlparse(u).netloc.removeprefix("www."),
                  "pref": True, "serp_title": st, "force": force}]
    else:
        cands = pick_candidates(record)
    if not cands:
        log.warning("ID %s: aday yok -> ⚠kontrol", cid)
        return {"id": cid, "status": "kontrol", "reason": "aday-yok"}
    for c in cands[:4]:
        ptitle, how = fetch_page_title(c["url"])
        prov = "live"
        if ptitle and looks_blocked(ptitle):
            log.info("ID %s: engel-basligi yakalandi ('%s') -> serp kanitina dus", cid, ptitle[:50])
            ptitle = None
        if not ptitle and c.get("serp_title"):
            ptitle, how, prov = c["serp_title"], "serp-kanit", "serp"
        if not ptitle:
            log.info("ID %s: %s baslik alinamadi (%s)", cid, c["url"][:60], how)
            continue
        score, kind = title_score(title, ptitle)
        force = c.get("force")
        log.info("ID %s: aday %s | sayfa='%s' | skor=%.2f(%s/%s)", cid,
                 c["url"][:60], ptitle[:70], score, kind, prov)
        if score >= 0.8 or (force and score >= 0.45):
            out = {"id": cid, "status": "pass", "url": c["url"],
                   "domain": c["domain"], "score": round(score, 2), "page_title": ptitle}
            if apply_:
                wrong = [s for s in sites_index().get(cid, []) if s.get("is_primary")]
                code, body = api(f"/api/content/{cid}/sites", "POST",
                                 {"site_name": BRAND.get(c["domain"], c["domain"]),
                                  "site_url": c["url"], "is_primary": True})
                if code != 201:
                    log.error("ID %s: POST %s %s", cid, code, body)
                    out["status"] = "apply-fail"
                    return out
                for s in wrong:
                    if s["site_url"] != c["url"]:
                        api(f"/api/sites/{s['id']}/mark-dead", "PATCH")
                        log.info("ID %s: eski yanlis primary id=%s mark-dead (%s)", cid, s["id"], s["site_url"][:60])
                out["applied"] = True
                out["old_dead"] = [s["id"] for s in wrong]
            log.info("ID %s: KABUL skor=%.2f -> %s (apply=%s)", cid, score, c["url"][:60], apply_)
            return out
        if score >= 0.6:
            log.warning("ID %s: sinirda %.2f -> ⚠kontrol (yazilmadi)", cid, score)
            return {"id": cid, "status": "kontrol", "score": round(score, 2),
                    "url": c["url"], "page_title": ptitle}
    log.warning("ID %s: dogrulanmis aday yok -> ⚠kontrol", cid)
    return {"id": cid, "status": "kontrol", "reason": "skor-dusuk"}


SECTION_ORDER = ["anime", "manga", "manhwa", "series", "movie", "cartoon", "game"]
SECTION_TITLE = {"anime": "ANIME", "manga": "MANGA", "manhwa": "MANHWA",
                 "series": "SERIES", "movie": "MOVIE", "cartoon": "CARTOON",
                 "game": "GAME"}
SOURCE_NAME = {"mal": "MyAnimeList", "anilist": "AniList", "tmdb": "TMDB",
               "imdb": "IMDb", "steam": "Steam", "mangadex": "MangaDex"}
MEDIA_TYPES = {"anime", "manga", "manhwa"}


def fmt(v):
    if v is None or v == "":
        return "-"
    return f"{float(v):.1f}"


def fmt_int(v):
    if v is None or v == "":
        return "-"
    fv = float(v)
    return str(int(fv)) if fv.is_integer() else str(fv)


def provider_url(ext):
    if not ext or ":" not in ext:
        return ""
    kind, _, eid = ext.partition(":")
    return {
        "mal": f"https://myanimelist.net/anime/{eid}",
        "anilist": f"https://anilist.co/anime/{eid}",
        "tmdb": f"https://www.themoviedb.org/movie/{eid}",
        "imdb": f"https://www.imdb.com/title/tt{eid}" if eid.isdigit() else "",
        "steam": f"https://store.steampowered.com/app/{eid}",
        "mangadex": f"https://mangadex.org/title/{eid}",
    }.get(kind, "")


def pick_watch_url(c):
    sites = c.get("sites", [])
    live = [s for s in sites if not s.get("is_dead")]
    if live:
        prim = [s for s in live if s.get("is_primary")]
        return sorted(prim or live, key=lambda s: s["id"])[0]["site_url"]
    prim_all = [s for s in sites if s.get("is_primary")]
    if prim_all:
        return sorted(prim_all, key=lambda s: s["id"])[0]["site_url"]
    return ""


def regen():
    setup_logging()
    code, items = api("/api/content")
    if code != 200:
        log.error("/api/content %s", code)
        return
    groups = {t: [] for t in SECTION_ORDER}
    for c in items:
        if c.get("type") in groups:
            groups[c["type"]].append(c)
    ext = c.get("external_id") or ""
    lines = ["# KUROWATCH - TUM MEDYA ENVANTERI (2026-08-24)", "",
             f"Toplam **{len(items)}** kayit (merge sonrasi; efsanevi 714'un birlesmis hali).", "",
             "Siralama: kategori -> baslik. `Detay Kaynagi` = kart bilgilerinin cekildigi site. ",
             "`Kaynak URL` = izleme/indirme sayfasi (site tablosundaki canli primary link; yoksa saglayici sayfasi). ",
             "`API Puan` = saglayicidan gelen 10'luk puan (IMDb degil — IMDb puani icin Ayarlar'a TMDB/OMDb key gerekli).", "",
             "Legendlar: `⚠ C` = tip/kaynak capraz suphe (kaptan kontrol listesi), `-` = veri yok.", "", ""]
    for t in SECTION_ORDER:
        rows = sorted(groups[t], key=lambda x: (x.get("title") or "").lower())
        lines.append(f"## {SECTION_TITLE[t]} ({len(rows)})")
        lines.append("")
        lines.append("| ID | Baslik | Detay Kaynagi | API Puan | Benim Puan | Durum | Bolum/Ch | Kaynak URL | Not |")
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for c in rows:
            ext = c.get("external_id") or ""
            kind = ext.partition(":")[0]
            sname = SOURCE_NAME.get(kind, "-")
            src_is_media = kind in ("mal", "anilist", "mangadex")
            cross = (c["type"] in MEDIA_TYPES and kind in ("tmdb", "imdb")) or \
                    (c["type"] not in MEDIA_TYPES and src_is_media)
            url = pick_watch_url(c) or provider_url(ext)
            ch = c.get("total_episodes") if t in ("anime", "series", "movie",
                                                  "cartoon") else c.get("total_chapters")
            if t == "game":
                ch = None
            if cross:
                note = "⚠ C"
            elif not ext:
                note = "kaynak yok url yok" if not url else "kaynak yok"
            else:
                note = ""
            lines.append(f"| {c['id']} | {c.get('title') or '-'} | {sname} | "
                         f"{fmt(c.get('external_score'))} | {fmt(c.get('my_score'))} | "
                         f"{c.get('status') or '-'} | {fmt_int(ch)} | {url or '-'} | {note} |")
        lines.append("")
    out = "\n".join(lines).rstrip() + "\n"
    LISTE.write_text(out, encoding="utf-8")
    n_cross = out.count("⚠ C")
    log.info("REGEN OK: %d kayit -> %s (%d ⚠C)", len(items), LISTE.name, n_cross)


def slugify(title):
    return norm(title).replace(" ", "-")


def old_slugs(record):
    out = set()
    for s in sites_index().get(record["id"], []):
        u = s.get("site_url") or ""
        if "tranimaci.com" not in u and "turkanime" not in u:
            continue
        m = re.search(r"/(?:video|anime)/([^/?]+)", u)
        if not m:
            m = re.search(r"/([^/?]+?)(?:-1-bolum(?:-izle)?|-\d+-bolum(?:-izle)?)/?$", u)
        if not m:
            continue
        slug = re.sub(r"-\d+-bolum(?:-izle)?$", "", m.group(1))
        if slug and len(slug) > 2:
            out.add(slug)
    return out


def auto_candidates(record):
    ttype = record["type"]
    urls = []
    if ttype in ANIME_TYPES:
        bases = old_slugs(record) | {slugify(record["title"])}
        for b in bases:
            urls += [f"https://www.turkanime.tv/video/{b}-1-bolum",
                     f"https://www.turkanime.tv/anime/{b}",
                     f"https://www.turkanime.tv/video/{b}"]
    else:
        bases = {slugify(record["title"])}
        for a in ALIAS.get(norm_key(record["title"]), []):
            bases.add(slugify(a))
        for b in bases:
            urls += [f"https://yerlifilmizle.org/{b}-izle/",
                     f"https://www.hdfilmizle.to/{b}-izle/",
                     f"https://yerlifilmizle.org/{b}/",
                     f"https://www.hdfilmizle.to/{b}/"]
    seen = set()
    return [u for u in urls if not (u in seen or seen.add(u))]


def _post_search(url, data, link_re):
    try:
        r = cr.post(url, data=data, impersonate="chrome", timeout=15,
                    headers={"Accept-Language": "tr-TR,tr;q=0.9"})
    except Exception:
        return []
    out = []
    for u, t in re.findall(link_re, r.text, re.S):
        if u.startswith("//"):
            u = "https:" + u
        t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t)).strip()
        out.append((u, t))
    return out


def search_turkanime(q):
    return _post_search("https://www.turkanime.tv/arama", {"arama": q},
                        r'href="(//www\.turkanime\.tv/anime/[^"]+)"[^>]*>((?:[^<]|<[^/][^>]*>)*?)</a>')


def search_ddizi(q):
    try:
        r = cr.post("https://www.ddizi.im/arama/", data={"arama": q},
                    impersonate="chrome", timeout=15,
                    headers={"Accept-Language": "tr-TR,tr;q=0.9"})
    except Exception:
        return []
    t = r.text
    i = t.find("arama sonuçları")
    if i < 0:
        return []
    seg = t[i:]
    if "bulunamad" in seg[:600]:
        return []
    out = []
    for u, ti in re.findall(
            r'href="(https://www\.ddizi\.im/diziler/\d+/[^"]+)"[^>]*title="([^"]{2,80})"', seg):
        ti = ti.replace(" izle", "").strip()
        if (u, ti) not in out:
            out.append((u, ti))
    return out[:6]


def process_auto(record, apply_):
    cid, title = record["id"], record["title"]
    log.info("=== AUTO ID %s [%s] '%s'", cid, record["type"], title)
    for url in auto_candidates(record)[:6]:
        ptitle, how = fetch_page_title(url)
        if not ptitle or "bulunamad" in ptitle.lower() or "not found" in ptitle.lower():
            continue
        score, kind = title_score(title, ptitle)
        log.info("ID %s: aday %s | '%s' | %.2f(%s)", cid, url[:62], ptitle[:60], score, kind)
        if score >= 0.8:
            out = {"id": cid, "status": "pass", "url": url,
                   "domain": urllib.parse.urlparse(url).netloc.removeprefix("www."),
                   "score": round(score, 2), "page_title": ptitle}
            if apply_:
                wrong = [s for s in sites_index().get(cid, []) if s.get("is_primary")]
                code, body = api(f"/api/content/{cid}/sites", "POST",
                                 {"site_name": BRAND.get(out["domain"], out["domain"]),
                                  "site_url": url, "is_primary": True})
                if code != 201:
                    log.error("ID %s: POST %s %s", cid, code, body)
                    out["status"] = "apply-fail"
                    return out
                for s in wrong:
                    if s["site_url"] != url:
                        api(f"/api/sites/{s['id']}/mark-dead", "PATCH")
                        log.info("ID %s: eski primary id=%s mark-dead", cid, s["id"])
                out["applied"] = True
            log.info("ID %s: KABUL -> %s", cid, url[:70])
            return out
        if score >= 0.6:
            log.warning("ID %s: sinirda %.2f -> ⚠kontrol", cid, score)
            return {"id": cid, "status": "kontrol", "score": round(score, 2), "url": url}
    res = search_fallback(record, apply_)
    if res:
        return res
    log.warning("ID %s: canli dogrulanmis aday yok -> ⚠kontrol", cid)
    return {"id": cid, "status": "kontrol", "reason": "auto-aday-yok"}


def try_apply(record, url, ptitle, apply_):
    cid = record["id"]
    title = record["title"]
    score, kind = title_score(title, ptitle)
    if score < 0.8:
        return None
    out = {"id": cid, "status": "pass", "url": url,
           "domain": urllib.parse.urlparse(url).netloc.removeprefix("www."),
           "score": round(score, 2), "page_title": ptitle}
    if apply_:
        wrong = [s for s in sites_index().get(cid, []) if s.get("is_primary")]
        code, body = api(f"/api/content/{cid}/sites", "POST",
                         {"site_name": BRAND.get(out["domain"], out["domain"]),
                          "site_url": url, "is_primary": True})
        if code != 201:
            log.error("ID %s: POST %s %s", cid, code, body)
            return None
        for s in wrong:
            if s["site_url"] != url:
                api(f"/api/sites/{s['id']}/mark-dead", "PATCH")
                log.info("ID %s: eski primary id=%s mark-dead", cid, s["id"])
        out["applied"] = True
    log.info("ID %s: KABUL(arama) -> %s", cid, url[:70])
    return out


def search_fallback(record, apply_):
    cid, title, ttype = record["id"], record["title"], record["type"]
    if ttype in ANIME_TYPES:
        results = search_turkanime(title)
        if not results:
            results = search_turkanime(" ".join(norm_key(title).split()[:3]))
        for u, st in results[:5]:
            m = re.search(r"/anime/([^/?]+)", u)
            if not m:
                continue
            slug = m.group(1)
            for ep_url in (f"https://www.turkanime.tv/video/{slug}-1-bolum",
                           f"https://www.turkanime.tv/anime/{slug}"):
                ptitle, how = fetch_page_title(ep_url)
                if not ptitle or "bulunamad" in ptitle.lower():
                    continue
                log.info("ID %s: TK-arama %s | '%s' (%.2f on-skor)", cid, ep_url[:60],
                         ptitle[:55], title_score(title, st)[0])
                res = try_apply(record, ep_url, ptitle, apply_)
                if res:
                    return res
        return None
    results = search_ddizi(title)
    for u, st in results[:5]:
        ptitle, how = fetch_page_title(u)
        if not ptitle or "bulunamad" in ptitle.lower() or "sonuç bulunamadı" in ptitle.lower():
            continue
        log.info("ID %s: DD-arama %s | '%s'", cid, u[:60], ptitle[:55])
        res = try_apply(record, u, ptitle, apply_)
        if res:
            return res
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids")
    ap.add_argument("--set", dest="pairs", help="id=url,id=url (kesif disaridan geldiginde)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--regen", action="store_true", help="MEDIA_LISTE.md yeniden uret")
    ap.add_argument("--auto", action="store_true",
                    help="site slug-probe ile otonom keşif (sadece canli acilanlar)")
    args = ap.parse_args()

    if args.regen:
        regen()
        return

    setup_logging()
    suspects = extract_suspects()
    log.info("MEDIA_LISTE supheli kayit: %d", len(suspects))
    presets = {}
    if args.pairs:
        for p in re.split(r",(?=\d+=)", args.pairs):
            k, _, v = p.partition("=")
            presets[int(k)] = v
    targets = [int(x) for x in args.ids.split(",")] if args.ids else (
        sorted(presets) if presets else sorted(suspects))
    if args.limit:
        targets = targets[:args.limit]
    done = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    results = []
    for cid in targets:
        if str(cid) in done and not presets:
            log.info("ID %s zaten islenmis, atla", cid)
            continue
        if cid not in suspects:
            log.warning("ID %s listede yok", cid)
            continue
        rec = suspects[cid]
        if args.auto:
            res = process_auto(rec, args.apply)
        else:
            res = process(rec, args.apply, preset_url=presets.get(cid))
        results.append(res)
        done[str(cid)] = res
        STATE.write_text(json.dumps(done, ensure_ascii=False, indent=1), encoding="utf-8")
        time.sleep(1)
    ok = [r for r in results if r["status"] == "pass"]
    kn = [r for r in results if r["status"] == "kontrol"]
    log.info("BATCH SONUC: %d islem | %d KABUL %s | %d ⚠kontrol %s",
             len(results), len(ok), [r["id"] for r in ok],
             len(kn), [r["id"] for r in kn])


if __name__ == "__main__":
    main()
