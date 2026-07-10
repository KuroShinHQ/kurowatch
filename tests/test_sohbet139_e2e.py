"""SOHBET-139 E2E tests — manga DNS fix + series/movie/cartoon download buttons"""
import pytest
from playwright.sync_api import expect


def _find_content_with_missing_ep_urls(api, ctype, limit=50):
    """Find a content of given type that has sites but episodes without URLs."""
    r = api.get(f"/api/content?type={ctype}&limit={limit}")
    items = r.json()
    for item in items:
        cid = item["id"]
        r2 = api.get(f"/api/content/{cid}")
        data = r2.json()
        eps = data.get("episodes", [])
        sites = data.get("sites", [])
        missing = [e for e in eps if not e.get("url")]
        if sites and missing:
            return data
    return None


@pytest.fixture
def dexter(api):
    """Fixture: fetch Dexter (or similar series) with site but no ep URLs."""
    r = api.get("/api/content/287")
    if r.status_code == 200:
        data = r.json()
        eps = data.get("episodes", [])
        sites = data.get("sites", [])
        has_any_url = any(e.get("url") for e in eps)
        if sites and not has_any_url:
            return data
    return _find_content_with_missing_ep_urls(api, "series")


# ── SORUN 1: mangaokutr.com DNS fix ──────────────────────────────────


def test_mangaokutr_urls_fixed(api):
    """SORUN-1: DB'de hiçbir episode URL'i mangaokutr.com içermemeli."""
    r = api.get("/api/content?limit=200")
    items = r.json()
    found = 0
    checked = 0
    for item in items:
        if item["type"] not in ("manga", "manhwa"):
            continue
        cid = item["id"]
        r2 = api.get(f"/api/content/{cid}")
        data = r2.json()
        for ep in data.get("episodes", []):
            checked += 1
            if ep.get("url") and "mangaokutr.com" in ep["url"]:
                found += 1
    print(f"  checked {checked} episodes")
    assert found == 0, f"{found} episodes still have mangaokutr.com URLs"


# ── SORUN 2+3: Series/movie/cartoon download buttons ─────────────────


def test_series_ep_dl_buttons_with_fallback(app, api, dexter):
    """SORUN-2+3: Series ep without URL shows ep-dl-btn via primarySite fallback."""
    if not dexter:
        pytest.skip("No suitable series content found (needs sites + URL-less eps)")
    cid = dexter["id"]
    app.evaluate(f"window.openDetail({cid})")
    app.wait_for_timeout(1500)
    expect(app.locator("#screen-detail")).to_be_visible()

    dl_btns = app.locator(".ep-dl-btn")
    count = dl_btns.count()
    assert count > 0, f"Series #{cid}: no ep-dl-btn found (expected via primarySite fallback)"

    overlay_btns = app.locator(".ep-overlay-btn")
    assert overlay_btns.count() > 0, f"Series #{cid}: no ep-overlay-btn"

    stream_btns = app.locator(".ep-stream-btn")
    assert stream_btns.count() > 0, f"Series #{cid}: no ep-stream-btn"

    first_btn = dl_btns.first
    ep_url = first_btn.get_attribute("data-ep-url")
    assert ep_url and ep_url.startswith("http"), f"data-ep-url missing/invalid: {ep_url}"

    primary_site = (dexter.get("sites") or [None])[0]
    if primary_site:
        assert primary_site["site_url"] in ep_url, (
            f"ep-url '{ep_url}' should contain site_url '{primary_site['site_url']}'"
        )


def test_movie_ep_dl_buttons_with_fallback(app, api):
    """SORUN-2+3: Movie ep without URL shows ep-dl-btn via primarySite fallback."""
    target = _find_content_with_missing_ep_urls(api, "movie")
    if not target:
        pytest.skip("No suitable movie content found")
    cid = target["id"]
    app.evaluate(f"window.openDetail({cid})")
    app.wait_for_timeout(1500)
    expect(app.locator("#screen-detail")).to_be_visible()

    dl_btns = app.locator(".ep-dl-btn")
    assert dl_btns.count() > 0, f"Movie #{cid}: no ep-dl-btn"

    overlay_btns = app.locator(".ep-overlay-btn")
    assert overlay_btns.count() > 0, f"Movie #{cid}: no ep-overlay-btn"


def test_cartoon_ep_dl_buttons_with_fallback(app, api):
    """SORUN-2+3: Cartoon ep without URL shows ep-dl-btn via primarySite fallback."""
    target = _find_content_with_missing_ep_urls(api, "cartoon")
    if not target:
        pytest.skip("No suitable cartoon content found")
    cid = target["id"]
    app.evaluate(f"window.openDetail({cid})")
    app.wait_for_timeout(1500)
    expect(app.locator("#screen-detail")).to_be_visible()

    dl_btns = app.locator(".ep-dl-btn")
    assert dl_btns.count() > 0, f"Cartoon #{cid}: no ep-dl-btn"

    overlay_btns = app.locator(".ep-overlay-btn")
    assert overlay_btns.count() > 0, f"Cartoon #{cid}: no ep-overlay-btn"


def test_episode_url_coverage_report(api):
    """SORUN-2+3: Rapor — her tip için URL coverage yüzdesi."""
    import json
    report = {}
    for ctype in ("anime", "series", "movie", "cartoon", "manga", "manhwa"):
        r = api.get(f"/api/content?type={ctype}&limit=100")
        items = r.json()
        total_eps = 0
        url_eps = 0
        for item in items:
            cid = item["id"]
            r2 = api.get(f"/api/content/{cid}")
            data = r2.json()
            for ep in data.get("episodes", []):
                total_eps += 1
                if ep.get("url"):
                    url_eps += 1
        pct = round(url_eps / total_eps * 100, 1) if total_eps else 0
        report[ctype] = {"total": total_eps, "with_urls": url_eps, "pct": pct}
        print(f"  {ctype}: {url_eps}/{total_eps} ({pct}%)")
    # Series/movie/cartoon must have >0 episodes (verification data exists)
    for ctype in ("series", "movie", "cartoon"):
        assert report[ctype]["total"] > 0, f"{ctype}: no episodes found in report"
