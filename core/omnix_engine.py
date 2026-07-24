# Omnix V4 module

from loguru import logger

from vision.screen_observer import ScreenObserver
from vision.vision_manager import VisionManager

from core.agent_controller import AgentController


class OmnixEngine:

    def __init__(self):

        logger.info("Initializing Omnix Engine...")

        # Vision system
        self.observer = ScreenObserver()
        self.vision = VisionManager(self.observer)

        # Agent controller (brain)
        self.agent = AgentController(self.vision)

    def start(self):

        logger.info("Starting Omnix Engine")

        # start vision system
        self.vision.start()

        while True:

            command = input("Command: ")

            if not command:
                continue

            result = self.agent.process_command(command)

            if result:
                print(result)