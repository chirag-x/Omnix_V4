from loguru import logger


class RetryManager:

    def __init__(self, max_retries=3):
        self.retry_counts = {}
        self.max_retries = max_retries

    def should_retry(self, action):

        key = str(action)
        count = self.retry_counts.get(key, 0)

        if count >= self.max_retries:
            logger.warning(f"Retry limit reached for action: {action}")
            return False

        self.retry_counts[key] = count + 1
        return True

    def reset(self, action):

        key = str(action)

        if key in self.retry_counts:
            del self.retry_counts[key]