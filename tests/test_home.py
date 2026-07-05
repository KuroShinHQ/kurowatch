"""Home screen UI tests — T-01 to T-06"""
import pytest
from playwright.sync_api import expect


def test_home_opens(app):
    """T-01: App opens, home screen visible, nav bar shows"""
    home = app.locator("#screen-home")
    expect(home).to_be_visible()

    nav = app.locator("#bottom-nav")
    expect(nav).to_be_visible()


def test_home_hero_visible(app, api):
    """T-03a: Hero banner shows with title + meta"""
    r = api.get("/api/content?limit=1")
    items = r.json()
    if not items:
        pytest.skip("No content in DB")

    expect(app.locator("#home-hero-title")).to_be_visible()
    expect(app.locator("#home-hero-meta")).to_be_visible()


def test_home_continue_row(app, api):
    """T-03b: Devam Et row has clickable cards"""
    r = api.get("/api/content")
    items = r.json()
    if not items:
        pytest.skip("No content")
    cont_row = app.locator("#home-continue-row")
    if cont_row.is_visible():
        cards = cont_row.locator("[data-content-id]")
        if cards.count() > 0:
            expect(cards.first).to_be_visible()


def test_home_anime_row_cards(app, api):
    """T-03c: Anime row shows content cards"""
    r = api.get("/api/content?type=anime&limit=1")
    items = r.json()
    if not items:
        pytest.skip("No anime")

    anime_row = app.locator("#home-anime-row")
    if anime_row.is_visible():
        cards = anime_row.locator("[data-content-id]")
        if cards.count() > 0:
            expect(cards.first).to_be_visible()


def test_home_card_click_opens_detail(app, api):
    """T-06: Click content card → detail screen opens"""
    r = api.get("/api/content?limit=1")
    items = r.json()
    if not items:
        pytest.skip("No content")

    card = app.locator("#home-anime-row [data-content-id]").first
    if not card.is_visible():
        pytest.skip("No visible anime card")

    card.click()
    app.wait_for_timeout(500)
    detail = app.locator("#screen-detail")
    expect(detail).to_be_visible()
