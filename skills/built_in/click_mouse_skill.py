from system.keyboard_mouse_controller import KeyboardMouseController


class ClickMouseSkill:

    name = "click_mouse"

    def run(self, params):

        x = params.get("x")
        y = params.get("y")

        KeyboardMouseController.click(x, y)

        return "success"