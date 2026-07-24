from system.keyboard_mouse_controller import KeyboardMouseController


class HotkeySkill:

    name = "hotkey"

    def run(self, params):

        keys = params.get("keys")

        if not keys:
            return "error"

        KeyboardMouseController.hotkey(*keys)

        return "success"