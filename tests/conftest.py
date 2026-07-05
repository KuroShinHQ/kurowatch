"""Playwright hybrid test fixtures — API + UI shared state"""
import json
import pytest
import httpx
from playwright.sync_api import sync_playwright

API_BASE = "http://localhost:8099"


@pytest.fixture(scope="session")
def api():
    """Direct API client for test setup & verification"""
    with httpx.Client(base_url=API_BASE, timeout=10) as client:
        yield client


@pytest.fixture(scope="session")
def browser():
    """Single browser instance — each test gets isolated context"""
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        yield b
        b.close()


@pytest.fixture
def app(browser, api):
    """Authenticated page with fresh context + API verification"""
    ctx = browser.new_context(viewport={"width": 390, "height": 844})
    page = ctx.new_page()

    # Health check — backend ayakta mı?
    try:
        r = api.get("/api/content?limit=1")
        assert r.status_code == 200, f"Backend down: {r.status_code}"
    except Exception as e:
        pytest.fail(f"Backend unreachable: {e}")

    page.goto(API_BASE)
    page.wait_for_load_state("networkidle")
    yield page
    ctx.close()
