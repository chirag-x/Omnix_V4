import re
from loguru import logger


class CommandProcessor:

    AUTOMATION_KEYWORDS = {
        "open", "start", "launch", "run", "close", "exit", "quit",
        "type", "write", "press", "hit", "click", "tap", "scroll",
        "volume", "mute", "unmute", "play", "pause", "resume", "next",
        "previous", "search", "google", "look", "create", "delete", "move",
        "rename", "copy", "paste", "select", "switch", "minimize",
        "maximize", "restore", "refresh", "navigate", "turn", "set"
    }

    CHAT_PREFIXES = (
        "what ",
        "why ",
        "who ",
        "when ",
        "where ",
        "how ",
        "explain ",
        "tell me ",
        "do you ",
        "are you ",
        "should i ",
        "could you tell me ",
        "can you tell me ",
    )

    SIMPLE_COMMAND_PATTERNS = [
        (
            r"^(?:open|start|launch|run)\s+(?:the\s+)?(.+?)(?:\s+app(?:lication)?)?$",
            "open_app",
            "app",
        ),
        (
            r"^(?:close|exit|quit)\s+(?:the\s+)?(.+?)(?:\s+app(?:lication)?)?$",
            "close_app",
            "app",
        ),
        (
            r"^(?:type|write)\s+(.+)$",
            "type_text",
            "text",
        ),
        (
            r"^(?:press|hit)\s+(.+)$",
            "press_key",
            "key",
        ),
        (
            r"^(?:click|tap)\s+(.+)$",
            "click_ui",
            "text",
        ),
        (
            r"^scroll\s+(up|down)$",
            "scroll_page",
            "direction",
        ),
    ]

    def process(self, text):

        text = text.strip().lower()

        if not text:
            return None

        if text in ["exit", "quit", "shutdown"]:
            return {"type": "system", "command": "shutdown"}

        text = text.replace("omnix", "").strip()

        return {
            "type": "user_input",
            "command": text
        }

    def create_simple_plan(self, text):

        plan = self._build_simple_plan(text)

        if not plan:
            return []

        logger.info(f"Using simple command plan: {plan}")
        return plan

    def is_simple_automation(self, text):

        return bool(self._build_simple_plan(text))

    def looks_like_automation(self, text):

        text = self._clean_command(text)

        if self.is_simple_automation(text):
            return True

        if text.startswith(self.CHAT_PREFIXES):
            return False

        for prefix in ("i want you to ", "i need you to ", "go ahead and "):
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
                break

        words = re.findall(r"[a-z0-9]+", text)

        if not words:
            return False

        if text.startswith("look up "):
            return True

        return words[0] in self.AUTOMATION_KEYWORDS

    def _build_simple_plan(self, text):

        text = self._clean_command(text)

        chained_plan = self._match_chained_command(text)

        if chained_plan:
            return chained_plan

        action = self._match_simple_command(text)

        if action:
            return [action]

        return self._actions_for_command_part(text, [])

    def _match_chained_command(self, text):

        parts = [
            part.strip()
            for part in re.split(r"\s+(?:and then|then|and)\s+", text)
            if part.strip()
        ]

        if len(parts) < 2:
            return []

        plan = []

        for part in parts:
            actions = self._actions_for_command_part(part, plan)

            if not actions:
                return []

            plan.extend(actions)

        return plan

    def _actions_for_command_part(self, text, current_plan):

        action = self._match_simple_command(text)

        if action:
            return [action]

        # Handle patterns like: "send hi to gopal" → click contact, type, press enter
        send_match = re.match(r"^send\s+(.+?)\s+to\s+(.+)$", text)

        if send_match:

            message = self._clean_parameter(send_match.group(1))
            recipient = self._clean_parameter(send_match.group(2))

            if not message or not recipient:
                return []

            actions = []

            # Click the contact by visible text
            actions.append({
                "skill": "click_ui",
                "parameters": {"text": recipient}
            })

            # Type the message
            actions.append({
                "skill": "type_text",
                "parameters": {"text": message}
            })

            # Send via Enter key
            actions.append({
                "skill": "press_key",
                "parameters": {"key": "enter"}
            })

            return actions

    def _match_simple_command(self, text):

        text = self._clean_command(text)

        if re.search(r"\s+(?:and then|then|and)\s+", text):
            return None

        direct_action = self._match_direct_command(text)

        if direct_action:
            return direct_action

        for pattern, skill, param_name in self.SIMPLE_COMMAND_PATTERNS:
            match = re.match(pattern, text)

            if not match:
                continue

            value = self._clean_parameter(match.group(1))

            if not value:
                return None

            return {
                "skill": skill,
                "parameters": {
                    param_name: value
                }
            }

        return None

    def _match_direct_command(self, text):

        media_actions = [
            (
                r"^(?:play|pause|resume)(?:\s+(?:music|song|track))?$",
                "play_pause",
            ),
            (
                r"^(?:next)(?:\s+(?:music|song|track))?$",
                "next_track",
            ),
            (
                r"^(?:previous|prev)(?:\s+(?:music|song|track))?$",
                "previous_track",
            ),
            (
                r"^(?:volume up|turn volume up|increase volume|raise volume)$",
                "volume_up",
            ),
            (
                r"^(?:volume down|turn volume down|decrease volume|lower volume)$",
                "volume_down",
            ),
            (
                r"^(?:mute|mute volume|turn mute on|unmute|turn mute off)$",
                "mute",
            ),
        ]

        for pattern, action in media_actions:
            if re.match(pattern, text):
                return {
                    "skill": "media_control",
                    "parameters": {"action": action}
                }

        window_match = re.match(
            r"^(minimize|maximize|restore|close)\s+"
            r"(?:(?:the|this|active|current)\s+)?window$",
            text,
        )

        if window_match:
            return {
                "skill": "window_control",
                "parameters": {"action": window_match.group(1)}
            }

        focus_match = re.match(r"^(?:switch to|focus)\s+(.+?)(?:\s+window)?$", text)

        if focus_match:
            return {
                "skill": "window_control",
                "parameters": {
                    "action": "focus",
                    "title": self._clean_parameter(focus_match.group(1))
                }
            }

        search_match = re.match(r"^(?:search|google|look up)\s+(?:for\s+)?(.+)$", text)

        if search_match:
            return {
                "skill": "browser_action",
                "parameters": {
                    "action": "search",
                    "query": self._clean_parameter(search_match.group(1))
                }
            }

        return None

    def _clean_command(self, text):

        text = str(text or "").lower().strip()
        text = re.sub(r"\b(?:hey\s+)?omnix\b", "", text)
        text = re.sub(r"^(?:please|can you|could you|would you)\s+", "", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip(" .,!?:;")

    def _clean_parameter(self, value):

        value = str(value or "").strip(" .,!?:;")

        for prefix in ("please ", "the "):
            if value.startswith(prefix):
                value = value[len(prefix):].strip()

        return value
