# kurowatch - Changelog

## v2.3 (25 Agustos 2026)

**Ekran-2 KULE AURA v2 — kaptan begenmeyisi uzerine tam yeniden tasarim.**

- **Yeni sahne (14 satir, programatik):** parildayan yildizlar + hilal / donen fener huzmesi (10 fazli sol-sag kol salinimi) + magenta lamba / radar kubbesi icinde 4-faz donen anten / balkonda kirpan gozcu (f%8==7 blink) / korkuluk + yanan sonen pencereler ([*]/[ ] deterministik flicker) / genisleyen temel / deniz ufku RADAR TARAMASI (beyaz kafa + yesul iz + 4 blip gecis sonrasi 40-kolon flash) / dalga satiri.
- **Ders uygulama:** DEEP-SMOKE ASSERT (tum satirlar SCENE_W uniform - programatik canvas, ham art literal YOK); PANEL-WRAP (SCENE_W<=96); AURA OKUNABILIRLIGI (satir bazli tek karakter dokusu); kaynakta sadece \\uXXXX escapes (mojibake/encoding yasaği GI-1/G3 uyumlu).
- **FAZ A:** 12->18 kare (0.12s), wordmark reveal daha akici.
- **Kanitlar:** py_compile PY_OK; frame-width assert 5 kare = SCENE_W; pytest unit menu 7/7; `< nul` EOF-pipe EXIT=0; ilk-3-bayt BOM-yok; mojibake taramasi 0.

## v2.2 (24 Agustos 2026)

**Menu-5 URL YONETIMI + duplike merge + sapkin tip fix + TEK-BAT uyumu.**

- **MENU-5 (Lord istegi; onceki "9"dan tasinandi):** URL yonetim paneli — [1] medya PAGER'i (tek kart + Enter/Space sonraki + q don; 677 kayit tek-tek), [2] sifirdan URL ile ekle (anilist/mal/tmdb/imdb/mangadex parse; anilist'te baslik+kapak+puan CANLI), [3] indirici siteleri (olu/canli + filtre + toggle). Yeni API: GET /api/sites, POST /api/content/from-url (201/409/422 kanitli).
- **READER-THREAD YARISI FIX (Lord'un "1'e bastim cevap yok" dersi):** live_menu reader-thread'i olmuyordu, sonraki input()'larin stdin'ini yutuyordu. Yeni mimari: TEK kalici thread + TEK kuyruk; _ask() ayni kuyruktan okur. Ayrica main()'de "5" hala EXIT olarak listeliydi (gizli bug) — temizlendi.
- **DEFAULT EN dogrulandi:** .lang tercihi 'tr' kaydi silindi → acilis EN ([L] ile kalici TR mumkun).

- **TEK-BAT POLITIKASI (15.1 k1):** redundant `start.bat` (eski http.server frontend launcher) SILINDI — islevi zaten menu-1'de (FastAPI frontend'i kendisi servis ediyor). Repoda tek giris: `kurowatch.bat`. README tablosu guncellendi.

- **MENU-9 (Lord istegi):** URL yonetim paneli — [1] kayitli medya listesi (isim + kaynak URL kutusu + kapak/puan durumu), [2] sifirdan URL ile icerik ekle (anilist/mal/tmdb/imdb/mangadex parse; anilist'te baslik+kapak+puan CANLI cekilir), [3] indirici siteleri (olu/canli sayac + domain filtre + ID ile toggle). Yeni API: GET /api/sites (1342 satir, content join), POST /api/content/from-url (201/409-dup/422-gecersiz; kanit: Frieren 154587 canli fetch).
- **7 review cifti karara baglandi:** MERGE Dexter(112->287, tmdb dogru) + Hababam(342->341) + Ben10 bundle(245->244); SPY/Kaguya S1-S2, JoJo 2012-vs-2000-OVA, Shangri-La S1/S2 AYRI kaldi (meşru sezon). Final: **677 kayit**.
- **Kanitlar:** pipe testleri EXIT=0; mangatr filtresi 84/84 OLU dogru; pytest 51/51.

## v2.1 (24 Agustos 2026)

**BAT_OLUSTURMA_REHBERI standardizasyonu (15.10 3-ekran + 12a i18n) + 4 launcher bug fix'i.**

- **Ekran-2 KULE AURA (15.10 k1):** izleme kulesi sahnesi - donen radar, yanip sonen beacon (magenta vurgu), gozcu chibi (gozler kayar), wordmark reveal + radar zemin seridi. TUSLA SKIP (msvcrt.kbhit), EOF-pipe guvenli. TEMA-BAG BENZERSIZLIK: kule/radar/gozcu motifi kurowatch'a ozel.
- **Ekran-3 MINI-AURA + CANLI MENU (15.10 k4/k6, kaizoku v2.1):** ust seritte mini radar chibi + versiyon/saat/port-durumu. Menu secim beklerken animasyon DURMAZ: Rich Live menu_frame(t) yeniler, giris reader-thread (sys.stdin.readline + queue, isatty gate YOK - ISATTY TUZAGI dersi). `< nul` EOF'ta zarif dusus (EXIT=0).
- **i18n (12a/15.6):** L10N tr/en + T() + [L] menu satiri. DEFAULT EN, tercih ROOT/.lang (.gitignore'da, .lang.example="en"). TAM KAPSAM: menu, boot adimlari, PASS/FAIL, panel basliklari, prompt, veda. Parite testi: tests/unit/test_menu_l10n.py (7 test).
- **PANEL-WRAP (15.10 k9):** paneller WIDTH=100 sabit.
- **4 launcher bug fix (logger kanitli):** pause_or_close NameError -> pause_enter; wslpath backslash yutma -> forward-slash + /mnt fallback; start-title tuzaigi -> Popen CREATE_NEW_CONSOLE; backend_alive localhost-only -> localhost+WSL-IP cift health-check + pick_url gercek URL.
- **Kanitlar:** `< nul` EXIT=0 (6s); `echo 0 |` EXIT=0; pytest 51/51; canli PASS Backend canli, /api/content 200 (676 kayit); logger sifir ERROR.
# kurowatch — Changelog

## v1.2 (1 Ağustos 2026)

**GÖREV 2 — WSL backend düzeltmesi (kurowatch.bat/kurowatch.sh v1.2).**

- **Kök neden:** Eski `kurowatch.bat` backend'i **Windows python'uyla** başlatıyordu → Windows'ta `uvicorn` YOK → backend hiç açılmıyor (port 8099 boş). Çözüm: tüm backend menüleri **WSL tabanlı** yapıldı (`/opt/kuroshin/venv`, uvicorn orada).
- **:FRONTEND menüsü KALDIRILDI:** FastAPI zaten frontend'i `main.py`'de mount ediyor (`app.mount("/", StaticFiles(html=True))`) → ayrı `python -m http.server` gereksizdi. `kurowatch.bat` menüsü tek backend sürecine indirgendi.
- **Yeni menü (v1.2):**
  - `[1] Backend + Frontend Baslat (arka plan)` — `start_backend.sh` (WSL) + tarayıcı aç
  - `[2] Sadece Backend Baslat (arka plan)` — `start_backend.sh` (WSL)
  - `[3] Backend On Planda (Ctrl+C ile durdur)` — ön plan uvicorn (WSL)
  - `[4] Port Temizle` — WSL `pkill`/`fuser` + Windows `taskkill`
  - `[5] Cikis`
- **Argüman desteği:** `kurowatch.bat 2` gibi direkt menü seçimi (EOF'ta eski değeri korumaması için `:MENU` başında `choice=` sıfırlanıyor).
- **Düzeltilen buglar:**
  - `wsl wslpath` pipe'ının stdin'i yutması (menü seçimi boş kalıyordu) → `wslpath` kaldırıldı, sabit `/mnt/c/KuroshinHQ/kurowatch` kullanılıyor.
  - `%~1` argüman + `goto MENU` sonsuz döngü (yüzlerce log satırı) → `:CLEAN`'da argümanlıysa `goto END`.
- **Kanıt:** `start_backend.sh` → uvicorn PID, 8099 LISTENING, `/docs` 200, `/api/content` 200; WSL IP `172.25.89.7:8099` → 200.
- **Açık (wslrelay):** Windows'tan `localhost:8099` bazen 000 (wslrelay kararsız), WSL IP'den her zaman 200.
- Commit: `919ac4d` (feat: kurowatch v1.2 — WSL backend, :FRONTEND kaldirma, yeni menu, arguman destegi, wslrelay :PICK_URL toleransi + CHANGELOG v1.2). Önceki satırdaki "37e9249 (başlık referansı)" yalnızca Q5 venv taşıma commit'iydi — v1.2 değişiklikleri 919ac4d ile commit edildi.

## v1.1 (1 Ağustos 2026)

**GÖREV 1: Ortak launcher logger standardı (kuro_logger).**

- **Ortak logger:** `_hub/shared-scripts/kuro_logger.bat` + `kuro_logger.sh` entegre edildi
- **Log hedefi:** `_hub/shared-logs/kurowatch_launcher.log` (oturum başlıklı, zaman damgalı)
- **Launcher güncellemeleri:**
  - `kurowatch.bat` v1.0 → v1.1 — her menü dalında log (FULL/BACKEND/FRONTEND/CLEAN), exit code yakalama
  - `start.bat` v1.0 — başlık bloğu + logger + FATAL/WARN dalları
  - `kurowatch.sh` v1.0 → v1.1 — logger entegrasyonu (set -e uyumlu) + **Q5 venv düzeltmesi** (sistem python'u `idna` eksikti → `/opt/kuroshin/venv` aktive edildi, test ile doğrulandı: 8099 LISTENING)
  - `start_backend.sh` v1.0 — başlık bloğu + logger + **ölü yol düzeltmesi** (`/mnt/c/Kuroshin/kurowatch` → dinamik `KW_ROOT`)
- Log formatı: `YYYY-MM-DDTHH:MM:SS [SEVIYE] mesaj`
- Commit: v1.1 + v1.2 değişiklikleri birlikte `919ac4d` ile commit edildi (yukarıdaki v1.2 entry'sine bakın).

## v1.0 (30 Temmuz 2026)

**Faz F: Bağımsız repo taşıması.** GitHub'dan `C:\KuroshinHQ\kurowatch\`'a temiz clone.

- **İç hiyerarşi:** 325 dosya — Faz B subtree ile birebir eşleşiyor
- **Launcher yazıldı:** `kurowatch.bat` (Windows, menülü) + `kurowatch.sh` (WSL/Linux)
- **Versiyon başlığı:** Standart blok (repo adı, versiyon, commit hash, CHANGELOG linki)
- **Backend test:** uvicorn FastAPI başlatıldı, HTTP 200 doğrulandı
- **Önceki commit:** bfdd0cd ("chore: add pre-commit secret/PII scanner hook")
