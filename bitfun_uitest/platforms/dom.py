from __future__ import annotations

import json
import time
from typing import Any, Mapping, Protocol

from bitfun_uitest.ui import UiElement


class JsExecutor(Protocol):
    def evaluate(self, expression: str) -> Any:
        ...


class DomTestIdMixin:
    def wait_for_test_id(
        self: JsExecutor,
        test_id: str,
        timeout: float = 15.0,
        attrs: Mapping[str, str] | None = None,
    ) -> UiElement:
        deadline = time.monotonic() + timeout
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            try:
                element = self.find_by_test_id(test_id, attrs=attrs)  # type: ignore[attr-defined]
                if element is not None:
                    return element
            except Exception as error:
                last_error = error
            time.sleep(0.2)

        locator = format_locator(test_id, attrs)
        if last_error:
            raise AssertionError(f"Timed out waiting for {locator}: {last_error}") from last_error
        raise AssertionError(f"Timed out waiting for {locator}")

    def wait_for_test_id_gone(self: JsExecutor, test_id: str, timeout: float = 15.0) -> None:
        deadline = time.monotonic() + timeout
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            try:
                if self.find_by_test_id(test_id) is None:  # type: ignore[attr-defined]
                    return
            except Exception as error:
                last_error = error
            time.sleep(0.2)

        if last_error:
            raise AssertionError(f"Timed out waiting for data-testid={test_id!r} to disappear: {last_error}") from last_error
        raise AssertionError(f"Timed out waiting for data-testid={test_id!r} to disappear")

    def find_by_test_id(self: JsExecutor, test_id: str, attrs: Mapping[str, str] | None = None) -> UiElement | None:
        payload = self.evaluate(element_snapshot_script(test_id, attrs))
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
            attributes=payload["attributes"],
        )

    def click_by_test_id(self: JsExecutor, test_id: str, attrs: Mapping[str, str] | None = None) -> None:
        clicked = self.evaluate(
            f"""
            (() => {{
              const el = ({find_element_function()})({json.dumps(test_id)}, {json.dumps(dict(attrs or {}))});
              if (!el) return false;
              el.scrollIntoView({{ block: 'center', inline: 'center' }});
              const rect = el.getBoundingClientRect();
              const x = rect.left + rect.width / 2;
              const y = rect.top + rect.height / 2;
              const target = document.elementFromPoint(x, y);
              const clickTarget = target && el.contains(target) ? target : el;
              for (const type of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) {{
                clickTarget.dispatchEvent(new MouseEvent(type, {{
                  bubbles: true,
                  cancelable: true,
                  view: window,
                  clientX: x,
                  clientY: y,
                }}));
              }}
              return true;
            }})()
            """
        )
        if not clicked:
            raise AssertionError(f"{format_locator(test_id, attrs)} was not found")

    def fill_by_test_id(self: JsExecutor, test_id: str, text: str, attrs: Mapping[str, str] | None = None) -> None:
        updated = self.evaluate(
            f"""
            (() => {{
              const el = ({find_element_function()})({json.dumps(test_id)}, {json.dumps(dict(attrs or {}))});
              if (!el) return false;
              el.scrollIntoView({{ block: 'center', inline: 'center' }});
              el.focus();
              const value = {json.dumps(text)};
              if ('value' in el) {{
                const prototype = el.tagName === 'TEXTAREA'
                  ? window.HTMLTextAreaElement.prototype
                  : window.HTMLInputElement.prototype;
                const valueSetter = Object.getOwnPropertyDescriptor(prototype, 'value')?.set;
                if (valueSetter) {{
                  valueSetter.call(el, value);
                }} else {{
                  el.value = value;
                }}
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
            raise AssertionError(f"{format_locator(test_id, attrs)} was not fillable or was not found")


def element_snapshot_script(test_id: str, attrs: Mapping[str, str] | None = None) -> str:
    return f"""
    (() => {{
      const el = ({find_element_function()})({json.dumps(test_id)}, {json.dumps(dict(attrs or {}))});
      if (!el) return null;
      const rect = el.getBoundingClientRect();
      const style = window.getComputedStyle(el);
      const value = 'value' in el ? String(el.value ?? '') : null;
      const attributes = {{}};
      for (const attr of el.attributes || []) {{
        if (attr.name.startsWith('data-')) attributes[attr.name] = attr.value;
      }}
      return {{
        testId: {json.dumps(test_id)},
        tagName: String(el.tagName || '').toLowerCase(),
        text: String(el.innerText || el.textContent || '').trim(),
        value,
        visible: Boolean((rect.width || rect.height) && style.display !== 'none' && style.visibility !== 'hidden'),
        disabled: Boolean(el.disabled || el.getAttribute('aria-disabled') === 'true'),
        rect: {{ x: rect.x, y: rect.y, width: rect.width, height: rect.height }},
        attributes
      }};
    }})()
    """


def find_element_function() -> str:
    return """
    (testId, attrs = {}) => {
      const escapeCss = window.CSS && CSS.escape
        ? CSS.escape
        : (value) => String(value).replace(/[\\\"\\\\]/g, '\\\\$&');
      const dataAttrName = (name) => String(name).startsWith('data-') ? String(name) : `data-${name}`;
      const candidates = document.querySelectorAll(`[data-testid="${escapeCss(testId)}"]`);
      const matches = Array.from(candidates).filter((el) =>
        Object.entries(attrs || {}).every(([name, value]) =>
          el.getAttribute(dataAttrName(name)) === String(value)
        )
      );
      const isVisible = (el) => {
        const rect = el.getBoundingClientRect();
        const style = window.getComputedStyle(el);
        return Boolean((rect.width || rect.height || el.getClientRects().length) &&
          style.display !== 'none' &&
          style.visibility !== 'hidden');
      };
      return matches.find(isVisible) || matches[0] || null;
    }
    """


def format_locator(test_id: str, attrs: Mapping[str, str] | None = None) -> str:
    if not attrs:
        return f"data-testid={test_id!r}"
    suffix = ", ".join(f"data-{key.removeprefix('data-')}={value!r}" for key, value in attrs.items())
    return f"data-testid={test_id!r} ({suffix})"
