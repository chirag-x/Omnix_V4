import threading
import time
import mss
import numpy as np
from loguru import logger


class ScreenObserver:

    def __init__(self, capture_interval=0.5):

        logger.info("Initializing Screen Observer")

        self.capture_interval = capture_interval
        self.latest_frame = None
        self.screen_bounds = None

        self.running = False
        self.thread = None

        
    def start(self):

        logger.info("Starting screen observer")

        self.running = True

        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def stop(self):

        logger.info("Stopping screen observer")

        self.running = False

        if self.thread:
            self.thread.join()

    def _capture_loop(self):

        # IMPORTANT: create MSS inside the thread
        with mss.mss() as sct:

            monitor = sct.monitors[0]  # full desktop
            self.screen_bounds = {
                "left": monitor.get("left", 0),
                "top": monitor.get("top", 0),
                "width": monitor.get("width", 0),
                "height": monitor.get("height", 0),
            }

            while self.running:

                try:

                    screenshot = sct.grab(monitor)

                    frame = np.array(screenshot)

                    self.latest_frame = frame

                    time.sleep(self.capture_interval)

                except Exception as e:

                    logger.error(f"Screen capture failed: {e}")
                    time.sleep(1)

    def get_latest_frame(self):

        return self.latest_frame
