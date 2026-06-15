from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend import push_manager

router = APIRouter()


class SubscribeReq(BaseModel):
    endpoint: str
    keys: dict
    expirationTime: Optional[float] = None


class UnsubscribeReq(BaseModel):
    endpoint: str


class TestPushReq(BaseModel):
    title: str = "KuroWatch"
    body:  str = "Push bildirimleri çalışıyor! 🎉"


@router.get("/push/vapid-public-key")
async def get_vapid_key():
    pub, _ = push_manager.get_or_create_vapid_keys()
    return {"publicKey": pub}


@router.post("/push/subscribe")
async def subscribe(req: SubscribeReq):
    count = push_manager.add_subscription(req.model_dump(exclude_none=True))
    return {"ok": True, "subscriptions": count}


@router.delete("/push/subscribe")
async def unsubscribe(req: UnsubscribeReq):
    removed = push_manager.remove_subscription(req.endpoint)
    return {"ok": removed}


@router.get("/push/subscriptions/count")
async def count_subscriptions():
    return {"count": len(push_manager.load_subs())}


@router.post("/push/test")
async def test_push(req: TestPushReq):
    try:
        result = push_manager.send_push(req.title, req.body, "/#screen-updates")
        return result
    except Exception as exc:
        raise HTTPException(500, str(exc))
