from utils.logger import setup_logger
import time
import transformers
import warnings


def main():

    logger = setup_logger()
    logger.info("Starting Omnix V4...")

    warnings.filterwarnings("ignore")
    try:
        transformers.logging.set_verbosity_error()
    except Exception:
        pass
    try:

        # -----------------------------
        # Context Manager
        # -----------------------------
        from context.context_manager import ContextManager

        context_manager = ContextManager()
        system_context = context_manager.get_system_context()

        logger.info(f"System Context: {system_context}")

        # -----------------------------
        # Memory System
        # -----------------------------
        from memory.memory_manager import MemoryManager

        memory = MemoryManager()

        memory.add_memory("Chirag likes coding in VS Code")
        memory.add_memory("Chirag watches python tutorials frequently")
        memory.add_memory("Chirag prefers Chrome browser")

        # -----------------------------
        # Vision Manager
        # -----------------------------
        from vision.screen_observer import ScreenObserver
        from vision.vision_manager import VisionManager

        observer = ScreenObserver()

        vision_manager = VisionManager(observer)
        vision_manager.start()

        time.sleep(2)

        logger.info("Vision system started")

        # -----------------------------
        # Agent Controller
        # -----------------------------
        from core.agent_controller import AgentController

        agent = AgentController(vision_manager)

        logger.info("Agent controller initialized")

        # -----------------------------
        # Voice System
        # -----------------------------
        from voice.voice_manager import VoiceManager

        voice = VoiceManager(agent)
        voice.start()
        # time.sleep(1)

        # voice.speak("Hello Chirag. Omnix is now online.")

        logger.info("Voice system started")

        # Keep program alive
        while True:
            time.sleep(1)

    except Exception as e:

        logger.exception(f"Fatal error: {e}")


if __name__ == "__main__":
    main()
