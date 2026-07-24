from system.keyboard_mouse_controller import KeyboardMouseController


class PressKeySkill:

    name = "press_key"

    def run(self, params):

        key = params.get("key")

        if not key:
            return "error"

        KeyboardMouseController.press_key(key)

        return "success"