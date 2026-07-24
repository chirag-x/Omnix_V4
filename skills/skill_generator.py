from loguru import logger
import os


class SkillGenerator:

    def __init__(self):

        logger.info("Initializing Skill Generator")

        self.skill_folder = "skills/generated"

        os.makedirs(self.skill_folder, exist_ok=True)

    def create_skill(self, skill_name):

        file_name = f"{skill_name}_skill.py"
        file_path = os.path.join(self.skill_folder, file_name)
        built_in = f"skills/built_in/{skill_name}_skill.py"
        generated = f"skills/generated/{skill_name}_skill.py"

        if os.path.exists(built_in) or os.path.exists(generated):
            logger.info(f"Skill already exists: {skill_name}")
            return None

        logger.info(f"Generating new skill: {skill_name}")

        class_name = "".join(word.capitalize()
                             for word in skill_name.split("_")) + "Skill"

        template = f'''
            from loguru import logger

            class {class_name}:

                name = "{skill_name}"

                def __init__(self, **deps):
                    self.deps = deps

                def run(self, params):

                    logger.info("Running generated skill: {skill_name}")

                    # access dependencies like:
                    # controller = self.deps.get("system")

                    return "success"
            '''

        with open(file_path, "w") as f:
            f.write(template)

        logger.info(f"Skill created: {file_path}")

        return file_path
