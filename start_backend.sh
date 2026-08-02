#!/bin/bash
# ============================================
# start_backend.sh
# Versiyon: v1.0
# Aciklama: KuroWatch backend (uvicorn) arka plan baslatma
# Repo: KuroShinHQ/kurowatch
# Son guncelleme commit: 37e9249
# Detay: docs/CHANGELOG.md
# ============================================
KW_ROOT="$(cd "$(dirname "$0")" && pwd)"
HUB_DIR="$(dirname "$KW_ROOT")/_hub"
KLOG_FILE="$HUB_DIR/shared-logs/kurowatch_launcher.log"
source "$HUB_DIR/shared-scripts/kuro_logger.sh" "$KLOG_FILE"
klog_header "start_backend.sh v1.0"

pkill -f 'uvicorn backend.main' 2>/dev/null
fuser -k 8099/tcp 2>/dev/null
sleep 1
source /opt/kuroshin/venv/bin/activate
cd "$KW_ROOT"
setsid python -m uvicorn backend.main:app --port 8099 --host 0.0.0.0 --log-level warning > /tmp/kwb.log 2>&1 &
klog INFO "KuroWatch PID: $!"
