from __future__ import annotations

import json
import time
from typing import Any, Protocol

from bitfun_uitest.ui import UiElement


class JsExecutor(Protocol):
    def evaluate(self, expression: str) -> Any:
        ...


class DomTestIdMixin:
    def wait_for_test_id(self: JsExecutor, test_id: str, timeout: float = 15.0) -> UiElement:
        deadline = time.monotonic() + timeout
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            try:
                element = self.find_by_test_id(test_id)  # type: ignore[attr-defined]
                if element is not None:
                    return element
            except Exception as error:
                last_error = error
            time.sleep(0.2)

        if last_error:
            raise AssertionError(f"Timed out waiting for data-testid={test_id!r}: {last_error}") from last_error
        raise AssertionError(f"Timed out waiting for data-testid={test_id!r}")

    def find_by_test_id(self: JsExecutor, test_id: str) -> UiElement | None:
        payload = self.evaluate(element_snapshot_script(test_id))
        if payload is None:
            return None
        return UiElement(
            test_id=payload["testId"],
            tag_name=payload["tagName"],
            text=payload["text"],
            value=payload.get("value"),
            visible=bool(payload["visible"]),
            disabled=bool(payload["disabled"]),
            rect=payload["rect"],
        )

    def click_by_test_id(self: JsExecutor, test_id: str) -> None:
        clicked = self.evaluate(
            f"""
            (() => {{
              const el = ({find_element_function()})({json.dumps(test_id)});
              if (!el) return false;
              el.scrollIntoView({{ block: 'center', inline: 'center' }});
              el.click();
              return true;
            }})()
            """
        )
        if not clicked:
            raise AssertionError(f"data-testid={test_id!r} was not found")

    def fill_by_test_id(self: JsExecutor, test_id: str, text: str) -> None:
        updated = self.evaluate(
            f"""
            (() => {{
              const el = ({find_element_function()})({json.dumps(test_id)});
              if (!el) return false;
              el.scrollIntoView({{ block: 'center', inline: 'center' }});
              el.focus();
              const value = {json.dumps(text)};
              if ('value' in el) {{
                el.value = value;
              }} else if (el.isContentEditable) {{
                el.textContent = value;
              }} else {{
                return false;
              }}
              const InputEventCtor = window.InputEvent || Event;
              el.dispatchEvent(new InputEventCtor('input', {{ bubbles: true, inputType: 'insertText', data: value }}));
              el.dispatchEvent(new Event('change', {{ bubbles: true }}));
              return true;
            }})()
            """
        )
        if not updated:
            raise AssertionError(f"data-testid={test_id!r} was not fillable or was not found")


def element_snapshot_script(test_id: str) -> str:
    return f"""
    (() => {{
      const el = ({find_element_function()})({json.dumps(test_id)});
      if (!el) return null;
      const rect = el.getBoundingClientRect();
      const style = window.getComputedStyle(el);
      const value = 'value' in el ? String(el.value ?? '') : null;
      return {{
        testId: {json.dumps(test_id)},
        tagName: String(el.tagName || '').toLowerCase(),
        text: String(el.innerText || el.textContent || '').trim(),
        value,
        visible: Boolean((rect.width || rect.height) && style.display !== 'none' && style.visibility !== 'hidden'),
        disabled: Boolean(el.disabled || el.getAttribute('aria-disabled') === 'true'),
        rect: {{ x: rect.x, y: rect.y, width: rect.width, height: rect.height }}
      }};
    }})()
    """


def find_element_function() -> str:
    return """
    (testId) => {
      const escapeCss = window.CSS && CSS.escape
        ? CSS.escape
        : (value) => String(value).replace(/[\\\"\\\\]/g, '\\\\$&');
      return document.querySelector(`[data-testid="${escapeCss(testId)}"]`);
    }
    """

