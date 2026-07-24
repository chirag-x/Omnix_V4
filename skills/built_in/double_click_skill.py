from system.keyboard_mouse_controller import KeyboardMouseController


class DoubleClickSkill:

    name = "double_click"

    def run(self, params):

        x = params.get("x")
        y = params.get("y")

        KeyboardMouseController.double_click(x, y)

        return "success"