from system.keyboard_mouse_controller import KeyboardMouseController


class MediaSkill:

    name = "media_control"

    def run(self, params):

        action = params.get("action")

        try:

            if action == "volume_up":
                KeyboardMouseController.press_key("volumeup")

            elif action == "volume_down":
                KeyboardMouseController.press_key("volumedown")

            elif action == "mute":
                KeyboardMouseController.press_key("volumemute")

            elif action == "play_pause":
                KeyboardMouseController.press_key("playpause")

            elif action == "next_track":
                KeyboardMouseController.press_key("nexttrack")

            elif action == "previous_track":
                KeyboardMouseController.press_key("prevtrack")

            else:
                return "error"

            return "success"

        except Exception:
            return "error"
