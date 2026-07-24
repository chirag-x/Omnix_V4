import pyautogui


class ScrollPageSkill:

    name = "scroll_page"

    def run(self, params):

        direction = params.get("direction", "down")

        if direction == "down":
            pyautogui.scroll(-500)
        elif direction == "up":
            pyautogui.scroll(500)
        else:
            return "error"

        return "success"
