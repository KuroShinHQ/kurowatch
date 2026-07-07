"""
Abstract download client wrapper: qBittorrent WebUI + Aria2 JSON-RPC.
"""
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class TorrentInfo:
    name: str
    size: int
    progress: float  # 0-100
    speed: int       # bytes/s
    eta: int         # seconds
    state: str       # downloading / paused / completed / error
    hash_id: str

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self) -> dict:
        return {
            "name": getattr(self, "name", ""),
            "size": getattr(self, "size", 0),
            "progress": round(getattr(self, "progress", 0), 1),
            "speed": getattr(self, "speed", 0),
            "eta": getattr(self, "eta", 0),
            "state": getattr(self, "state", "unknown"),
            "hash": getattr(self, "hash_id", ""),
        }


class DownloadClient(ABC):
    @abstractmethod
    async def add_torrent(self, magnet_url: str, save_path: Optional[str] = None) -> str:
        """Add magnet. Returns torrent hash/id."""

    @abstractmethod
    async def get_status(self) -> list[TorrentInfo]:
        """Return all active torrents."""

    @abstractmethod
    async def pause(self, hash_id: str) -> bool:
        """Pause torrent."""

    @abstractmethod
    async def resume(self, hash_id: str) -> bool:
        """Resume torrent."""

    @abstractmethod
    async def remove(self, hash_id: str) -> bool:
        """Remove torrent (delete files too)."""


# ── qBittorrent ───────────────────────────────────────────────────────

class QBittorrentClient(DownloadClient):
    def __init__(self, url: str, username: str = "", password: str = ""):
        self.base = url.rstrip("/")
        self.username = username
        self.password = password
        self._client = httpx.AsyncClient(timeout=10, follow_redirects=True)
        self._cookies: dict = {}

    async def _login(self) -> bool:
        if self._cookies.get("SID"):
            return True
        try:
            r = await self._client.post(
                f"{self.base}/api/v2/auth/login",
                data={"username": self.username, "password": self.password},
            )
            if r.status_code == 200 and r.text.strip() == "Ok.":
                for c in self._client.cookies.jar:
                    if c.name == "SID":
                        self._cookies["SID"] = c.value
                        return True
            logger.warning("qBittorrent login failed: HTTP %d", r.status_code)
            return False
        except Exception as e:
            logger.warning("qBittorrent login error: %s", e)
            return False

    async def add_torrent(self, magnet_url: str, save_path: Optional[str] = None) -> str:
        await self._login()
        data = {"urls": magnet_url}
        if save_path:
            data["savepath"] = save_path
        try:
            r = await self._client.post(
                f"{self.base}/api/v2/torrents/add",
                data=data,
                cookies=self._cookies,
            )
            if r.status_code in (200, 201):
                logger.info("qBittorrent: torrent added via magnet")
                return "ok"
            logger.warning("qBittorrent add error: HTTP %d %s", r.status_code, r.text[:100])
            return ""
        except Exception as e:
            logger.error("qBittorrent add exception: %s", e)
            return ""

    async def get_status(self) -> list[TorrentInfo]:
        await self._login()
        try:
            r = await self._client.get(
                f"{self.base}/api/v2/torrents/info",
                cookies=self._cookies,
            )
            if r.status_code != 200:
                return []
            data = r.json()
            result = []
            for t in data:
                eta = t.get("eta", 86400)
                if eta < 0:
                    eta = 0
                result.append(TorrentInfo(
                    name=t.get("name", ""),
                    size=t.get("total_size", 0),
                    progress=t.get("progress", 0) * 100,
                    speed=t.get("dlspeed", 0),
                    eta=eta,
                    state=t.get("state", "unknown"),
                    hash_id=t.get("hash", ""),
                ))
            return result
        except Exception as e:
            logger.error("qBittorrent status error: %s", e)
            return []

    async def pause(self, hash_id: str) -> bool:
        await self._login()
        try:
            r = await self._client.post(
                f"{self.base}/api/v2/torrents/pause",
                data={"hashes": hash_id},
                cookies=self._cookies,
            )
            return r.status_code == 200
        except Exception:
            return False

    async def resume(self, hash_id: str) -> bool:
        await self._login()
        try:
            r = await self._client.post(
                f"{self.base}/api/v2/torrents/resume",
                data={"hashes": hash_id},
                cookies=self._cookies,
            )
            return r.status_code == 200
        except Exception:
            return False

    async def remove(self, hash_id: str) -> bool:
        await self._login()
        try:
            r = await self._client.post(
                f"{self.base}/api/v2/torrents/delete",
                data={"hashes": hash_id, "deleteFiles": "true"},
                cookies=self._cookies,
            )
            return r.status_code == 200
        except Exception:
            return False


# ── Aria2 ─────────────────────────────────────────────────────────────

class Aria2Client(DownloadClient):
    def __init__(self, url: str, token: str = ""):
        self.url = url.rstrip("/")
        self.token = token
        self._client = httpx.AsyncClient(timeout=10)

    def _rpc(self, method: str, params: list = None) -> dict:
        body = {
            "jsonrpc": "2.0",
            "id": "kuro",
            "method": method,
            "params": [f"token:{self.token}"] + (params or []),
        }
        return body

    async def _call(self, method: str, params: list = None) -> Optional[dict]:
        try:
            r = await self._client.post(
                self.url,
                json=self._rpc(method, params),
            )
            if r.status_code == 200:
                data = r.json()
                if "error" in data:
                    logger.warning("Aria2 RPC error: %s", data["error"])
                    return None
                return data.get("result")
            logger.warning("Aria2 HTTP %d", r.status_code)
            return None
        except Exception as e:
            logger.error("Aria2 call error: %s", e)
            return None

    async def add_torrent(self, magnet_url: str, save_path: Optional[str] = None) -> str:
        params = [magnet_url]
        if save_path:
            params.append({"dir": save_path})
        r = await self._call("aria2.addUri", params)
        if r:
            return str(r)  # GID
        return ""

    async def get_status(self) -> list[TorrentInfo]:
        result = []
        # Get active + waiting + stopped
        for status_type in ["active", "waiting", "stopped"]:
            r = await self._call(f"aria2.tell{status_type.capitalize()}", [
                -1, 1000  # offset, num
            ])
            if not r:
                continue
            for t in r:
                total = int(t.get("totalLength", 0))
                completed = int(t.get("completedLength", 0))
                speed = int(t.get("downloadSpeed", 0))
                state = t.get("status", "unknown")
                remaining = t.get("remainingTime")
                try:
                    eta = int(remaining) if remaining else 0
                except (ValueError, TypeError):
                    eta = 0
                if state == "complete":
                    state = "completed"
                elif state == "active":
                    state = "downloading"
                elif state == "paused":
                    state = "paused"
                elif state == "error":
                    state = "error"
                result.append(TorrentInfo(
                    name=t.get("bittorrent", {}).get("info", {}).get("name", t.get("gid", "")),
                    size=total,
                    progress=(completed / total * 100) if total > 0 else 0,
                    speed=speed,
                    eta=eta,
                    state=state,
                    hash_id=t.get("gid", ""),
                ))
        return result

    async def pause(self, hash_id: str) -> bool:
        r = await self._call("aria2.pause", [hash_id])
        return r == "OK"

    async def resume(self, hash_id: str) -> bool:
        r = await self._call("aria2.unpause", [hash_id])
        return r == "OK"

    async def remove(self, hash_id: str) -> bool:
        r = await self._call("aria2.removeDownloadResult", [hash_id])
        if r == "OK":
            return True
        # Try force remove active
        r2 = await self._call("aria2.forceRemove", [hash_id])
        return r2 == "OK"


# ── Factory ───────────────────────────────────────────────────────────

def create_client(cfg: dict) -> Optional[DownloadClient]:
    client_type = cfg.get("download_client_type", "").lower()
    if client_type == "qbittorrent":
        url = cfg.get("qb_url", "http://localhost:8080")
        return QBittorrentClient(url, cfg.get("qb_username", ""), cfg.get("qb_password", ""))
    elif client_type == "aria2":
        url = cfg.get("aria2_url", "http://localhost:6800/jsonrpc")
        return Aria2Client(url, cfg.get("aria2_token", ""))
    return None
