# Omnix V4 module
import psutil
import pygetwindow as gw
from loguru import logger


class ContextManager:

    def __init__(self):
        logger.info("Initializing Context Manager")

    def get_active_window(self):
        """
        Returns the currently active window title
        """

        try:
            window = gw.getActiveWindow()

            if window:
                return window.title

            return None

        except Exception as e:
            logger.error(f"Failed to get active window: {e}")
            return None

    def get_running_apps(self):
        """
        Returns a list of running processes
        """

        apps = []

        try:
            for process in psutil.process_iter(['name']):
                apps.append(process.info['name'])

            return apps

        except Exception as e:
            logger.error(f"Failed to fetch running apps: {e}")
            return []

    def get_system_context(self):
        """
        Returns a simple context snapshot
        """

        context = {
            "active_window": self.get_active_window(),
            "running_apps": self.get_running_apps()[:20]  # limit list
        }

        return context