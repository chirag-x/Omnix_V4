from loguru import logger


class ScreenIntelligence:

    def __init__(self, vision_manager=None):

        logger.info("Initializing Screen Intelligence")
        
        self.vision = vision_manager

    def analyze(self, vision_data):

        objects = vision_data.get("objects", [])
        texts = vision_data.get("texts", [])

        ui_elements = []

        # OCR text elements
        for text in texts:

            label = str(text.get("text", "")).strip()

            if not label:
                continue

            ui_elements.append({
                "type": "text",
                "text": label,
                "x": text.get("x"),
                "y": text.get("y"),
                "source": "ocr"
            })

        # YOLO detected objects
        for obj in objects:

            ui_elements.append({
                "type": obj.get("type"),
                "text": obj.get("type"),
                "x": obj.get("x"),
                "y": obj.get("y"),
                "source": "vision"
            })

        logger.info(
            f"Screen Intelligence extracted {len(ui_elements)} UI elements"
        )

        return ui_elements

    def find_text_element(self, text):

        if not self.vision:
            return None

        analysis = self.vision.get_latest_analysis()

        if not analysis:
            return None

        texts = analysis.get("texts", [])

        target = text.lower()

        for item in texts:

            content = str(
                item.get("text", "")
            ).lower()

            if target in content:
                return item

        return None

    def find_click_target(self, keywords):

        if not self.vision:
            return None

        analysis = self.vision.get_latest_analysis()

        if not analysis:
            return None

        texts = analysis.get("texts", [])

        for keyword in keywords:

            keyword = keyword.lower()

            for item in texts:

                content = str(
                    item.get("text", "")
                ).lower()

                if keyword in content:
                    return item

        return None

    def find_search_box(self):

        return self.find_click_target([
            "search",
            "google",
            "search google",
            "type here",
            "find"
        ])
