import os
import requests
from loguru import logger
from dotenv import load_dotenv

load_dotenv()


class BrainManager:

    def __init__(self):
        logger.info("Initializing AI Brain Manager")

        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("OPENROUTER_MODEL")
        self.url = self._chat_completions_url(
            os.getenv("OPENROUTER_URL")
            or "https://openrouter.ai/api/v1/chat/completions"
        )

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY missing in .env file")

    def _chat_completions_url(self, url):

        url = str(url or "").rstrip("/")

        if url.endswith("/chat/completions"):
            return url

        if url.endswith("/api/v1"):
            return f"{url}/chat/completions"

        return url

    # ──────────────────────────────────────────────────────────
    # Core ask — ab conversation_history support karta hai
    # ──────────────────────────────────────────────────────────

    def ask(
        self,
        message: str,
        context: str = None,
        vision_data: dict = None,   # 🔥 NEW
        conversation_history: list = None
    ) -> str | None:

        try:
            # ── System prompt ──────────────────────────────
            system_parts = [
                "You are Omnix, an intelligent desktop AI agent.",
                "You help the user control their Windows PC through voice and automation.",
                "Be concise. Respond in the same language the user speaks.",
            ]

            if vision_data:
                texts = [t.get("text", "")
                         for t in vision_data.get("texts", [])][:20]
                ui = vision_data.get("ui_elements", [])[:15]

                system_parts.append(
                    "\n--- Current Screen Context ---\n"
                    f"Visible texts: {texts}\n"
                    f"UI elements: {ui}\n"
                    "Use this to decide actions precisely.\n"
                    "---"
                )

            if context:
                system_parts.append(f"\nAdditional context:\n{context}")

            messages = [{
                "role": "system",
                "content": "\n".join(system_parts)
            }]

            # ── History inject karo (last 10 turns) ───────
            if conversation_history:
                for role, text in conversation_history[-10:]:
                    messages.append({
                        "role": role,
                        "content": str(text)
                    })

            # ── Current message ────────────────────────────
            messages.append({
                "role": "user",
                "content": str(message)
            })

            response = requests.post(
                self.url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "http://localhost",
                    "X-Title": "Omnix AI Assistant",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": 800,
                    "temperature": 0.3
                },
                timeout=30
            )

            try:
                data = response.json()
            except ValueError:
                logger.error(
                    f"Invalid AI JSON response ({response.status_code}): "
                    f"{response.text[:300]}"
                )
                return None

            if "error" in data:
                logger.error(f"OpenRouter error: {data['error']}")
                return None

            logger.debug(f"OpenRouter raw response: {data}")

            if "choices" not in data:
                logger.error(f"Invalid AI response: {data}")
                return None

            return data["choices"][0]["message"]["content"]

        except Exception as e:
            logger.error(f"AI request failed: {e}")
            return None

    # ──────────────────────────────────────────────────────────
    # Plan generation
    # ──────────────────────────────────────────────────────────

    def generate_plan(self, command: str, screen_summary: str = None) -> list | None:

        logger.info("AI Brain generating execution plan")

        screen_part = f"\nCurrent screen state:\n{screen_summary}" if screen_summary else ""

        system_prompt = f"""You are the brain of an AI computer assistant called Omnix.

Convert the user request into a step-by-step JSON plan.

Available tools:
- open_app(app)
- close_app(app)
- type_text(text)
- press_key(key)
- click_ui(text)
- click_mouse(x, y)
- double_click(x, y)
- right_click(x, y)
- hotkey(keys)
- scroll_page(direction)
- drag_mouse(x1, y1, x2, y2)
{screen_part}

Return ONLY a valid JSON list. No explanation. No markdown.

Example:
[
  {{"tool":"open_app","app":"chrome"}},
  {{"tool":"type_text","text":"python tutorials"}},
  {{"tool":"press_key","key":"enter"}}
]"""

        response = self.ask(command, context=system_prompt)

        if not response:
            return None

        try:
            import json
            response = response.strip().replace("```json", "").replace("```", "")
            start = response.find("[")
            end = response.rfind("]")
            if start == -1 or end == -1:
                return None
            return json.loads(response[start:end + 1])
        except Exception:
            logger.error("Failed to parse AI plan")
            return None
