# Omnix V4 module
import pyautogui
from loguru import logger

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05


class KeyboardMouseController:

    @staticmethod
    def click(x=None, y=None):

        logger.info(f"Mouse click at {x}, {y}")

        if x is not None and y is not None:
            pyautogui.click(x, y)
        else:
            pyautogui.click()

    @staticmethod
    def double_click(x=None, y=None):

        logger.info(f"Mouse double click at {x}, {y}")

        if x is not None and y is not None:
            pyautogui.doubleClick(x, y)
        else:
            pyautogui.doubleClick()

    @staticmethod
    def right_click(x=None, y=None):

        logger.info(f"Mouse right click at {x}, {y}")

        if x is not None and y is not None:
            pyautogui.rightClick(x, y)
        else:
            pyautogui.rightClick()

    @staticmethod
    def drag(x1, y1, x2, y2):

        logger.info(f"Dragging from {x1},{y1} to {x2},{y2}")

        pyautogui.moveTo(x1, y1)
        pyautogui.dragTo(x2, y2, duration=0.3)

    @staticmethod
    def scroll(amount):

        logger.info(f"Scrolling {amount}")

        pyautogui.scroll(amount)

    @staticmethod
    def type_text(text):

        logger.info(f"Typing text: {text}")

        pyautogui.write(text, interval=0.03)

    @staticmethod
    def press_key(key):

        logger.info(f"Pressing key: {key}")

        pyautogui.press(key)

    @staticmethod
    def hotkey(*keys):

        logger.info(f"Hotkey pressed: {keys}")

        pyautogui.hotkey(*keys)