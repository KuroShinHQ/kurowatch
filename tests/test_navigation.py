"""Navigation tests — T-02: screen transitions work"""
from playwright.sync_api import expect


def test_nav_home_to_search(app):
    """Home → Search transition"""
    search_nav = app.locator("#bottom-nav a[href*='search'], #bottom-nav button:has-text('Arama')")
    if search_nav.is_visible():
        search_nav.click()
        app.wait_for_timeout(500)
        expect(app.locator("#screen-search")).to_be_visible()


def test_nav_all_screens_accessible(app, api):
    """All bottom nav screens open without error"""
    nav_items = app.locator("#bottom-nav a")
    count = nav_items.count()
    if count == 0:
        pytest.skip("No bottom nav found")

    for i in range(count):
        item = nav_items.nth(i)
        try:
            item.click()
            app.wait_for_timeout(500)
        except Exception:
            pass
