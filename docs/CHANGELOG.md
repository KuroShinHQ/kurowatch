# kurowatch — Changelog

## v1.0 (30 Temmuz 2026)

**Faz F: Bağımsız repo taşıması.** GitHub'dan `C:\KuroshinHQ\kurowatch\`'a temiz clone.

- **İç hiyerarşi:** 325 dosya — Faz B subtree ile birebir eşleşiyor
- **Launcher yazıldı:** `kurowatch.bat` (Windows, menülü) + `kurowatch.sh` (WSL/Linux)
- **Versiyon başlığı:** Standart blok (repo adı, versiyon, commit hash, CHANGELOG linki)
- **Backend test:** uvicorn FastAPI başlatıldı, HTTP 200 doğrulandı
- **Önceki commit:** bfdd0cd ("chore: add pre-commit secret/PII scanner hook")
