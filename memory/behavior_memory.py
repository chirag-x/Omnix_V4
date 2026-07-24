import json
import os
from loguru import logger


class BehaviorMemory:

    def __init__(self):

        logger.info("Initializing Behavior Memory")

        self.file_path = "memory/behavior_store.json"

        if not os.path.exists(self.file_path):

            with open(self.file_path, "w") as f:
                json.dump({}, f)

        self.memory = self._load()

    def _load(self):

        try:
            with open(self.file_path, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self):

        try:
            with open(self.file_path, "w") as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            logger.error(f"Failed saving behavior memory: {e}")

    def store(self, command, plan):

        key = command.lower()

        logger.info(f"Storing behavior for: {key}")

        self.memory[key] = plan

        self._save()

    def recall(self, command):

        command = command.lower()

        for stored_command in self.memory:

            if stored_command in command or command in stored_command:

                logger.info(f"Behavior memory match: {stored_command}")

                return self.memory[stored_command]

        return None

    def all_behaviors(self):

        return self.memory