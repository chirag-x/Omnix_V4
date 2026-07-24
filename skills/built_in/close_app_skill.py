from loguru import logger
from system.app_controller import AppController


class CloseAppSkill:

    name = "close_app"

    def run(self, params):

        app = params.get("app")

        if not app:
            logger.warning("close_app called without app parameter")
            return "error"

        logger.info(f"Closing application: {app}")

        try:
            return AppController.close_app(app)

        except Exception as e:

            logger.error(f"Failed to close app: {e}")

            return "error"
