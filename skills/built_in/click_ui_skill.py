from loguru import logger

from system.keyboard_mouse_controller import KeyboardMouseController
from system.ui_controller import UIController


class ClickUISkill:

    name = "click_ui"

    def __init__(self, vision_manager=None, ui_controller=None, **_deps):

        self.controller = ui_controller or UIController(vision_manager)

    def run(self, params):

        x = params.get("x")
        y = params.get("y")

        if x is not None and y is not None:
            logger.info(f"Clicking UI coordinates: ({x},{y})")
            KeyboardMouseController.click(int(x), int(y))
            return "success"

        target = params.get("text") or params.get("target")

        if not target:
            logger.warning("click_ui called without target text or coordinates")
            return "error"

        return self.controller.click(
            target=target,
            control_type=params.get("control_type"),
            index=int(params.get("index", 0)),
            window_title=params.get("window") or params.get("window_title"),
            button=params.get("button", "left"),
            double=bool(params.get("double", False)),
        )
