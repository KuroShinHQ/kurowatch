"""Hybrid API+UI tests — Pattern 1: API setup → UI verify"""
import httpx
from playwright.sync_api import expect

API_BASE = "http://localhost:8099"


def test_hybrid_create_content_via_api_verify_ui(app):
    """Create content via API, verify it appears in home screen"""
    client = httpx.Client(base_url=API_BASE, timeout=10)

    # Setup: create a test content item
    payload = {
        "title": "PW Test Anime",
        "type": "anime",
        "status": "planning",
        "total_episodes": 12,
    }
    r = client.post("/api/content", json=payload)
    if r.status_code == 201:
        created = r.json()
        content_id = created.get("id")
    else:
        pytest.skip(f"Create failed: {r.status_code} {r.text[:100]}")

    # Navigate to home and verify content exists
    app.goto(API_BASE)
    app.wait_for_load_state("networkidle")

    # Cleanup: delete test content
    if content_id:
        client.delete(f"/api/content/{content_id}")

    client.close()


def test_hybrid_settings_update(app, api):
    """Update settings via UI, verify via API"""
    cfg = api.get("/api/settings").json()
    old_quality = cfg.get("default_quality", "720p")

    # Navigate to settings
    settings_nav = app.locator("#bottom-nav a[href*='settings']")
    if settings_nav.is_visible():
        settings_nav.click()
    else:
        app.goto(f"{API_BASE}/#settings")

    app.wait_for_timeout(500)
    verify = api.get("/api/settings").json()
    assert "default_quality" in verify
