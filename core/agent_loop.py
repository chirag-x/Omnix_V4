import time
from loguru import logger
from memory.behavior_memory import BehaviorMemory
from core.target_resolver import TargetResolver


class AgentLoop:

    def __init__(
        self,
        planner,
        executor,
        vision_manager,
        context_manager,
        ui_controller=None,
    ):

        self.planner = planner
        self.executor = executor
        self.vision = vision_manager
        self.context = context_manager
        self.ui_controller = ui_controller

        self.behavior_memory = BehaviorMemory()
        self.target_resolver = TargetResolver(self.vision)

        self.running = False

    def _get_dynamic_steps(self, goal: str):
        length = len(goal)

        if length > 120:
            return 40
        elif any(word in goal.lower() for word in ["open", "search", "play"]):
            return 15
        return 25

    def _get_ui_elements(self, screen):

        elements = list((screen or {}).get("ui_elements", []) or [])

        if self.ui_controller is None:
            return elements

        seen = {
            (
                element.get("source", "vision"),
                str(element.get("type", "")),
                str(element.get("text", "")),
                element.get("x"),
                element.get("y"),
            )
            for element in elements
        }

        try:
            native_controls = self.ui_controller.list_controls(limit=40)
        except Exception as e:
            logger.debug(f"Native UI context unavailable in goal loop: {e}")
            return elements

        for control in native_controls:
            text = str(control.get("text") or "").strip()

            if not text:
                continue

            rectangle = control.get("rectangle") or {}
            item = {
                "source": "uia",
                "type": control.get("type") or "control",
                "text": text,
                "automation_id": control.get("automation_id"),
                "rectangle": rectangle,
            }

            if rectangle:
                item["x"] = int((rectangle["left"] + rectangle["right"]) / 2)
                item["y"] = int((rectangle["top"] + rectangle["bottom"]) / 2)

            key = (
                item["source"],
                str(item.get("type", "")),
                item["text"],
                item.get("x"),
                item.get("y"),
            )

            if key not in seen:
                elements.append(item)
                seen.add(key)

        return elements

    def run_goal(self, goal):

        logger.info(f"Agent goal started: {goal}")

        stored_plan = self.behavior_memory.recall(goal)

        if stored_plan:
            logger.info("Using stored behavior plan")
            return self.execute_plan(goal, stored_plan)

        logger.info("No stored behavior → planning")

        self.running = True
        step_count = 0
        max_steps = self._get_dynamic_steps(goal)

        generated_plan = []

        last_action = None
        last_result = None

        while self.running and step_count < max_steps:

            step_count += 1

            # Always refresh vision
            screen = self.vision.get_latest_analysis() or {}
            ui_elements = self._get_ui_elements(screen)

            system_context = self.context.get_system_context()

            combined_context = {
                "goal": goal,
                "system": system_context,
                "vision": screen,
                "ui_elements": ui_elements,
                "known_patterns": self.vision.ui_memory.get_patterns(
                    system_context.get("active_window", "unknown")
                ),
                "step_count": step_count,
                "last_action": last_action,
                "last_result": last_result
            }

            action = self.planner.next_action(goal, combined_context)

            if not action:
                logger.info("Planner returned no action → goal complete")
                break

            logger.info(f"Executing action: {action}")

            resolved = self.target_resolver.resolve(action, ui_elements)

            if resolved:
                action = resolved

            last_action = action

            result = self.executor.execute_skill(action)

            last_result = result

            logger.info(f"Execution result: {result}")

            if result == "error":

                logger.warning("Action failed → replanning")
                continue

            if result in ["done", "success"]:

                generated_plan.append(action)

                logger.info("Action succeeded")

            time.sleep(0.8)

        if generated_plan:

            logger.info("Storing successful behavior")

            self.behavior_memory.store(goal, generated_plan)

        logger.info("Agent loop finished")

    def execute_plan(self, goal, plan):

        logger.info(f"Executing stored plan for: {goal}")

        for step in plan:

            logger.info(f"Executing stored step: {step}")

            result = self.executor.execute_skill(step)

            if result == "error":

                logger.warning("Stored plan failed → abandoning")
                return

            time.sleep(1)

        logger.info("Stored behavior execution finished")
