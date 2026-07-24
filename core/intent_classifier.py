from ai.brain_manager import BrainManager


class IntentClassifier:

    def __init__(self, command_processor=None, available_skills=None):

        self.brain = BrainManager()
        self.command_processor = command_processor
        self.available_skills = sorted(available_skills or [])

    def classify(self, text):

        if self.command_processor and self.command_processor.looks_like_automation(text):
            return "automation"

        skill_text = ", ".join(self.available_skills) or "desktop control skills"

        prompt = f"""
You are the intent router for Omnix, a conversational Windows AI assistant.

Classify whether the user wants Omnix to perform an action on the PC or is
having a conversation.

Return ONLY one word: automation or chat.

Choose automation when the user asks Omnix to operate the computer, apps,
files, media, keyboard, mouse, windows, browser, or visible screen.

Choose chat when the user asks for an explanation, opinion, factual answer,
or talks socially without requesting a PC action.

Questions about how to do something are chat unless the user explicitly asks
Omnix to do it.

Available automation skills:
{skill_text}

Examples:
"Open Chrome" -> automation
"Scroll down and click Downloads" -> automation
"Turn the volume up" -> automation
"How do I open Chrome?" -> chat
"What do you think about Spotify?" -> chat
"Can you explain what is on my screen?" -> chat

User input:
{text}
"""

        response = self.brain.ask(prompt)

        if not response:
            return "chat"

        response = response.strip().lower()

        if response.startswith("automation"):
            return "automation"

        return "chat"
