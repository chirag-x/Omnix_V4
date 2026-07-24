import time
from loguru import logger

from core.task_planner import TaskPlanner
from core.command_processor import CommandProcessor
from ai.brain_manager import BrainManager
from core.intent_classifier import IntentClassifier
from core.conversation_manager import ConversationManager   # NEW
from core.agent_loop import AgentLoop
from core.goal_executor import GoalExecutor
from skills.skill_manager import SkillManager
from memory.memory_manager import MemoryManager
from context.context_manager import ContextManager
from automation.automation_engine import AutomationEngine
from state.environment_state import EnvironmentState
from vision.screen_summary import ScreenSummaryBuilder
from system.ui_controller import UIController


class AgentController:

    def __init__(self, vision_manager):

        logger.info("Initializing Agent Controller")

        self.command_processor = CommandProcessor()
        self.vision = vision_manager
        self.ui_controller = UIController(self.vision)
        self.skill_dependencies = {
            "vision_manager": self.vision,
            "screen_observer": getattr(self.vision, "observer", None),
            "ui_controller": self.ui_controller,
        }
        self.skills = SkillManager(self.skill_dependencies)
        self.intent_classifier = IntentClassifier(
            self.command_processor,
            available_skills=self.skills.skills.keys()
        )
        self.planner = TaskPlanner(
            self.command_processor,
            available_skills=self.skills.skills.keys()
        )
        self.memory = MemoryManager()
        self.context = ContextManager()
        self.brain = BrainManager()
        self.screen_summary = ScreenSummaryBuilder()
        self.conversation = ConversationManager()           # NEW

        self.executor = GoalExecutor(self.skills)
        self.env_state = EnvironmentState()

        self.agent_loop = AgentLoop(
            self.planner,
            self.executor,
            self.vision,
            self.context,
            self.ui_controller
        )

        self.automation = AutomationEngine(self)

    # ──────────────────────────────────────────────────────────
    # Helper — screen summary
    # ──────────────────────────────────────────────────────────

    def _get_screen_summary(self) -> str:
        system_context = self.context.get_system_context()
        vision_data = self._with_native_ui(self.vision.get_latest_analysis() or {})
        return self.screen_summary.build(system_context, vision_data)

    def _with_native_ui(self, vision_data):

        enriched = dict(vision_data or {})
        enriched["ui_elements"] = self._get_current_ui_elements(enriched)
        return enriched

    def _get_current_ui_elements(self, vision_data):

        elements = list((vision_data or {}).get("ui_elements", []) or [])
        seen = set()

        for element in elements:
            seen.add((
                element.get("source", "vision"),
                str(element.get("type", "")),
                str(element.get("text", "")),
                element.get("x"),
                element.get("y"),
            ))

        try:
            native_controls = self.ui_controller.list_controls(limit=40)
        except Exception as e:
            logger.debug(f"Native UI context unavailable: {e}")
            native_controls = []

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

    # ──────────────────────────────────────────────────────────
    # Main command processor
    # ──────────────────────────────────────────────────────────

    def process_command(self, command: str) -> str:

        logger.info(f"Processing command: {command}")

        # User message history mein add karo
        self.conversation.add_user_message(command)

        intent = self.intent_classifier.classify(command)

        # ── Chat mode ─────────────────────────────────────────
        if intent == "chat":
            logger.info("Chat intent detected")

            summary = self._get_screen_summary()
            history = self.conversation.get_history_for_brain()

            # Current message history se nikalo — brain separately bhejega
            history_without_last = history[:-1] if history else []

            answer = self.brain.ask(
                command,
                context=summary,
                conversation_history=history_without_last   # pichla context
            )

            if not answer:
                answer = "I couldn't generate a response."

            # Response history mein save karo
            self.conversation.add_assistant_message(answer)
            return answer

        # ── Goal mode ─────────────────────────────────────────
        if self.is_goal_command(command):
            logger.info("Goal-style command detected -> starting agent loop")
            self.agent_loop.run_goal(command)
            response = "Working on it."
            self.conversation.add_assistant_message(response)
            return response

        # ── Simple automation mode ─────────────────────────────
        system_context = self.context.get_system_context()
        vision_data = self._with_native_ui(self.vision.get_latest_analysis() or {})
        self.env_state.update(system_context, vision_data)

        summary = self.screen_summary.build(system_context, vision_data)
        logger.info(f"Screen summary:\n{summary}")

        related_memory = self.memory.search_memory(command)
        logger.info(f"Related memory: {related_memory}")

        ui_elements = vision_data.get("ui_elements", [])
        patterns = self.vision.ui_memory.get_patterns(
            system_context.get("active_window", "unknown")
        )

        combined_context = {
            "system": system_context,
            "vision": vision_data,
            "ui_elements": ui_elements,
            "memory": related_memory,
            "known_patterns": patterns,
            "screen_summary": summary
        }

        plan = self.planner.create_plan(command, combined_context)
        logger.info(f"Plan generated: {plan}")

        if not plan:
            logger.warning("No plan generated")
            response = "I couldn't figure out how to do that."
            self.conversation.add_assistant_message(response)
            return response

        result = self.execute_plan_with_feedback(command, plan)

        if result == "error":
            response = "I tried, but that action failed."
        else:
            response = "Task completed."

        self.conversation.add_assistant_message(response)
        return response

    # ──────────────────────────────────────────────────────────
    # Plan execution with vision feedback
    # ──────────────────────────────────────────────────────────

    def execute_plan_with_feedback(self, command: str, plan: list, fail_count=0):

        step_count = 0
        max_steps = self.planner.max_plan_steps
        max_failures = 3

        for step in plan:

            if step_count >= max_steps:
                logger.warning("Max steps reached, stopping")
                return "error"

            step_count += 1
            skill = step.get("skill")
            logger.info(f"Executing step: {skill}")

            result = self.skills.execute_skill(step)
            self.env_state.set_action_feedback(step, result)
            logger.info(f"Skill result: {result}")

            time.sleep(1)

            system_context = self.context.get_system_context()
            vision_data = self._with_native_ui(
                self.vision.get_latest_analysis() or {}
            )
            summary = self.screen_summary.build(system_context, vision_data)

            observation = {
                "system": system_context,
                "vision": vision_data,
                "ui_elements": vision_data.get("ui_elements", []),
                "last_result": result,
                "screen_summary": summary
            }

            logger.debug(f"Post-step screen: {summary}")

            if result == "error":
                fail_count += 1
                if fail_count >= max_failures:
                    logger.error("Too many failures, aborting")
                    return "error"
                logger.warning("Step failed -> replanning")
                new_plan = self.planner.create_plan(command, observation)
                if new_plan:
                    return self.execute_plan_with_feedback(
                        command,
                        new_plan,
                        fail_count=fail_count
                    )
                return "error"

        logger.info("Task execution completed")
        return "success"

    # ──────────────────────────────────────────────────────────
    # Goal detection
    # ──────────────────────────────────────────────────────────

    def is_goal_command(self, command: str) -> bool:

        command = command.lower()

        goal_keywords = [
            "find", "research", "look for",
            "compare", "analyze", "download", "summarize"
        ]
        simple_commands = ["open", "start", "launch", "type", "press"]

        if any(cmd in command for cmd in simple_commands):
            return False

        return any(word in command for word in goal_keywords)
