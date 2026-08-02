#!/bin/bash
# ============================================
# kurowatch.sh
# Versiyon: v1.1
# Aciklama: KuroWatch backend (uvicorn) baslatma (WSL/Linux)
# Repo: KuroShinHQ/kurowatch
# Son guncelleme commit: 37e9249
# Detay: docs/CHANGELOG.md
# ============================================
set -e

source /opt/kuroshin/venv/bin/activate

KW_ROOT="$(cd "$(dirname "$0")" && pwd)"
HUB_DIR="$(dirname "$KW_ROOT")/_hub"
KLOG_FILE="$HUB_DIR/shared-logs/kurowatch_launcher.log"
source "$HUB_DIR/shared-scripts/kuro_logger.sh" "$KLOG_FILE"
KW_PORT=8099

cleanup() {
    klog INFO "Port temizleniyor..."
    pkill -f "uvicorn backend.main" 2>/dev/null || true
    fuser -k "${KW_PORT}/tcp" 2>/dev/null || true
    sleep 1
}

case "${1:-full}" in
    backend)
        cleanup
        klog INFO "Backend baslatiliyor (port $KW_PORT)..."
        cd "$KW_ROOT"
        exec python -m uvicorn backend.main:app --port "$KW_PORT" --host 0.0.0.0 --log-level warning
        ;;
    full|*)
        cleanup
        klog INFO "Backend baslatiliyor (background)..."
        cd "$KW_ROOT"
        nohup python -m uvicorn backend.main:app --port "$KW_PORT" --host 0.0.0.0 --log-level warning > /tmp/kurowatch.log 2>&1 &
        KW_PID=$!
        klog INFO "PID: $KW_PID"
        sleep 3
        echo "[KuroWatch] http://localhost:$KW_PORT"
        if command -v xdg-open &>/dev/null; then
            xdg-open "http://localhost:$KW_PORT" 2>/dev/null || true
        elif command -v open &>/dev/null; then
            open "http://localhost:$KW_PORT" 2>/dev/null || true
        fi
        ;;
esac
