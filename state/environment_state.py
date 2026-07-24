from loguru import logger


class EnvironmentState:

    def __init__(self):

        logger.info("Initializing Environment State")

        self.state = {
            "active_window": None,
            "active_app": None,
            "ui_elements": [],
            "last_action": None,
            "last_result": None
        }

    def update(self, system_context, vision_data):

        if system_context:

            self.state["active_window"] = system_context.get("active_window")
            self.state["active_app"] = system_context.get("active_app")

        if vision_data:

            self.state["ui_elements"] = vision_data.get("ui_elements", [])

    def set_action_feedback(self, action, result):

        self.state["last_action"] = action
        self.state["last_result"] = result

    def get_state(self):

        return self.state
