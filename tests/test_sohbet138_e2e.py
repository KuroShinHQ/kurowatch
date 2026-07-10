"""SOHBET-138 E2E tests — covers, downloads, streams"""
import pytest
from playwright.sync_api import expect


def _get_by_type(api, content_type, limit=3):
    r = api.get(f"/api/content?type={content_type}&limit={limit}")
    return r.json()


def _open_detail(app, content_id):
    app.evaluate(f"window.openDetail({content_id})")
    app.wait_for_timeout(1500)
    expect(app.locator("#screen-detail")).to_be_visible()


def test_movie_cover_from_tmdb(app, api):
    """SORUN-1: Movie/series covers should come from TMDB (https://image.tmdb.org)"""
    for ctype in ("movie", "series", "cartoon"):
        items = _get_by_type(api, ctype)
        if not items:
            pytest.skip(f"No {ctype} found")
        for item in items[:2]:
            cid = item["id"]
            _open_detail(app, cid)
            app.wait_for_timeout(800)
            cover_img = app.locator("#detail-cover-img")
            if cover_img.is_visible():
                src = cover_img.get_attribute("src") or ""
                assert "tmdb.org" in src, f"{ctype} #{cid} cover not from TMDB: {src[:80]}"


def test_manga_per_episode_download_buttons(app, api):
    """SORUN-2: Manga/manhwa episodes show download button per-chapter"""
    for ctype in ("manga", "manhwa"):
        items = _get_by_type(api, ctype)
        if not items:
            pytest.skip(f"No {ctype} found")
        for item in items[:2]:
            cid = item["id"]
            _open_detail(app, cid)
            app.wait_for_timeout(1000)
            ep_btns = app.locator(".ep-dl-btn")
            count = ep_btns.count()
            assert count > 0, f"{ctype} #{cid}: no per-episode download buttons found"


def test_manga_download_api_endpoint(app, api):
    """SORUN-3: Backend manga download accepts URLs without gallery-dl crash"""
    items = _get_by_type(api, "manga")
    if not items:
        pytest.skip("No manga found")
    for item in items[:2]:
        cid = item["id"]
        r = api.get(f"/api/content/{cid}")
        data = r.json()
        eps = data.get("episodes", [])
        urls = [e["url"] for e in eps[:3] if e.get("url")]
        if not urls:
            continue
        # Validate the backend can queue a download without immediate crash
        r2 = api.post("/api/download/start", json={
            "content_id": cid,
            "content_title": item["title"],
            "episode_number": eps[0]["number"],
            "url": urls[0],
            "media_type": "manga",
        })
        assert r2.status_code in (200, 409), f"Download start failed: {r2.status_code} {r2.text[:100]}"
        if r2.status_code == 200:
            job = r2.json()
            assert job["status"] in ("queued", "downloading", "done")


def test_stream_fallback_chain(app, api):
    """SORUN-4: Stream URL resolution falls back through mirrors"""
    items = _get_by_type(api, "anime")
    if not items:
        pytest.skip("No anime found")
    for item in items[:3]:
        cid = item["id"]
        r = api.get(f"/api/content/{cid}")
        data = r.json()
        eps = [e for e in data.get("episodes", []) if e.get("url")]
        if not eps:
            continue
        ep = eps[0]
        url = ep["url"]
        if "tranimaci.com" in url:
            r2 = api.get(f"/api/stream/url", params={"url": url})
            assert r2.status_code == 200, f"Stream URL failed: {r2.status_code}"
            result = r2.json()
            assert result.get("ok") or result.get("proxy_url") or result.get("stream_url")


def test_all_content_types_have_episodes_or_download(app, api):
    """SORUN-5: Every content has episodes (or download panel for games)"""
    r = api.get("/api/content?limit=50")
    items = r.json()
    if not items:
        pytest.skip("No content found")
    for item in items:
        cid = item["id"]
        ctype = item["type"]
        r2 = api.get(f"/api/content/{cid}")
        data = r2.json()
        eps = data.get("episodes", [])
        if ctype == "game":
            assert data.get("sites") or eps, f"Game #{cid} has no sites or episodes"
        else:
            assert len(eps) > 0, f"{ctype} #{cid} has zero episodes"


def test_cover_fix_script_ran(app, api):
    """Verify covers were updated by sohbet138_fix_covers.py"""
    import os, json
    report_path = os.path.join(
        os.path.dirname(__file__), "..", "_kanit_sohbet138", "cover_raporu.json"
    )
    if not os.path.isfile(report_path):
        pytest.skip("Cover report not found — run fix script first")
    with open(report_path, encoding="utf-8") as f:
        report = json.load(f)
    assert report["updated"] > 0, "No covers were updated"
    assert report["total"] > 0, "Cover report is empty"
