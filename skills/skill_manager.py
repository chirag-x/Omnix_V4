from loguru import logger
from skills.skill_loader import SkillLoader
from skills.skill_generator import SkillGenerator


class SkillManager:

    def __init__(self, dependencies=None):

        logger.info("Initializing Skill Manager")

        self.dependencies = dependencies or {}

        self.loader = SkillLoader(self.dependencies)

        self.skills = self.loader.load_skills()

        self.generator = SkillGenerator()

    def _normalize_step(self, step):

        if not isinstance(step, dict):
            return {}

        skill_name = step.get("skill") or step.get("tool")
        params = step.get("parameters", {})

        if not isinstance(params, dict):
            params = {}

        for key, value in step.items():
            if key not in {"skill", "tool", "parameters"}:
                params.setdefault(key, value)

        if skill_name == "open_browser":
            skill_name = "open_app"
            params.setdefault("app", "chrome")

        if skill_name == "open_url":
            skill_name = "browser_action"
            params.setdefault("action", "open_url")

        if skill_name in {"browser_search", "search_web", "web_search"}:
            skill_name = "browser_action"
            params.setdefault("action", "search")

        if skill_name in {"click", "tap"}:
            skill_name = "click_ui"

        if skill_name in {"control_ui", "ui"}:
            skill_name = "ui_control"

        if skill_name in {"window", "control_window"}:
            skill_name = "window_control"

        if skill_name in {"wait_for", "wait_until"}:
            skill_name = "wait_for_ui"

        return {
            "skill": skill_name,
            "parameters": params
        }

    def execute_skill(self, step):

        step = self._normalize_step(step)

        skill_name = step.get("skill")

        if not skill_name:
            logger.warning("No skill specified in step")
            return "error"

        if skill_name not in self.skills:

            logger.warning(f"No skill found for tool: {skill_name}")

            try:

                self.generator.create_skill(skill_name)

                self.skills = self.loader.load_skills()

                logger.info(f"Generated and loaded new skill: {skill_name}")

            except Exception as e:

                logger.error(f"Skill generation failed: {e}")
                return "error"

            return "error"

        skill = self.skills[skill_name]

        logger.info(f"Running skill: {skill_name}")

        params = step.get("parameters", {})

        result = skill.run(params)

        if result is None:
            return "success"

        return result
