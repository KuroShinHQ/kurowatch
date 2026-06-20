#!/bin/bash
pkill -f 'uvicorn backend.main' 2>/dev/null
fuser -k 8099/tcp 2>/dev/null
sleep 1
source /root/kuroshin/venv/bin/activate
cd /mnt/c/Kuroshin/kurowatch
setsid python -m uvicorn backend.main:app --port 8099 --host 0.0.0.0 --log-level warning > /tmp/kwb.log 2>&1 &
echo "KuroWatch PID: $!"
