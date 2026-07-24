from loguru import logger


class AutomationEngine:

    def __init__(self, skill_manager):

        logger.info("Initializing Automation Engine")

        self.skill_manager = skill_manager
        self.running = True

    def execute_plan(self, plan):

        logger.info("Starting automation plan")

        for step in plan:

            if not self.running:
                logger.warning("Automation stopped")
                break

            skill_name = step.get("skill")
            params = step.get("params", {})

            logger.info(f"Executing step: {skill_name}")

            skill = self.skill_manager.get_skill(skill_name)

            if not skill:
                logger.error(f"Skill not found: {skill_name}")
                continue

            try:

                skill.execute(**params)

            except Exception as e:

                logger.error(f"Skill failed: {skill_name} | Error: {e}")

        logger.info("Automation plan finished")

    def stop(self):

        logger.warning("Stopping automation")

        self.running = False
