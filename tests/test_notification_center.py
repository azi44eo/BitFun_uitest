from __future__ import annotations


def test_notification_center_opens_and_closes(ui):
    button = ui.wait_for_test_id("notification-button")
    assert button.visible

    ui.click_by_test_id("notification-button")

    center = ui.wait_for_test_id("notification-center")
    assert center.visible

    ui.click_by_test_id("notification-center-close-btn")

    ui.wait_for_test_id_gone("notification-center")
