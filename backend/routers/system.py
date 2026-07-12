import asyncio
import io
import json
import os
import shutil
import time
import zipfile
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db, DB_PATH

router = APIRouter()

_BACKUP_DIR = Path(os.path.dirname(DB_PATH)) / "backups"
_BACKUP_DIR.mkdir(exist_ok=True)

_TAG = "[BACKUP]"

# ── Domain Health Tag ──────────────────────────────────────────────
_D_TAG = "[DOMAIN]"

# ── Request/Response Models ────────────────────────────────────────


class DomainCheckRequest(BaseModel):
    domain: Optional[str] = None


class DomainFindRequest(BaseModel):
    dead_domain: str
    site_name: Optional[str] = ""
    sample_path: Optional[str] = "/"


class DomainApplyRequest(BaseModel):
    dead_domain: str
    new_domain: str
    content_type: Optional[str] = None


class DomainTestRequest(BaseModel):
    sample_size: int = 3
    specific_domain: Optional[str] = None


class DomainCheckLiveRequest(BaseModel):
    urls: list[str]


def _db_path() -> str:
    return DB_PATH if os.path.isabs(DB_PATH) else os.path.join(
        os.path.dirname(os.path.dirname(__file__)), DB_PATH
    )


@router.post("/system/backup")
async def create_backup(db: AsyncSession = Depends(get_db)):
    """Create a compressed backup of the SQLite database."""
    db_file = _db_path()
    if not os.path.exists(db_file):
        raise HTTPException(404, "Database file not found")

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_name = f"kurowatch_{ts}.zip"
    backup_path = _BACKUP_DIR / backup_name

    try:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(db_file, "kurowatch.db")
            config_path = os.path.join(os.path.dirname(db_file), "..", "config.json")
            if os.path.exists(config_path):
                zf.write(config_path, "config.json")
        buf.seek(0)

        with open(backup_path, "wb") as f:
            f.write(buf.getvalue())

        size_kb = os.path.getsize(backup_path) / 1024
        print(f"{_TAG} Backup created: {backup_name} ({size_kb:.1f} KB)")

        return {
            "success": True,
            "filename": backup_name,
            "size_kb": round(size_kb, 1),
            "created_at": ts,
        }
    except Exception as e:
        raise HTTPException(500, f"Backup failed: {e}")


@router.get("/system/backup")
async def list_backups():
    """List all available backup files."""
    files = sorted(_BACKUP_DIR.iterdir(), key=lambda f: f.stat().st_mtime, reverse=True)
    backups = []
    for f in files:
        if f.suffix == ".zip":
            stat = f.stat()
            backups.append({
                "filename": f.name,
                "size_kb": round(stat.st_size / 1024, 1),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
    return {"backups": backups}


@router.get("/system/backup/{filename}")
async def download_backup(filename: str):
    """Download a backup file."""
    filepath = _BACKUP_DIR / filename
    if not filepath.exists() or not filepath.is_file():
        raise HTTPException(404, f"Backup not found: {filename}")
    return StreamingResponse(
        open(filepath, "rb"),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/system/restore")
async def restore_backup(file: UploadFile = File(...)):
    """Restore database from an uploaded backup zip."""
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(400, "Only .zip files accepted")

    try:
        contents = await file.read()
        db_file = _db_path()

        backup_dir = os.path.dirname(db_file)
        restore_timestamp = int(time.time())

        # Backup current DB before overwriting
        current_backup = os.path.join(backup_dir, f"pre_restore_{restore_timestamp}.db")
        if os.path.exists(db_file):
            shutil.copy2(db_file, current_backup)

        with zipfile.ZipFile(io.BytesIO(contents)) as zf:
            if "kurowatch.db" not in zf.namelist():
                # Remove pre-restore backup if nothing was extracted
                if os.path.exists(current_backup):
                    os.remove(current_backup)
                raise HTTPException(400, "ZIP does not contain kurowatch.db")

            zf.extract("kurowatch.db", backup_dir)

        print(f"{_TAG} Restore complete from {file.filename}")
        return {
            "success": True,
            "note": "Database restored. Backend must be restarted.",
            "pre_restore_backup": f"pre_restore_{restore_timestamp}.db",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Restore failed: {e}")


# ═══════════════════════════════════════════════════════════════════
# DOMAIN HEALTH ENDPOINTS (SOHBET-147)
# ═══════════════════════════════════════════════════════════════════


@router.post("/system/domains/check")
async def domain_health_check(req: DomainCheckRequest, db: AsyncSession = Depends(get_db)):
    """Run health check on all (or specific) domains, update is_dead in DB."""
    from backend.services.domain_health import check_single_url, get_all_domains, get_domain_sample_urls

    if req.domain:
        urls_to_check = [f"https://www.{req.domain}"]
    else:
        domains = await get_all_domains(db)
        urls_to_check = domains

    results = {}
    for domain in urls_to_check[:100]:
        samples = await get_domain_sample_urls(db, domain) if not req.domain else [f"https://www.{domain}"]
        if not samples:
            results[domain] = {"status": "NO_SAMPLES"}
            continue
        health_result = await check_single_url(samples[0])
        results[domain] = {
            "status": health_result.status,
            "status_code": health_result.status_code,
            "elapsed_ms": health_result.elapsed_ms,
            "error": health_result.error,
        }

    # Update DB
    from backend.services.domain_health import update_dead_status
    from backend.services.domain_health import HealthResult

    health_results = {}
    for domain, r in results.items():
        hr = HealthResult(domain=domain, status=r.get("status", "ERROR"),
                          status_code=r.get("status_code"))
        health_results[domain] = hr
    updated = await update_dead_status(db, health_results)

    return {
        "checked": len(results),
        "updated_sites": updated,
        "results": results,
    }


@router.get("/system/domains/status")
async def domain_status(db: AsyncSession = Depends(get_db)):
    """Get current domain health status from DB."""
    result = await db.execute(text("""
        SELECT s.site_name, s.site_url, s.is_dead,
               COUNT(DISTINCT CASE WHEN e.id IS NOT NULL THEN e.id END) as episode_count,
               c.title, c.type
        FROM site s
        LEFT JOIN content c ON c.id = s.content_id
        LEFT JOIN episode e ON e.content_id = s.content_id AND e.url LIKE '%' || s.site_url || '%'
        GROUP BY s.id
        ORDER BY s.is_dead DESC, s.site_name
        LIMIT 200
    """))
    sites = []
    dead_count = 0
    for row in result.fetchall():
        site = {
            "site_name": row[0],
            "site_url": row[1],
            "is_dead": row[2],
            "episode_count": row[3],
            "content_title": row[4],
            "content_type": row[5],
        }
        if row[2]:
            dead_count += 1
        sites.append(site)

    return {
        "total_sites": len(sites),
        "dead_sites": dead_count,
        "sites": sites,
    }


@router.post("/system/domains/find")
async def domain_find(req: DomainFindRequest):
    """Find working alternative domains for a dead domain."""
    from backend.services.domain_finder import find_alternatives_for_domain

    candidates = await find_alternatives_for_domain(
        req.dead_domain, req.site_name, req.sample_path
    )
    return {
        "dead_domain": req.dead_domain,
        "candidates": [
            {
                "domain": c.domain,
                "source": c.source,
                "status": c.status,
                "status_code": c.status_code,
                "error": c.error,
            }
            for c in candidates
        ],
    }


@router.post("/system/domains/apply")
async def domain_apply(req: DomainApplyRequest, db: AsyncSession = Depends(get_db)):
    """Apply a new domain alternative to all affected content."""
    from backend.services.db_updater import apply_alternative_domain

    results = await apply_alternative_domain(
        db, req.dead_domain, req.new_domain, req.content_type
    )
    return {
        "dead_domain": req.dead_domain,
        "new_domain": req.new_domain,
        "contents_updated": len(results),
        "total_episodes_updated": sum(r.episodes_updated for r in results),
        "results": [
            {
                "content_id": r.content_id,
                "content_title": r.content_title,
                "site_updated": r.site_updated,
                "episodes_updated": r.episodes_updated,
                "error": r.error,
            }
            for r in results
        ],
    }


@router.post("/system/domains/test")
async def domain_test(req: DomainTestRequest, db: AsyncSession = Depends(get_db)):
    """Test all URLs and produce a report."""
    from backend.services.test_runner import run_full_test

    report = await run_full_test(
        db, sample_size=req.sample_size, specific_domain=req.specific_domain
    )
    return {
        "started_at": report.started_at,
        "finished_at": report.finished_at,
        "elapsed_seconds": report.elapsed_seconds,
        "total_urls": report.total_urls,
        "total_ok": report.total_ok,
        "total_dead": report.total_dead,
        "total_cloudflare": report.total_cloudflare,
        "ok_pct": report.ok_pct,
        "by_domain": {
            d: {"total": s.total, "ok": s.ok, "dead": s.dead, "cloudflare": s.cloudflare}
            for d, s in report.by_domain.items()
        },
        "by_content_type": {
            ct: {"total": s.total, "ok": s.ok}
            for ct, s in report.by_content_type.items()
        },
    }


@router.post("/system/domains/find-all-dead")
async def domain_find_all_dead(db: AsyncSession = Depends(get_db)):
    """Find alternatives for all dead domains in the DB."""
    from backend.services.domain_finder import find_and_test_all_dead

    all_candidates = await find_and_test_all_dead(db)
    result = {}
    for domain, candidates in all_candidates.items():
        working = [c for c in candidates if c.status == "OK"]
        result[domain] = {
            "total_candidates": len(candidates),
            "working": len(working),
            "candidates": [
                {"domain": c.domain, "source": c.source, "status": c.status}
                for c in candidates[:10]
            ],
        }
    return {"domains": result}


@router.post("/system/domains/check-live")
async def domain_check_live(req: DomainCheckLiveRequest, db: AsyncSession = Depends(get_db)):
    """Check live status of specific URLs (max 10)."""
    from backend.services.domain_health import check_single_url

    if len(req.urls) > 10:
        raise HTTPException(400, "Maximum 10 URLs per request")
    results = []
    for url in req.urls:
        r = await check_single_url(url)
        results.append({
            "url": url,
            "status": r.status,
            "status_code": r.status_code,
            "elapsed_ms": r.elapsed_ms,
            "error": r.error,
        })
    return {"results": results}
