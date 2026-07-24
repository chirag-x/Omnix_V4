from system.keyboard_mouse_controller import KeyboardMouseController


class DragMouseSkill:

    name = "drag_mouse"

    def run(self, params):

        x1 = params.get("x1")
        y1 = params.get("y1")
        x2 = params.get("x2")
        y2 = params.get("y2")

        if None in [x1, y1, x2, y2]:
            return "error"

        KeyboardMouseController.drag(x1, y1, x2, y2)

        return "success"