from system.ui_controller import UIController


class WaitForUISkill:

    name = "wait_for_ui"

    def __init__(self, vision_manager=None, ui_controller=None, **_deps):

        self.controller = ui_controller or UIController(vision_manager)

    def run(self, params):

        target = params.get("target") or params.get("text")

        if not target:
            return "error"

        return self.controller.wait_for(
            target=target,
            state=params.get("state", "visible"),
            control_type=params.get("control_type"),
            window_title=params.get("window") or params.get("window_title"),
            timeout=params.get("timeout", 10),
        )
