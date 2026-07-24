import os
import importlib
import inspect
from loguru import logger


class SkillLoader:

    def __init__(self, dependencies=None):

        self.skill_folders = [
            "skills/built_in",
            "skills/generated"
        ]

        # dependencies that can be passed into skills
        self.dependencies = dependencies or {}

    def load_skills(self):

        skills = {}

        for folder in self.skill_folders:

            if not os.path.exists(folder):
                continue

            for file in os.listdir(folder):

                if not file.endswith(".py"):
                    continue

                module_name = file[:-3]
                module_path = folder.replace("/", ".") + "." + module_name

                try:

                    module = importlib.import_module(module_path)
                    importlib.reload(module)

                    for name, obj in inspect.getmembers(module):

                        if inspect.isclass(obj) and name.endswith("Skill"):

                            try:
                                skill_instance = obj(**self.dependencies)
                            except TypeError:
                                skill_instance = obj()

                            if skill_instance.name in skills:
                                logger.warning(
                                    f"Skipping duplicate skill: {skill_instance.name}"
                                )
                                continue

                            skills[skill_instance.name] = skill_instance

                            logger.info(f"Loaded skill: {skill_instance.name}")

                except Exception as e:
                    logger.error(f"Failed loading skill {module_path}: {e}")

        return skills
