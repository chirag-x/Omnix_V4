import json
from loguru import logger
from ai.brain_manager import BrainManager
from core.command_processor import CommandProcessor


class TaskPlanner:

    SKILL_DESCRIPTIONS = {
        "open_app": "opens an installed desktop application. parameters: app",
        "close_app": "closes a running application. parameters: app",
        "type_text": "types text into the active input field. parameters: text",
        "press_key": "presses one keyboard key. parameters: key",
        "click_ui": "clicks a visible UI element by text using native UI automation first, OCR fallback second. parameters: text or target, optional index, window, control_type",
        "click_mouse": "clicks screen coordinates. parameters: x, y",
        "double_click": "double-clicks screen coordinates. parameters: x, y",
        "right_click": "right-clicks screen coordinates. parameters: x, y",
        "drag_mouse": "drags from one coordinate to another. parameters: x1, y1, x2, y2",
        "hotkey": "presses a keyboard shortcut. parameters: keys as a list, e.g. [\"ctrl\", \"l\"]",
        "scroll_page": "scrolls the active page or app. parameters: direction, use up or down",
        "media_control": "controls media and volume. parameters: action, one of volume_up, volume_down, mute, play_pause, next_track, previous_track",
        "browser_action": "controls browser workflows. parameters: action one of open_browser, open_url, search, back, forward, refresh, new_tab, close_tab, focus_address, next_tab, previous_tab; use query for search and url for open_url",
        "file_action": "performs file operations when supported by the file skill",
        "ui_control": "controls any visible app/window UI. parameters: action one of click, double_click, right_click, invoke, set_text, type, focus, select, expand, collapse, check, uncheck; target/text optional for set_text, value required for set_text/type",
        "window_control": "controls windows. parameters: action one of focus, switch, minimize, maximize, restore, close; optional title/window",
        "wait_for_ui": "waits until a UI element appears, disappears, or is enabled. parameters: target/text, optional state visible/gone/enabled, timeout, window, control_type",
    }

    DEFAULT_SKILLS = set(SKILL_DESCRIPTIONS)

    def __init__(self, command_processor=None, available_skills=None):

        logger.info("Initializing Task Planner")
        self.brain = BrainManager()
        self.command_processor = command_processor or CommandProcessor()
        self.allowed_skills = set(available_skills or self.DEFAULT_SKILLS)

        self.max_plan_steps = 20

    def set_available_skills(self, available_skills):

        self.allowed_skills = set(available_skills or self.DEFAULT_SKILLS)

    def _available_skills_text(self):

        lines = []

        for skill in sorted(self.allowed_skills):
            description = self.SKILL_DESCRIPTIONS.get(
                skill,
                "available skill loaded from the skills system. Use parameters required by that skill."
            )
            lines.append(f"- {skill}: {description}")

        return "\n".join(lines)

    def _normalize_action(self, action):

        if not isinstance(action, dict):
            return None

        skill = action.get("skill") or action.get("tool")

        if not skill:
            return None

        parameters = action.get("parameters", {})

        if not isinstance(parameters, dict):
            parameters = {}

        for key, value in action.items():
            if key not in {"skill", "tool", "parameters"}:
                parameters.setdefault(key, value)

        if skill == "open_browser":
            skill = "open_app"
            parameters.setdefault("app", "chrome")

        if skill == "open_url":
            skill = "browser_action"
            parameters.setdefault("action", "open_url")

        if skill in {"browser_search", "search_web", "web_search"}:
            skill = "browser_action"
            parameters.setdefault("action", "search")

        if skill in {"click", "tap"}:
            skill = "click_ui"

        if skill in {"control_ui", "ui"}:
            skill = "ui_control"

        if skill in {"window", "control_window"}:
            skill = "window_control"

        if skill in {"wait_for", "wait_until"}:
            skill = "wait_for_ui"

        # 🔥 FIX: Prevent trying to kill websites as OS processes
        if skill == "close_app" and str(parameters.get("app", "")).lower() in ["youtube", "google", "gmail", "facebook", "twitter", "whatsapp", "instagram"]:
            skill = "browser_action"
            parameters = {"action": "close_tab"}

        if skill not in self.allowed_skills:
            logger.warning(f"Invalid skill generated: {skill}")
            return None

        return {
            "skill": skill,
            "parameters": parameters
        }

    def _normalize_plan(self, plan):

        normalized = []

        for action in plan:
            item = self._normalize_action(action)
            if item:
                normalized.append(item)

        return normalized

    # ------------------------------------------------
    # Create full plan
    # ------------------------------------------------

    def create_plan(self, command, context=None):

        system_context = None
        vision_context = None
        ui_elements = []
        known_patterns = []

        if context:
            system_context = context.get("system")
            vision_context = context.get(
                "screen_summary") or context.get("vision")

            # 🔥 FIX: UI Elements ko compress kar rahe hain taaki tokens bach sakein
            raw_ui = (context.get("ui_elements") or [])[:30]
            ui_elements = [{"text": e.get("text"), "type": e.get(
                "type")} for e in raw_ui if e.get("text")]

            # 🔥 FIX: Patterns ko 5 se kam karke 3 kar diya aur unnecessary data hata diya
            raw_patterns = (context.get("known_patterns") or [])[-3:]
            for pattern in raw_patterns:
                compressed_pattern = [{"text": e.get("text"), "type": e.get(
                    "type")} for e in pattern if e.get("text")]
                known_patterns.append(compressed_pattern)

        prompt = f"""
                You are the planning brain of an AI desktop assistant called Omnix.

                Convert the user command into a sequence of executable actions.

                System context:
                {system_context}

                Vision context:
                {vision_context}

                Visible UI elements:
                {json.dumps(ui_elements)}

                Known UI patterns:
                {json.dumps(known_patterns)}

                Available skills loaded from the skills system:
                {self._available_skills_text()}

                Legacy skill reminders:

                open_app(app) → opens any installed desktop application
                close_app(app) → closes a running application
                type_text(text) → types text into the active input field
                press_key(key) → presses a keyboard key
                click_ui(text) → clicks a UI element containing specific text
                click_mouse(x, y) → clicks at screen coordinates
                double_click(x, y) → double clicks at coordinates
                right_click(x, y) → right clicks at coordinates
                drag_mouse(x1, y1, x2, y2) → drags mouse between coordinates
                hotkey(keys) → presses a keyboard shortcut (example: ctrl+c)
                scroll_page(direction) → scrolls up or down

                IMPORTANT:
                Use the existing skills loaded from the skills system.
                Return multiple steps for multi-part commands.
                Prefer ui_control or click_ui with visible text over mouse coordinates.
                Do not guess coordinates unless necessary.
                For browser search, prefer browser_action with action="search" and query.
                For browser navigation, use browser_action instead of raw typing when possible.
                For app-level closing, use close_app. For closing the active window or tab, use window_control or browser_action.
                For app UI workflows, open the app, wait_for_ui when useful, then use ui_control/click_ui/type_text/press_key.
                For play, pause, volume, mute, next, or previous media commands, use media_control.  
                If the user wants to close a website (e.g., "youtube"), use browser_action with action="close_tab", do NOT use close_app.
                For browser search, ALWAYS use browser_action with action="search" and the query parameter. Do NOT use hotkeys (Ctrl+L) for searching.
                For browser navigation, use browser_action instead of raw typing when possible.
                Use the existing skills loaded from the skills system.
                Prefer ui_control or click_ui with visible text over mouse coordinates. Do not guess coordinates.

                Rules:
                Return ONLY JSON list.
                Do not explain anything.
                Always include required parameters for each skill.

                Example:
                [
                {{"skill":"open_app","parameters":{{"app":"chrome"}}}}
                ]

                User command:
                {command}
                """

        try:
            response = self.brain.ask(prompt)
            logger.debug(f"AI planner response: {response}")

            if not response:
                logger.warning("AI returned empty response")
                return self.command_processor.create_simple_plan(command)

            response = response.strip()

            # remove markdown formatting
            response = response.replace("```json", "").replace("```", "")

            start = response.find("[")
            end = response.rfind("]")

            if start == -1 or end == -1:
                logger.warning(f"Planner returned invalid JSON: {response}")
                return self.command_processor.create_simple_plan(command)

            json_text = response[start:end + 1]
            plan = json.loads(json_text)

            if not isinstance(plan, list):
                return []

            return self._normalize_plan(plan)

        except Exception as e:
            logger.error(f"Task planning failed: {e}")
            return self.command_processor.create_simple_plan(command)
    # ------------------------------------------------
    # Next action for agent loop
    # ------------------------------------------------

    def next_action(self, goal, context):

        system_context = context.get("system")
        ui_elements = context.get("ui_elements")
        known_patterns = context.get("known_patterns")

        prompt = f"""
You are Omnix, a goal-driven desktop AI agent.

Goal:
{goal}

System state:
{system_context}

Visible UI elements:
{ui_elements}

Known UI patterns:
{known_patterns}

Available skills:
{self._available_skills_text()}

Rules:
Use only available skills.
Prefer ui_control/click_ui by target text over click_mouse coordinates.
Use browser_action for browser search/navigation.
Use window_control for active or named window operations.
Return one next action. Return null or no action only when the goal is complete.

Previous action:
{context.get("last_action")}

Previous result:
{context.get("last_result")}

Return ONLY JSON:

{{"skill":"skill_name","parameters":{{}}}}
"""

        try:

            response = self.brain.ask(prompt)

            if not response:
                return None

            response = response.strip()

            start = response.find("{")
            end = response.rfind("}")

            if start == -1 or end == -1:
                return None

            action = json.loads(response[start:end + 1])

            return self._normalize_action(action)

        except Exception as e:

            logger.error(f"Next action planning failed: {e}")
            return None
