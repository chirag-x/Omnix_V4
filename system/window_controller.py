import re

import pygetwindow as gw
from loguru import logger


class WindowController:

    @staticmethod
    def get_active_window():

        try:
            window = gw.getActiveWindow()
        except Exception as e:
            logger.debug(f"Unable to read active window: {e}")
            return "unknown"

        if window:

            return window.title

        return "unknown"

    @staticmethod
    def focus_window(title=None):

        window = WindowController._find_window(title)

        if not window:
            logger.warning(f"Window not found for focus: {title}")
            return "error"

        try:
            logger.info(f"Focusing window: {window.title}")

            if getattr(window, "isMinimized", False):
                window.restore()

            window.activate()
            return "success"
        except Exception as e:
            logger.warning(f"Unable to focus window '{window.title}': {e}")
            return "error"

    @staticmethod
    def minimize_window(title=None):

        return WindowController._run_window_action(
            title,
            "minimize",
            lambda window: window.minimize(),
        )

    @staticmethod
    def maximize_window(title=None):

        return WindowController._run_window_action(
            title,
            "maximize",
            lambda window: window.maximize(),
        )

    @staticmethod
    def restore_window(title=None):

        return WindowController._run_window_action(
            title,
            "restore",
            lambda window: window.restore(),
        )

    @staticmethod
    def close_window(title=None):

        return WindowController._run_window_action(
            title,
            "close",
            lambda window: window.close(),
        )

    @staticmethod
    def _run_window_action(title, action_name, callback):

        window = WindowController._find_window(title)

        if not window:
            logger.warning(f"Window not found for {action_name}: {title}")
            return "error"

        try:
            logger.info(f"{action_name.capitalize()} window: {window.title}")
            callback(window)
            return "success"
        except Exception as e:
            logger.warning(
                f"Unable to {action_name} window '{window.title}': {e}"
            )
            return "error"

    @staticmethod
    def _find_window(title=None):

        if not title:
            try:
                return gw.getActiveWindow()
            except Exception as e:
                logger.debug(f"Unable to get active window: {e}")
                return None

        title = str(title).strip()

        if not title:
            return None

        try:
            windows = gw.getAllWindows()
        except Exception as e:
            logger.debug(f"Unable to list windows: {e}")
            windows = []

        ranked = []

        for window in windows:
            window_title = getattr(window, "title", "")

            if not window_title:
                continue

            score = WindowController._match_score(title, window_title)

            if score > 0:
                ranked.append((score, window))

        if ranked:
            ranked.sort(key=lambda item: item[0], reverse=True)
            return ranked[0][1]

        try:
            matches = gw.getWindowsWithTitle(title)
        except Exception:
            matches = []

        return matches[0] if matches else None

    @staticmethod
    def _match_score(target, value):

        target = WindowController._normalize(target)
        value = WindowController._normalize(value)

        if not target or not value:
            return 0

        if target == value:
            return 100

        if target in value or value in target:
            return 80

        target_tokens = set(target.split())
        value_tokens = set(value.split())

        if target_tokens and target_tokens.issubset(value_tokens):
            return 70

        overlap = len(target_tokens & value_tokens)

        if overlap:
            return 40 + (20 * overlap / max(len(target_tokens), 1))

        return 0

    @staticmethod
    def _normalize(value):

        value = str(value or "").lower()
        value = re.sub(r"[^a-z0-9]+", " ", value)
        return re.sub(r"\s+", " ", value).strip()
