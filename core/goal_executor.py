from loguru import logger
from skills.skill_manager import SkillManager
from core.retry_manager import RetryManager
from core.error_handler import ErrorHandler


class GoalExecutor:

    def __init__(self, skill_manager=None, dependencies=None):

        logger.info("Initializing Goal Executor")

        self.skill_manager = skill_manager or SkillManager(dependencies)
        self.retry_manager = RetryManager()
        self.error_handler = ErrorHandler()

        self.running = True

    # ------------------------------------------------
    # Execute full plan
    # ------------------------------------------------

    def execute_plan(self, plan):

        logger.info("Starting goal execution")

        for step_index, step in enumerate(plan):

            if not self.running:
                logger.warning("Goal execution stopped")
                break

            logger.info(f"Executing step {step_index + 1}: {step}")

            result = self.execute_step(step)

            if result == "error":

                logger.error("Goal execution failed")

                return "error"

        logger.info("Goal execution finished")

        return "success"

    # ------------------------------------------------
    # Execute single step
    # ------------------------------------------------

    def execute_step(self, step):

        try:

            result = self.skill_manager.execute_skill(step)

            if result == "error":

                if self.retry_manager.should_retry(step):

                    logger.warning("Retrying step")

                    return self.skill_manager.execute_skill(step)

                else:

                    logger.error("Step failed permanently")

                    return "error"

            return result

        except Exception as e:

            self.error_handler.handle(e, step)

            return "error"

    def execute_skill(self, step):

        return self.execute_step(step)

    # ------------------------------------------------
    # Stop execution
    # ------------------------------------------------

    def stop(self):

        logger.warning("Stopping goal execution")

        self.running = False
