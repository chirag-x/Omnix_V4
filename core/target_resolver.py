from loguru import logger
from vision.element_locator import ElementLocator


class TargetResolver:

    def __init__(self, vision_manager=None):

        self.vision_manager = vision_manager
        self.locator = ElementLocator(
            vision_manager) if vision_manager else None

    def resolve(self, action, ui_elements):

        skill = action.get("skill")

        # Only resolve UI click actions
        if skill != "click_ui":
            return None

        params = action.get("parameters", {})
        text = params.get("text")
        index = params.get("index")

        if not text:
            return None

        text = text.lower()

        element = None

        # ------------------------------------------------
        # 1️⃣ Check current UI elements first (FASTEST)
        # ------------------------------------------------

        if ui_elements:

            matches = []

            for el in ui_elements:

                label = el.get("text", "").lower()

                if text in label:
                    matches.append(el)

            if matches:

                if index is not None and index < len(matches):
                    element = matches[index]
                else:
                    element = matches[0]

                logger.info(f"Resolved from current UI elements: {text}")

        # ------------------------------------------------
        # 2️⃣ Try UI Pattern Memory
        # ------------------------------------------------

        if not element and self.vision_manager:

            active_app = None

            if hasattr(self.vision_manager, "context"):
                system = self.vision_manager.context.get_system_context()
                active_app = system.get("active_window")

            if active_app and hasattr(self.vision_manager, "ui_memory"):

                patterns = self.vision_manager.ui_memory.get_patterns(
                    active_app)

                for pattern in patterns:

                    for item in pattern:

                        label = item.get("text", "").lower()

                        if text in label:

                            logger.info(f"Resolved from UI memory: {label}")
                            element = item
                            break

                    if element:
                        break

        # ------------------------------------------------
        # 3️⃣ Locator indexed search
        # ------------------------------------------------

        if not element and self.locator and index is not None:

            element = self.locator.find_nth(text, index)

            if element:
                logger.info(f"Resolved indexed UI element: {text} #{index}")

        # ------------------------------------------------
        # 4️⃣ Locator direct search
        # ------------------------------------------------

        if not element and self.locator:

            element = self.locator.find_text(text)

            if element:
                logger.info(f"Resolved UI element by text: {text}")

        # ------------------------------------------------
        # 5️⃣ Ranked locator results
        # ------------------------------------------------

        if not element and self.locator:

            results = self.locator.find_ranked_results()

            for r in results:

                label = r.get("text", "").lower()

                if text in label:
                    element = r
                    logger.info(f"Resolved from ranked results: {label}")
                    break

        # ------------------------------------------------
        # 6️⃣ Vertical list detection
        # ------------------------------------------------

        if not element and self.locator:

            vertical_list = self.locator.detect_vertical_list()

            for item in vertical_list:

                label = item.get("text", "").lower()

                if text in label:
                    element = item
                    logger.info(f"Resolved vertical list element: {label}")
                    break

        # ------------------------------------------------
        # Final validation
        # ------------------------------------------------

        if not element:

            logger.warning(f"UI element not found: {text}")
            return None

        x = element.get("x")
        y = element.get("y")

        if x is None or y is None:

            logger.warning("Resolved element has no coordinates")
            return None

        if element.get("source") != "uia":
            x, y = self._desktop_coordinates(x, y)

        return {
            "skill": "click_mouse",
            "parameters": {
                "x": x,
                "y": y
            }
        }

    def _desktop_coordinates(self, x, y):

        observer = getattr(self.vision_manager, "observer", None)
        bounds = getattr(observer, "screen_bounds", None)

        if not bounds:
            return x, y

        return (
            int(bounds.get("left", 0) + x),
            int(bounds.get("top", 0) + y),
        )
