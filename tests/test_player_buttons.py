"""Simple player button existence test — checks DOM, doesn't require video open"""
import pytest
from playwright.sync_api import expect


def test_player_buttons_exist_in_html(app):
    """All 9 player button IDs exist in the HTML DOM even when player not open"""
    btn_ids = [
        'player-cc-btn', 'player-ambient-btn', 'player-quality-btn',
        'player-episodes-btn', 'player-lock-btn', 'player-capture-btn',
        'player-theater-btn', 'player-pip-btn', 'player-mini-btn'
    ]
    for btn_id in btn_ids:
        count = app.locator(f"#{btn_id}").count()
        assert count == 1, f"Button #{btn_id} should exist exactly once in DOM, found {count}"


def test_player_buttons_have_icons(app):
    """Each player button has a material-symbols-outlined icon child"""
    btn_ids = [
        'player-cc-btn', 'player-ambient-btn', 'player-quality-btn',
        'player-episodes-btn', 'player-lock-btn', 'player-capture-btn',
        'player-theater-btn', 'player-pip-btn', 'player-mini-btn'
    ]
    for btn_id in btn_ids:
        btn = app.locator(f"#{btn_id}")
        icon = btn.locator(".material-symbols-outlined")
        assert icon.count() >= 1, f"Button #{btn_id} missing material icon"


def test_player_buttons_have_title_tooltips(app):
    """Each player button has a title attribute"""
    btn_ids = [
        'player-cc-btn', 'player-ambient-btn', 'player-quality-btn',
        'player-episodes-btn', 'player-lock-btn', 'player-capture-btn',
        'player-theater-btn', 'player-pip-btn', 'player-mini-btn'
    ]
    for btn_id in btn_ids:
        btn = app.locator(f"#{btn_id}")
        title = btn.get_attribute("title")
        assert title and len(title) > 0, f"Button #{btn_id} missing title"
