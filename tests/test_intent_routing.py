import unittest

from core.command_processor import CommandProcessor
from core.intent_classifier import IntentClassifier


class FakeBrain:

    def __init__(self, response):
        self.response = response
        self.calls = 0

    def ask(self, _prompt):
        self.calls += 1
        return self.response


class IntentRoutingTests(unittest.TestCase):

    def setUp(self):
        self.processor = CommandProcessor()

    def test_explicit_pc_commands_are_automation(self):
        commands = [
            "open chrome",
            "can you close spotify",
            "scroll down",
            "turn volume up",
            "I want you to minimize this window",
        ]

        for command in commands:
            with self.subTest(command=command):
                self.assertTrue(self.processor.looks_like_automation(command))

    def test_conversational_questions_are_not_forced_to_automation(self):
        questions = [
            "how do I open chrome",
            "tell me why spotify is popular",
            "what does scroll mean",
        ]

        for question in questions:
            with self.subTest(question=question):
                self.assertFalse(self.processor.looks_like_automation(question))

    def test_classifier_skips_ai_for_explicit_command(self):
        classifier = IntentClassifier.__new__(IntentClassifier)
        classifier.command_processor = self.processor
        classifier.available_skills = ["open_app"]
        classifier.brain = FakeBrain("chat")

        self.assertEqual("automation", classifier.classify("open chrome"))
        self.assertEqual(0, classifier.brain.calls)

    def test_classifier_uses_ai_for_ambiguous_conversation(self):
        classifier = IntentClassifier.__new__(IntentClassifier)
        classifier.command_processor = self.processor
        classifier.available_skills = ["open_app"]
        classifier.brain = FakeBrain("chat")

        self.assertEqual("chat", classifier.classify("how do I open chrome"))
        self.assertEqual(1, classifier.brain.calls)


if __name__ == "__main__":
    unittest.main()
