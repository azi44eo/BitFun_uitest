from __future__ import annotations


def test_settings_opens_from_footer_menu(ui):
    ui.click_by_test_id("nav-footer-more-btn")

    menu = ui.wait_for_test_id("nav-footer-menu")
    assert menu.visible

    ui.click_by_test_id("nav-footer-settings-item")

    settings = ui.wait_for_test_id("settings-scene")
    assert settings.visible

    nav = ui.wait_for_test_id("settings-nav")
    assert nav.visible

    content = ui.wait_for_test_id("settings-scene-content")
    assert content.visible

