import threading
import time

from loguru import logger

from vision.vision_pipeline import VisionPipeline
from memory.ui_pattern_memory import UIPatternMemory
from system.window_controller import WindowController


class VisionManager:

    def __init__(self, observer):

        logger.info("Initializing Vision Manager")

        self.observer = observer
        self.pipeline = VisionPipeline(self.observer)

        self.ui_memory = UIPatternMemory()

        self.latest_analysis = None
        self.last_ui_snapshot = None

        self.running = False
        self.thread = None

    def start(self):

        logger.info("Starting Vision Manager")

        if self.running:
            return

        self.observer.start()

        self.running = True

        self.thread = threading.Thread(
            target=self._loop,
            daemon=True
        )

        self.thread.start()

    def stop(self):

        logger.info("Stopping Vision Manager")

        self.running = False

        if self.thread:
            self.thread.join()

        self.observer.stop()

    def _loop(self):

        logger.info("Vision Manager loop started")

        while self.running:

            try:

                frame = self.observer.get_latest_frame()

                if frame is None:
                    time.sleep(0.1)
                    continue

                analysis = self.pipeline.analyze_frame(frame)

                if not analysis:
                    continue

                ui_elements = analysis.get("ui_elements", [])

                # ------------------------------------------------
                # Detect UI change
                # ------------------------------------------------

                if ui_elements != self.last_ui_snapshot:

                    active_app = WindowController.get_active_window()

                    if active_app:
                        self.ui_memory.store_pattern(
                            active_app,
                            ui_elements
                        )

                    self.last_ui_snapshot = ui_elements

                    logger.debug("UI change detected — pattern stored")

                self.latest_analysis = dict(analysis)

            except Exception as e:

                logger.error(f"Vision loop error: {e}")

            time.sleep(0.25)

    def get_latest_analysis(self):

        return self.latest_analysis
