from system.keyboard_mouse_controller import KeyboardMouseController


class RightClickSkill:

    name = "right_click"

    def run(self, params):

        x = params.get("x")
        y = params.get("y")

        KeyboardMouseController.right_click(x, y)

        return "success"