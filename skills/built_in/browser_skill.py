import webbrowser

from system.app_controller import AppController
from system.keyboard_mouse_controller import KeyboardMouseController


class BrowserSkill:

    name = "browser_action"

    def run(self, params):

        action = str(params.get("action") or "open_browser").lower()
        browser = params.get("browser") or "chrome"

        if action in {"open", "open_browser"}:
            return AppController.open_app(browser)

        if action in {"open_url", "navigate", "go_to"}:
            url = params.get("url")
            if not url:
                return "error"
            url = self._normalize_url(url)
            webbrowser.open(url)
            return "success"

        if action == "search":
            query = params.get("query") or params.get("text")
            if not query:
                return "error"
            AppController.open_app(browser)
            KeyboardMouseController.hotkey("ctrl", "l")
            KeyboardMouseController.type_text(str(query))
            KeyboardMouseController.press_key("enter")
            return "success"

        hotkeys = {
            "back": ("alt", "left"),
            "forward": ("alt", "right"),
            "refresh": ("ctrl", "r"),
            "hard_refresh": ("ctrl", "shift", "r"),
            "new_tab": ("ctrl", "t"),
            "close_tab": ("ctrl", "w"),
            "next_tab": ("ctrl", "tab"),
            "previous_tab": ("ctrl", "shift", "tab"),
            "focus_address": ("ctrl", "l"),
        }

        keys = hotkeys.get(action)

        if keys:
            KeyboardMouseController.hotkey(*keys)
            return "success"

        return "error"

    def _normalize_url(self, url):

        url = str(url).strip()

        if not url:
            return url

        if "://" not in url and not url.startswith("about:"):
            return f"https://{url}"

        return url
