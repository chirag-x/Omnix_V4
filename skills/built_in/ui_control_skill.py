from loguru import logger

from system.ui_controller import UIController


class UIControlSkill:

    name = "ui_control"

    def __init__(self, vision_manager=None, ui_controller=None, **_deps):

        self.controller = ui_controller or UIController(vision_manager)

    def run(self, params):

        action = params.get("action", "click")
        target = params.get("target") or params.get("text")
        value = params.get("value")
        control_type = params.get("control_type")
        index = int(params.get("index", 0))
        window_title = params.get("window") or params.get("window_title")

        if not target and action not in {"set_text", "type"}:
            logger.warning("ui_control called without target")
            return "error"

        return self.controller.perform(
            action=action,
            target=target,
            value=value,
            control_type=control_type,
            index=index,
            window_title=window_title,
        )
