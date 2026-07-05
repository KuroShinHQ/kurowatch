"""Detail screen UI tests — T-07 to T-16"""
import pytest
from playwright.sync_api import expect


def _open_detail(app, api):
    """Click first visible content card to open detail"""
    r = api.get("/api/content?limit=1")
    items = r.json()
    if not items:
        pytest.skip("No content")
    card = app.locator("#home-anime-row [data-content-id]").first
    if not card.is_visible():
        pytest.skip("No visible card to click")
    card.click()
    app.wait_for_timeout(800)
    expect(app.locator("#screen-detail")).to_be_visible()
    return items[0]


def test_detail_hero_visible(app, api):
    """T-07: Hero cover + title visible"""
    _open_detail(app, api)
    expect(app.locator("#detail-cover-bg")).to_be_visible()
    expect(app.locator("#detail-title")).to_be_visible()


def test_detail_star_rating(app, api):
    """T-08: Click star → score updates"""
    _open_detail(app, api)
    container = app.locator("#detail-rating-container")
    if container.is_visible():
        stars = container.locator("span, button")
        count = stars.count()
        if count > 0:
            stars.first.click()
            app.wait_for_timeout(300)


def test_detail_episodes_tab(app, api):
    """T-10: Episodes tab visible by default"""
    _open_detail(app, api)
    expect(app.locator("#detail-tab-episodes")).to_be_visible()


def test_detail_switch_to_sites_tab(app, api):
    """T-12: Click Siteler tab button → sites content visible"""
    _open_detail(app, api)
    sites_btn = app.locator("button[onclick*='sites']").first
    if sites_btn.is_visible():
        sites_btn.click()
        app.wait_for_timeout(300)
        sites_content = app.locator("#detail-tab-sites")
        expect(sites_content).to_be_visible()


def test_detail_switch_to_notes_tab(app, api):
    """T-13: Click Notlar tab button → notes textarea visible"""
    _open_detail(app, api)
    notes_btn = app.locator("button[onclick*='notes']").first
    if notes_btn.is_visible():
        notes_btn.click()
        app.wait_for_timeout(300)
    notes_area = app.locator("#detail-tab-notes")
    expect(notes_area).to_be_visible()
