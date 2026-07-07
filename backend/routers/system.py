import os
import time
import shutil
import zipfile
import io
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db, DB_PATH

router = APIRouter()

_BACKUP_DIR = Path(os.path.dirname(DB_PATH)) / "backups"
_BACKUP_DIR.mkdir(exist_ok=True)

_TAG = "[BACKUP]"


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
