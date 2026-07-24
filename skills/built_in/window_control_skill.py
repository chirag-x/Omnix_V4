from loguru import logger

from system.window_controller import WindowController


class WindowControlSkill:

    name = "window_control"

    def run(self, params):

        action = str(params.get("action") or "").lower()
        title = params.get("title") or params.get("window")

        actions = {
            "focus": WindowController.focus_window,
            "switch": WindowController.focus_window,
            "minimize": WindowController.minimize_window,
            "maximize": WindowController.maximize_window,
            "restore": WindowController.restore_window,
            "close": WindowController.close_window,
        }

        handler = actions.get(action)

        if handler is None:
            logger.warning(f"Unknown window action: {action}")
            return "error"

        return handler(title)
