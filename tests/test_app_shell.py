from __future__ import annotations


def test_app_shell_loads(ui):
    app = ui.wait_for_test_id("app-layout")
    assert app.visible

    main = ui.wait_for_test_id("app-main-content")
    assert main.visible

    nav = ui.wait_for_test_id("nav-panel")
    assert nav.visible

