import numpy as np
import pygetwindow as gw
from system.keyboard_mouse_controller import KeyboardMouseController
from loguru import logger


class VisionController:

    def __init__(self, screen_observer):

        logger.info("Initializing Vision Controller")

        self.observer = screen_observer

    def click(self, x, y):

        logger.info(f"Clicking at {x}, {y}")

        KeyboardMouseController.click(x, y)

    def click_ui_element(self, element):

        x = element["x"]
        y = element["y"]

        self.click(x, y)

    def type_text(self, text):

        logger.info(f"Typing text via vision system: {text}")

        KeyboardMouseController.type_text(text)

    def press_key(self, key):

        logger.info(f"Pressing key: {key}")

        KeyboardMouseController.press_key(key)

    def ensure_window_focus(self, window_title):

        

        windows = gw.getWindowsWithTitle(window_title)

        if windows:

            window = windows[0]

            if not window.isActive:
                logger.info(f"Focusing window: {window_title}")
                window.activate()
