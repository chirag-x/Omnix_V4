from loguru import logger
from vision.ui_detector import UIDetector
from vision.text_detector import TextDetector
from vision.screen_intelligence import ScreenIntelligence


class VisionPipeline:

    def __init__(self, observer):

        logger.info("Initializing Vision Pipeline")

        self.observer = observer
        self.detector = UIDetector()
        self.text_detector = TextDetector()
        self.screen_ai = ScreenIntelligence()

    def analyze_frame(self, frame):

        objects = self.detector.detect(frame)
        texts = self.text_detector.detect_text(frame)

        if objects or texts:
            logger.info(
                f"Vision detected {len(objects)} objects and {len(texts)} text elements"
            )

        ui_elements = self.screen_ai.analyze({
            "objects": objects,
            "texts": texts
        })

        return {
            "objects": objects,
            "texts": texts,
            "ui_elements": ui_elements
        }
