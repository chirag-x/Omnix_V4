from loguru import logger
from memory.memory_manager import MemoryManager


class ConversationManager:
    """
    Session ki poori conversation history rakhta hai.
    BrainManager ko (role, text) tuples deta hai inject karne ke liye.
    """

    # Kitne turns brain ko dikhane hain (zyada = bada prompt = slow + costly)
    MAX_HISTORY_TURNS = 10

    def __init__(self):
        logger.info("Initializing Conversation Manager")

        self.memory = MemoryManager()

        # List of (role, text) — role = "user" ya "assistant"
        self.history: list[tuple[str, str]] = []

    # ──────────────────────────────────────────────────────────
    # Messages add karo
    # ──────────────────────────────────────────────────────────

    def add_user_message(self, message: str):

        logger.info(f"[User] {message}")

        self.history.append(("user", message))

        # Do NOT store every voice command as long-term memory
        # Only store conversational information.

        memory_keywords = [
            "my name is",
            "i like",
            "i prefer",
            "remember",
            "my favorite",
            "i work as",
            "i study",
        ]

        lower = message.lower()

        if any(k in lower for k in memory_keywords):
            self.memory.add_memory(message)

    def add_assistant_message(self, message: str):
        logger.info(f"[Omnix] {message}")
        self.history.append(("assistant", message))

    # ──────────────────────────────────────────────────────────
    # Brain ke liye history nikalo
    # ──────────────────────────────────────────────────────────

    def get_history_for_brain(self) -> list[tuple[str, str]]:
        """
        Last MAX_HISTORY_TURNS * 2 messages return karta hai
        (har turn mein user + assistant = 2 messages)
        """
        limit = self.MAX_HISTORY_TURNS * 2
        return self.history[-limit:]

    # ──────────────────────────────────────────────────────────
    # Legacy helper (pehle wala)
    # ──────────────────────────────────────────────────────────

    def get_history(self, limit: int = 10) -> list[tuple[str, str]]:
        return self.history[-limit:]

    # ──────────────────────────────────────────────────────────
    # Reset — naya session
    # ──────────────────────────────────────────────────────────

    def clear(self):
        logger.info("Conversation history cleared")
        self.history = []

    def __len__(self):
        return len(self.history)
