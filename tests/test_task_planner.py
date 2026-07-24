import unittest

from core.command_processor import CommandProcessor
from core.task_planner import TaskPlanner


class FakeBrain:

    def __init__(self, response):
        self.response = response
        self.calls = 0
        self.last_prompt = ""

    def ask(self, prompt):
        self.calls += 1
        self.last_prompt = prompt
        return self.response


class TaskPlannerTests(unittest.TestCase):

    def make_planner(self, response):
        planner = TaskPlanner.__new__(TaskPlanner)
        planner.brain = FakeBrain(response)
        planner.command_processor = CommandProcessor()
        planner.allowed_skills = {
            "hotkey",
            "media_control",
            "open_app",
            "press_key",
            "scroll_page",
            "type_text",
        }
        planner.max_plan_steps = 20
        return planner

    def test_ai_is_used_before_local_fallback(self):
        planner = self.make_planner(
            '[{"skill":"media_control","parameters":{"action":"volume_up"}}]'
        )

        plan = planner.create_plan("turn volume up", {})

        self.assertEqual(1, planner.brain.calls)
        self.assertEqual("media_control", plan[0]["skill"])
        self.assertIn("scroll_page", planner.brain.last_prompt)
        self.assertIn("media_control", planner.brain.last_prompt)

    def test_local_plan_is_only_used_when_ai_is_empty(self):
        planner = self.make_planner(None)

        plan = planner.create_plan("open spotify and play music", {})

        self.assertEqual(1, planner.brain.calls)
        self.assertEqual(
            ["open_app", "media_control"],
            [step["skill"] for step in plan],
        )


if __name__ == "__main__":
    unittest.main()
