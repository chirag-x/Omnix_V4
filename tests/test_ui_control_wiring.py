import unittest

from core.command_processor import CommandProcessor
from skills.skill_manager import SkillManager
from system.ui_controller import UIController


class FakeInfo:

    def __init__(self, control_type="Button", automation_id=""):
        self.control_type = control_type
        self.automation_id = automation_id
        self.class_name = control_type
        self.name = ""


class FakeRect:

    left = 10
    top = 20
    right = 110
    bottom = 60


class FakeControl:

    def __init__(self, text, control_type="Button"):
        self._text = text
        self.element_info = FakeInfo(control_type)
        self.clicked = False
        self.value = None

    def window_text(self):
        return self._text

    def is_visible(self):
        return True

    def rectangle(self):
        return FakeRect()

    def click_input(self, button="left"):
        self.clicked = button

    def set_edit_text(self, value):
        self.value = value


class FakeRoot:

    def __init__(self, controls):
        self.controls = controls

    def descendants(self, control_type=None):
        if control_type:
            return [
                control for control in self.controls
                if control.element_info.control_type == control_type
            ]
        return self.controls


class FakeUIController(UIController):

    def __init__(self, controls):
        super().__init__(None)
        self.root = FakeRoot(controls)

    def _get_window(self, window_title=None):
        return self.root


class UIControlWiringTests(unittest.TestCase):

    def test_ui_controller_clicks_fuzzy_native_control(self):
        save_button = FakeControl("Save changes")
        controller = FakeUIController([save_button])

        result = controller.click("save")

        self.assertEqual("success", result)
        self.assertEqual("left", save_button.clicked)

    def test_ui_controller_sets_text_in_native_edit(self):
        search_box = FakeControl("Search", "Edit")
        controller = FakeUIController([search_box])

        result = controller.set_text("hello world", target="search")

        self.assertEqual("success", result)
        self.assertEqual("hello world", search_box.value)

    def test_skill_manager_loads_ui_skills_with_dependencies(self):
        fake_controller = object()
        manager = SkillManager({"ui_controller": fake_controller})

        for skill_name in ("click_ui", "ui_control", "wait_for_ui", "window_control"):
            self.assertIn(skill_name, manager.skills)

    def test_local_fallback_handles_chained_browser_search(self):
        processor = CommandProcessor()

        plan = processor.create_simple_plan(
            "open chrome and search for python docs"
        )

        self.assertEqual(
            ["open_app", "browser_action"],
            [step["skill"] for step in plan],
        )
        self.assertEqual("search", plan[1]["parameters"]["action"])
        self.assertEqual("python docs", plan[1]["parameters"]["query"])


if __name__ == "__main__":
    unittest.main()
