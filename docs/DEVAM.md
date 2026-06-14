# 🚀 KuroWatch DEVAM — Yeni Sohbet Brief
**Son güncelleme:** 14 Haziran 2026 (sohbet-1) · **Aktif sürüm:** v0.1.0 · **Son commit:** `—`

> Yeni Claude'a tek-sayfa devamlılık. İlk önce **bu MD**'yi oku.

---

## ⚡ YENİ SOHBET BAŞLANGIÇ PROMPT (copy-paste)

```
KuroWatch DEVAM.md oku. Özet:

EN SON YAPILAN (14 Haz sohbet-1):
- Proje iskeleti oluşturuldu (klasör yapısı, docs, requirements.txt)
- GitHub repo: github.com/KuroShinHQ/kurowatch
- Kuroshin.bat entegrasyonu: [6] KuroWatch başlat planlandı

SIRADAKI GÖREV:
1. backend/database.py + models.py yaz
2. backend/main.py (FastAPI app)
3. Temel router'lar: content.py + sync.py
4. Stitch AI'dan frontend çıktısı alındıktan sonra frontend entegre
5. AniList API wrapper (anilist.py)
```

---

## 🎯 NEREDE KALDIK

**Sohbet-1 (14 Haz):** Proje kurulum.

### ✅ Tamamlananlar
- [ ] Klasör yapısı: `C:\Kuroshin\kurowatch\`
- [ ] `docs/YAPI.md` — tam mimari ve gereksinimler
- [ ] `backend/requirements.txt`
- [ ] GitHub repo oluşturuldu (`KuroShinHQ/kurowatch`)
- [ ] `.gitignore` oluşturuldu

### 🔴 Sıradaki (Öncelik Sırası)
1. `backend/database.py` — SQLite async engine + session factory
2. `backend/models.py` — Content, Site, Episode, Tag, TrackingSession ORM
3. `backend/main.py` — FastAPI app, CORS, router include, startup
4. `backend/routers/content.py` — temel CRUD
5. `backend/routers/sync.py` — export/import JSON
6. `backend/scraper/anilist.py` — metadata çekme
7. Frontend (Stitch AI sonrası)
8. Kuroshin.bat [6] entegrasyonu

---

## 🛠️ KRİTİK BİLGİLER

### Stack
- Backend: Python 3.11 + FastAPI + SQLAlchemy async + SQLite
- Frontend: Stitch AI çıktısı → static HTML/CSS/JS (FastAPI serve eder)
- Mobil: PWA (manifest + service worker) → telefonda "uygulamaya ekle"
- Port: `8099` (Kuroshin portlarından çakışmıyor)

### Veri Sync
- Export: `GET /api/export` → JSON indir
- Import: `POST /api/import` → JSON yükle, `updated_at` ile merge

### Yeni Bölüm Tespiti
- AniList GraphQL → MAL API → scraper fallback
- APScheduler ile periyodik kontrol

### Komutlar
```powershell
# Backend başlat
cd C:\Kuroshin\kurowatch
python -m uvicorn backend.main:app --reload --port 8099

# API test
curl http://localhost:8099/docs
```

### Portlar (Kuroshin ile çakışma yok)
```
8080 → Llama server
8082 → L2
9002 → Walker
9003 → Bridge WS
9004 → Bridge HTTP alarm
9005 → Chancellor HTTP
8099 → KuroWatch ← YENİ
```
