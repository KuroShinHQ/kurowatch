"""Check download job status"""
import httpx
r = httpx.get('http://localhost:8099/api/download/queue')
jobs = r.json().get('jobs', [])
for j in jobs:
    jid = j.get('id')
    if jid in (81, 82, 83, 84, 85):
        fp = j.get('file_path', '')
        err = (j.get('error') or '')[:100]
        print(f"Job #{jid}: status={j.get('status')} progress={j.get('progress_pct')}")
        print(f"  file_path={fp}")
        print(f"  error={err}")
