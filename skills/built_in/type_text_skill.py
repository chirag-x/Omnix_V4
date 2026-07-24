from system.keyboard_mouse_controller import KeyboardMouseController


class TypeTextSkill:

    name = "type_text"

    def run(self, params):

        text = params.get("text")

        if not text:
            return "error"

        KeyboardMouseController.type_text(text)

        return "success"