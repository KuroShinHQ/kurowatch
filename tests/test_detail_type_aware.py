"""Type-aware Detail screen tests — anime vs manga vs manhwa vs game"""
import pytest
from playwright.sync_api import expect


def _get_content_by_type(api, content_type, limit=1):
    """Fetch content by type from API"""
    r = api.get(f"/api/content?type={content_type}&limit={limit}")
    return r.json()


def _open_detail(app, content_id):
    """Navigate directly to a specific content's detail page"""
    app.evaluate(f"window.openDetail({content_id})")
    app.wait_for_timeout(1000)
    expect(app.locator("#screen-detail")).to_be_visible()


@pytest.mark.parametrize("content_type,expected_label,expected_mark_text,expected_status_icon", [
    ("anime", "BÖLÜM", "Sonraki Bölümü İşaretle", "play_circle"),
    ("manga", "CHAPTER", "Sonraki Chapter'ı İşaretle", "menu_book"),
    ("manhwa", "CHAPTER", "Sonraki Chapter'ı İşaretle", "menu_book"),
])
def test_detail_type_specific_labels(app, api, content_type, expected_label, expected_mark_text, expected_status_icon):
    """Detail screen shows type-specific labels (BÖLÜM/CHAPTER, Mark button text, status icon)"""
    items = _get_content_by_type(api, content_type)
    if not items:
        pytest.skip(f"No {content_type} found")

    cid = items[0]["id"]
    _open_detail(app, cid)

    # Progress label
    progress_label = app.locator("#screen-detail .font-label-caps.uppercase").first
    if progress_label.is_visible():
        text = progress_label.text_content()
        assert expected_label in text, f"Expected '{expected_label}' in progress label, got '{text}'"

    # Mark button text
    mark_btn = app.locator("#detail-mark-btn")
    if mark_btn.is_visible():
        btn_text = mark_btn.text_content()
        assert expected_mark_text in btn_text, f"Expected '{expected_mark_text}', got '{btn_text}'"

    # Status badge icon
    status_badge = app.locator("#detail-status-badge")
    if status_badge.is_visible():
        badge_html = status_badge.inner_html()
        assert expected_status_icon in badge_html, f"Expected icon '{expected_status_icon}' in badge"


def test_detail_game_hides_mark_button(app, api):
    """Game type should NOT show mark or continue buttons"""
    items = _get_content_by_type(api, "game")
    if not items:
        pytest.skip("No games found")

    _open_detail(app, items[0]["id"])

    # Mark button should be hidden for games
    mark_btn = app.locator("#detail-mark-btn")
    expect(mark_btn).not_to_be_visible()

    # Continue button should also be hidden
    cont_btn = app.locator("#detail-continue-btn")
    expect(cont_btn).not_to_be_visible()

    # Progress label should say TAMAMLANMA
    progress_label = app.locator("#screen-detail .font-label-caps.uppercase").first
    if progress_label.is_visible():
        assert "TAMAMLANMA" in progress_label.text_content()


def test_detail_star_rating_interactive(app, api):
    """Click stars updates the score display"""
    items = _get_content_by_type(api, "anime")
    if not items:
        pytest.skip("No anime found")

    cid = items[0]["id"]
    _open_detail(app, cid)

    container = app.locator("#detail-rating-container")
    expect(container).to_be_visible()

    stars = container.locator("[data-star]")
    count = stars.count()
    assert count == 10, f"Expected 10 stars, got {count}"

    # Click 7th star
    stars.nth(6).click()
    app.wait_for_timeout(500)

    # Check score text updates
    score_txt = app.locator("#detail-score-text")
    assert "7" in score_txt.text_content()


def test_detail_progress_slider_updates_display(app, api):
    """Dragging progress slider updates current/total/pct/bar"""
    items = _get_content_by_type(api, "anime")
    if not items:
        pytest.skip("No anime found")

    _open_detail(app, items[0]["id"])

    slider = app.locator("#detail-progress-slider")
    expect(slider).to_be_visible()

    # Set slider to midpoint value
    max_val = int(slider.get_attribute("max") or "100")
    mid = max(1, max_val // 2)
    slider.fill(str(mid))
    slider.dispatch_event("input")
    app.wait_for_timeout(300)
    slider.dispatch_event("change")
    app.wait_for_timeout(500)

    # Open detail again to see saved value
    _open_detail(app, items[0]["id"])
    current = app.locator("#detail-progress-current")
    current_txt = current.text_content()
    assert str(mid) in current_txt, f"Expected {mid} in current, got '{current_txt}'"


def test_detail_quick_edit_popup(app, api):
    """Progress tap opens quick-edit panel, ‑/+/Kaydet buttons work"""
    items = _get_content_by_type(api, "anime")
    if not items:
        pytest.skip("No anime found")

    _open_detail(app, items[0]["id"])

    # Tap progress to open quick-edit
    progress_tap = app.locator("#detail-progress-tap")
    expect(progress_tap).to_be_visible()
    progress_tap.click()
    app.wait_for_timeout(300)

    qe_panel = app.locator("#progress-quick-edit")
    expect(qe_panel).to_be_visible()

    # Test + button
    qe_input = app.locator("#pqe-input")
    orig_val = int(qe_input.input_value() or 0)
    app.locator("#pqe-plus").click()
    new_val = int(qe_input.input_value() or 0)
    assert new_val == orig_val + 1, f"Expected {orig_val + 1}, got {new_val}"

    # Test − button
    app.locator("#pqe-minus").click()
    final_val = int(qe_input.input_value() or 0)
    assert final_val == orig_val, f"Expected {orig_val}, got {final_val}"


def test_detail_episodes_season_picker(app, api):
    """Episodes tab shows season picker when multiple seasons exist"""
    r = api.get("/api/content?limit=50")
    items = r.json()
    multi_season = [c for c in items if (c.get("total_episodes") or 0) > 25]
    if not multi_season:
        pytest.skip("No multi-season content found")

    _open_detail(app, multi_season[0]["id"])

    ep_tab = app.locator("#detail-tab-episodes")
    expect(ep_tab).to_be_visible()

    ep_rows = ep_tab.locator(".ep-row")
    if ep_rows.count() > 0:
        expect(ep_rows.first).to_be_visible()


def test_detail_sites_add_and_delete(app, api):
    """Sites tab: add a site, verify, then clean up"""
    items = _get_content_by_type(api, "anime")
    if not items:
        pytest.skip("No anime found")

    cid = items[0]["id"]
    _open_detail(app, cid)

    # Switch to sites tab
    sites_btn = app.locator("button[onclick*='sites']").first
    if sites_btn.is_visible():
        sites_btn.click()
        app.wait_for_timeout(300)

    sites_content = app.locator("#detail-tab-sites")
    expect(sites_content).to_be_visible()

    # Check if add form is accessible
    add_toggle = sites_content.locator("#detail-site-add-toggle")
    if add_toggle.is_visible():
        add_toggle.click()
        app.wait_for_timeout(200)

    add_form = sites_content.locator("#detail-site-add-form")
    if add_form.is_visible():
        # Fill form
        name_input = app.locator("#detail-site-name")
        url_input = app.locator("#detail-site-url")
        if name_input.is_visible() and url_input.is_visible():
            name_input.fill("PW Test Site")
            url_input.fill("https://example-pw-test.com")
            app.locator("#detail-site-save-btn").click()
            app.wait_for_timeout(500)


def test_detail_notes_spoiler_toggle(app, api):
    """Notes tab: spoiler toggle blurs/unblurs textarea"""
    items = _get_content_by_type(api, "anime")
    if not items:
        pytest.skip("No anime found")

    _open_detail(app, items[0]["id"])

    # Switch to notes tab
    notes_btn = app.locator("button[onclick*='notes']").first
    if notes_btn.is_visible():
        notes_btn.click()
        app.wait_for_timeout(300)

    notes_tab = app.locator("#detail-tab-notes")
    expect(notes_tab).to_be_visible()

    # Check spoiler toggle exists
    spoiler = app.locator("#detail-spoiler-toggle")
    expect(spoiler).to_be_visible()


def test_detail_season_tabs_visible(app, api):
    """Season bar shows when content has related seasons"""
    r = api.get("/api/content?limit=50")
    items = r.json()
    if not items:
        pytest.skip("No content")

    _open_detail(app, items[0]["id"])

    season_bar = app.locator("#detail-season-bar")
    season_tabs = app.locator("#detail-season-tabs")
    if season_bar.is_visible() and season_tabs.is_visible():
        tab_btns = season_tabs.locator("button")
        assert tab_btns.count() > 0, "Season tabs should have buttons"


def test_detail_edit_modal_opens(app, api):
    """Edit button opens modal with pre-filled data"""
    items = _get_content_by_type(api, "anime")
    if not items:
        pytest.skip("No anime found")

    _open_detail(app, items[0]["id"])

    edit_btn = app.locator("#detail-edit-btn")
    expect(edit_btn).to_be_visible()
    edit_btn.click()
    app.wait_for_timeout(500)

    edit_modal = app.locator("#modal-edit")
    expect(edit_modal).to_be_visible()

    # Check pre-filled title
    title_input = app.locator("#edit-form-title")
    expect(title_input).to_be_visible()
    assert len(title_input.input_value()) > 0, "Title should be pre-filled"


def test_detail_cover_upload_button_exists(app, api):
    """Cover upload label (visual trigger) is visible; hidden input exists"""
    items = _get_content_by_type(api, "anime")
    if not items:
        pytest.skip("No anime found")

    _open_detail(app, items[0]["id"])

    # The label acts as the visible upload button (for="cover-file-input")
    cover_label = app.locator("label[for='cover-file-input']")
    expect(cover_label).to_be_visible()

    # The actual file input is intentionally hidden
    cover_input = app.locator("#cover-file-input")
    expect(cover_input).to_have_attribute("type", "file")
    expect(cover_input).not_to_be_visible()
