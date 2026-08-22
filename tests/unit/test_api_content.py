"""backend.routers.content API birim testleri (TestClient + gecici SQLite).

Sunucu/playwright GEREKTIRMEZ: ASGITransport ile in-process test.
"""
import pytest

pytestmark = pytest.mark.asyncio


async def _create_content(client, title="Test Anime", ctype="anime", **extra):
    payload = {"title": title, "type": ctype, **extra}
    r = await client.post("/api/content", json=payload)
    assert r.status_code in (200, 201), f"create basarisiz: {r.status_code} {r.text}"
    return r.json()


class TestContentCrud:
    async def test_list_empty_db_returns_200(self, client):
        # Normal durum: bos DB -> bos liste, 200.
        r = await client.get("/api/content")
        assert r.status_code == 200
        assert r.json() == []

    async def test_create_and_get_by_id(self, client):
        # Normal durum: olustur -> id ile geri oku.
        data = await _create_content(client, title="One Piece Test")
        cid = data.get("id")
        assert cid is not None
        r = await client.get(f"/api/content/{cid}")
        assert r.status_code == 200
        body = r.json()
        assert body["title"] == "One Piece Test"
        assert body["type"] == "anime"

    async def test_update_progress(self, client):
        # Normal durum: PATCH ile progress guncellemesi yansir.
        data = await _create_content(client)
        cid = data["id"]
        r = await client.patch(f"/api/content/{cid}", json={"my_progress": 5})
        assert r.status_code == 200
        r2 = await client.get(f"/api/content/{cid}")
        assert r2.json()["my_progress"] == 5

    async def test_delete_content(self, client):
        # Normal durum: silinen kayit 404 doner.
        data = await _create_content(client)
        cid = data["id"]
        r = await client.delete(f"/api/content/{cid}")
        assert r.status_code in (200, 204)
        r2 = await client.get(f"/api/content/{cid}")
        assert r2.status_code == 404

    async def test_get_nonexistent_returns_404(self, client):
        # Hata durumu: olmayan id -> 404.
        r = await client.get("/api/content/999999")
        assert r.status_code == 404

    async def test_delete_nonexistent_returns_404(self, client):
        # Hata durumu: olmayan kaydi silmek -> 404.
        r = await client.delete("/api/content/999999")
        assert r.status_code == 404

    async def test_patch_nonexistent_returns_404(self, client):
        # Hata durumu: olmayan kaydi guncellemek -> 404.
        r = await client.patch("/api/content/999999", json={"my_progress": 1})
        assert r.status_code == 404


class TestContentValidation:
    async def test_missing_title_rejected(self, client):
        # Hata durumu: title zorunlu — dogrulama hatasi.
        r = await client.post("/api/content", json={"type": "anime"})
        assert r.status_code in (400, 422)

    async def test_invalid_type_rejected_400(self, client):
        # Hata durumu: bilinmeyen icerik tipi -> 400.
        r = await client.post(
            "/api/content", json={"title": "X", "type": "uzayli-tur"}
        )
        assert r.status_code in (400, 422)


class TestContentFiltering:
    async def test_type_filter_only_matching(self, client):
        # Normal durum: type filtresi sadece eslesenleri dondurur.
        await _create_content(client, title="A", ctype="anime")
        await _create_content(client, title="M", ctype="manga")
        r = await client.get("/api/content?type=manga")
        assert r.status_code == 200
        items = r.json()
        assert len(items) == 1
        assert items[0]["type"] == "manga"

    async def test_search_q_matches_title_substring(self, client):
        # Normal durum: q parametresi baslikta arama yapar.
        await _create_content(client, title="Bespoke Anime Name")
        await _create_content(client, title="Farklı Kayit")
        r = await client.get("/api/content?q=bespoke")
        assert r.status_code == 200
        items = r.json()
        assert len(items) == 1
        assert items[0]["title"] == "Bespoke Anime Name"


class TestContentBoundary:
    async def test_unicode_title_preserved(self, client):
        # Sinir durumu: Turkce karakterler bozulmadan saklanir.
        data = await _create_content(client, title="Türkçe İçerik ĞÜŞİÖÇ")
        cid = data["id"]
        r = await client.get(f"/api/content/{cid}")
        assert "Türkçe" in r.json()["title"]

    async def test_empty_title_handled_without_server_error(self, client):
        # Sinir durumu: bos title — 422/400 ya da kabul; 500 ASLA.
        r = await client.post("/api/content", json={"title": "", "type": "anime"})
        assert r.status_code < 500

    async def test_all_seven_content_types_accepted(self, client):
        # Sinir durumu: CONTENT_TYPES'taki her tip gecerlidir.
        for ctype in ("anime", "manga", "manhwa", "game", "series", "movie", "cartoon"):
            data = await _create_content(client, title=f"T-{ctype}", ctype=ctype)
            assert data["type"] == ctype
