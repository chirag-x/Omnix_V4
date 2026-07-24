from loguru import logger


class ErrorHandler:

    def handle(self, error, context=None):

        logger.error(f"Error occurred: {error}")

        if context:
            logger.error(f"Context: {context}")

        return {
            "status": "error",
            "recoverable": True
        }