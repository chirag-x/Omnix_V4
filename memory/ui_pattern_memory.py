import json
import os
from loguru import logger


class UIPatternMemory:

    def __init__(self, file_path="memory/ui_patterns.json"):

        logger.info("Initializing UI Pattern Memory")

        self.file_path = file_path
        self.patterns = {}

        self._load()

    def _load(self):

        if not os.path.exists(self.file_path):
            return

        try:
            with open(self.file_path, "r") as f:
                self.patterns = json.load(f)

            logger.info("Loaded UI patterns from disk")

        except Exception as e:
            logger.error(f"Failed to load UI patterns: {e}")

    def _save(self):

        try:

            os.makedirs(
                os.path.dirname(self.file_path),
                exist_ok=True
            )

            with open(self.file_path, "w") as f:

                json.dump(
                    self.patterns,
                    f,
                    indent=2,
                    default=lambda o:
                    int(o) if hasattr(o, "item")
                    else str(o)
                )

        except Exception as e:

            logger.error(
                f"Failed to save UI patterns: {e}"
            )

    def store_pattern(self, app_name, ui_elements):

        if not ui_elements:
            return

        if app_name not in self.patterns:
            self.patterns[app_name] = []

        current_signature = sorted([
            (
                str(item.get("type", "")),
                str(item.get("text", ""))[:50]
            )
            for item in ui_elements
        ])

        for existing in self.patterns[app_name]:

            existing_signature = sorted([
                (
                    str(item.get("type", "")),
                    str(item.get("text", ""))[:50]
                )
                for item in existing
            ])

            if existing_signature == current_signature:
                return

        self.patterns[app_name].append(ui_elements)

        self.patterns[app_name] = (
            self.patterns[app_name][-20:]
        )

        self._save()

        logger.info(
            f"Stored new UI pattern for {app_name}"
        )

    def get_patterns(self, app_name):

        return self.patterns.get(
            app_name,
            []
        )

    def match_pattern(
        self,
        app_name,
        text
    ):

        patterns = self.patterns.get(
            app_name,
            []
        )

        for pattern in patterns:

            for element in pattern:

                label = str(
                    element.get("text", "")
                ).lower()

                if text.lower() in label:
                    return element

        return None
