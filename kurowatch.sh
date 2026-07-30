#!/bin/bash
# ============================================
# kurowatch.sh
# Versiyon: v1.0
# Aciklama: KuroWatch backend (uvicorn) baslatma (WSL/Linux)
# Repo: KuroShinHQ/kurowatch
# Son guncelleme commit: bfdd0cd ("chore: add pre-commit secret/PII scanner hook")
# Detay: docs/CHANGELOG.md
# ============================================
set -e

KW_ROOT="$(cd "$(dirname "$0")" && pwd)"
KW_PORT=8099

cleanup() {
    echo "[KuroWatch] Port temizleniyor..."
    pkill -f "uvicorn backend.main" 2>/dev/null || true
    fuser -k "${KW_PORT}/tcp" 2>/dev/null || true
    sleep 1
}

case "${1:-full}" in
    backend)
        cleanup
        echo "[KuroWatch] Backend baslatiliyor (port $KW_PORT)..."
        cd "$KW_ROOT"
        exec python -m uvicorn backend.main:app --port "$KW_PORT" --host 0.0.0.0 --log-level warning
        ;;
    full|*)
        cleanup
        echo "[KuroWatch] Backend baslatiliyor (background)..."
        cd "$KW_ROOT"
        nohup python -m uvicorn backend.main:app --port "$KW_PORT" --host 0.0.0.0 --log-level warning > /tmp/kurowatch.log 2>&1 &
        KW_PID=$!
        echo "[KuroWatch] PID: $KW_PID"
        sleep 3
        echo "[KuroWatch] http://localhost:$KW_PORT"
        if command -v xdg-open &>/dev/null; then
            xdg-open "http://localhost:$KW_PORT" 2>/dev/null || true
        elif command -v open &>/dev/null; then
            open "http://localhost:$KW_PORT" 2>/dev/null || true
        fi
        ;;
esac
