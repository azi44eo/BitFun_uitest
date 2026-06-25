from __future__ import annotations

import json
import time


def _normalize_attr_name(name: str) -> str:
    return name if name.startswith("data-") else f"data-{name}"


def _normalize_attrs(attrs: dict[str, str] | None) -> dict[str, str]:
    if not attrs:
        return {}
    return {_normalize_attr_name(name): str(value) for name, value in attrs.items()}


def _visible_test_id_payload(ui, test_id: str, attrs: dict[str, str] | None):
    payload = {"testId": test_id, "attrs": _normalize_attrs(attrs)}
    return ui.evaluate(
        f"""
        (() => {{
          const args = {json.dumps(payload, ensure_ascii=True)};
          const isVisible = (el) => {{
            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);
            return Boolean((rect.width || rect.height || el.getClientRects().length) &&
              style.display !== 'none' &&
              style.visibility !== 'hidden');
          }};
          const nodes = Array.from(document.querySelectorAll(`[data-testid="${{args.testId}}"]`));
          const matches = nodes.filter((el) =>
            Object.entries(args.attrs).every(([name, value]) => (el.getAttribute(name) ?? '') === value)
          );
          const visible = matches.filter(isVisible);
          return {{
            totalCount: matches.length,
            visibleCount: visible.length,
            matches: visible.map((el) => ({{
              text: String(el.innerText || el.textContent || '').trim(),
              modelId: el.getAttribute('data-model-id'),
              modelName: el.getAttribute('data-model-name'),
              providerId: el.getAttribute('data-provider-id'),
              optionKind: el.getAttribute('data-option-kind'),
              modelRole: el.getAttribute('data-model-role'),
              modelState: el.getAttribute('data-model-state'),
              status: el.getAttribute('data-status'),
            }})),
          }};
        }})()
        """
    )


def _click_visible_unique_test_id(ui, test_id: str, attrs: dict[str, str] | None):
    payload = {"testId": test_id, "attrs": _normalize_attrs(attrs)}
    return ui.evaluate(
        f"""
        (() => {{
          const args = {json.dumps(payload, ensure_ascii=True)};
          const isVisible = (el) => {{
            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);
            return Boolean((rect.width || rect.height || el.getClientRects().length) &&
              style.display !== 'none' &&
              style.visibility !== 'hidden');
          }};
          const nodes = Array.from(document.querySelectorAll(`[data-testid="${{args.testId}}"]`));
          const matches = nodes.filter((el) =>
            Object.entries(args.attrs).every(([name, value]) => (el.getAttribute(name) ?? '') === value)
          );
          const visible = matches.filter(isVisible);
          if (visible.length !== 1) {{
            return {{
              ok: false,
              totalCount: matches.length,
              visibleCount: visible.length,
              matches: visible.map((el) => ({{
                text: String(el.innerText || el.textContent || '').trim(),
                modelId: el.getAttribute('data-model-id'),
                modelName: el.getAttribute('data-model-name'),
                providerId: el.getAttribute('data-provider-id'),
                optionKind: el.getAttribute('data-option-kind'),
                modelRole: el.getAttribute('data-model-role'),
                modelState: el.getAttribute('data-model-state'),
                status: el.getAttribute('data-status'),
              }})),
            }};
          }}
          const target = visible[0];
          target.scrollIntoView({{ block: 'center', inline: 'center' }});
          target.click();
          return {{ ok: true }};
        }})()
        """
    )


def wait_for_unique_visible_test_id(
    ui,
    test_id: str,
    *,
    attrs: dict[str, str] | None = None,
    timeout: float = 30.0,
    description: str | None = None,
):
    deadline = time.monotonic() + timeout
    last_payload = None
    label = description or f"{test_id} {attrs or {}}"
    while time.monotonic() < deadline:
        last_payload = _visible_test_id_payload(ui, test_id, attrs)
        visible_count = int(last_payload.get("visibleCount") or 0)
        if visible_count == 1:
            return last_payload["matches"][0]
        if visible_count > 1:
            raise AssertionError(
                f"Expected exactly one visible {label}, found {visible_count}: {last_payload['matches']!r}"
            )
        time.sleep(0.2)
    raise AssertionError(f"Timed out waiting for a unique visible {label}; last payload={last_payload!r}")


def click_unique_visible_test_id(
    ui,
    test_id: str,
    *,
    attrs: dict[str, str] | None = None,
    timeout: float = 30.0,
    description: str | None = None,
) -> None:
    deadline = time.monotonic() + timeout
    last_payload = None
    label = description or f"{test_id} {attrs or {}}"
    while time.monotonic() < deadline:
        last_payload = _click_visible_unique_test_id(ui, test_id, attrs)
        if last_payload.get("ok"):
            return
        visible_count = int(last_payload.get("visibleCount") or 0)
        if visible_count > 1:
            raise AssertionError(
                f"Expected exactly one visible clickable {label}, found {visible_count}: {last_payload['matches']!r}"
            )
        time.sleep(0.2)
    raise AssertionError(f"Timed out clicking a unique visible {label}; last payload={last_payload!r}")


def wait_for_visible_chat_model_option(
    ui,
    model_name: str,
    *,
    timeout: float = 30.0,
    provider_id: str | None = None,
    option_kind: str = "model",
):
    attrs = {"option-kind": option_kind, "model-name": model_name}
    if provider_id is not None:
        attrs["provider-id"] = provider_id
    return wait_for_unique_visible_test_id(
        ui,
        "chat-model-selector-option",
        attrs=attrs,
        timeout=timeout,
        description=f"chat model option {attrs!r}",
    )


def click_chat_model_option(
    ui,
    model_name: str,
    *,
    timeout: float = 30.0,
    provider_id: str | None = None,
    option_kind: str = "model",
) -> None:
    attrs = {"option-kind": option_kind, "model-name": model_name}
    if provider_id is not None:
        attrs["provider-id"] = provider_id
    click_unique_visible_test_id(
        ui,
        "chat-model-selector-option",
        attrs=attrs,
        timeout=timeout,
        description=f"chat model option {attrs!r}",
    )


def click_settings_model_option(
    ui,
    model_name: str,
    *,
    timeout: float = 30.0,
    model_state: str = "selectable",
    option_kind: str = "model",
) -> None:
    attrs = {
        "option-kind": option_kind,
        "model-state": model_state,
        "model-name": model_name,
    }
    click_unique_visible_test_id(
        ui,
        "settings-model-option",
        attrs=attrs,
        timeout=timeout,
        description=f"settings model option {attrs!r}",
    )


def wait_for_saved_model_row(ui, model_name: str, *, timeout: float = 30.0):
    return wait_for_unique_visible_test_id(
        ui,
        "settings-model-row",
        attrs={
            "option-kind": "saved-model",
            "model-state": "saved",
            "model-name": model_name,
        },
        timeout=timeout,
        description=f"saved model row for {model_name!r}",
    )


def wait_for_saved_model_status(ui, model_name: str, *, status: str, timeout: float = 120.0):
    return wait_for_unique_visible_test_id(
        ui,
        "settings-model-test-status",
        attrs={
            "option-kind": "saved-model-status",
            "model-state": "saved",
            "model-name": model_name,
            "status": status,
        },
        timeout=timeout,
        description=f"saved model status for {model_name!r} with status={status!r}",
    )


def wait_for_selected_model_draft(ui, model_name: str, *, timeout: float = 30.0):
    return wait_for_unique_visible_test_id(
        ui,
        "settings-model-selected-row",
        attrs={
            "option-kind": "selected-draft",
            "model-state": "draft",
            "model-name": model_name,
        },
        timeout=timeout,
        description=f"selected model draft for {model_name!r}",
    )
