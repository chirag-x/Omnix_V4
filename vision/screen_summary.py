from loguru import logger


class ScreenSummaryBuilder:
    """
    Vision data ko ek clean, LLM-readable string mein convert karta hai.
    Yahi string brain ke prompt mein jaati hai.
    """

    def build(self, system_context: dict, vision_data: dict) -> str:

        try:
            lines = []

            # ── Active window ──────────────────────────────
            active_window = system_context.get("active_window") or "Unknown"
            lines.append(f"Active window: {active_window}")

            # ── Running apps (sirf top 10) ─────────────────
            running_apps = system_context.get("running_apps", [])
            if running_apps:
                top_apps = running_apps[:10]
                lines.append(f"Running apps: {', '.join(top_apps)}")

            # ── Screen text (OCR results) ──────────────────
            texts = vision_data.get("texts", [])
            if texts:
                # High confidence text only (>=0.5)
                readable = [
                    t["text"] for t in texts
                    if t.get("confidence", 0) >= 0.5 and t.get("text", "").strip()
                ]
                if readable:
                    # Limit to 30 items taaki prompt bada na ho
                    preview = readable[:30]
                    lines.append(f"Visible text on screen: {' | '.join(preview)}")

            # ── Detected UI elements ───────────────────────
            ui_elements = vision_data.get("ui_elements", [])
            if ui_elements:
                element_descriptions = []
                for el in ui_elements[:15]:
                    el_type = el.get("type", "unknown")
                    el_text = el.get("text", "")
                    x = el.get("x")
                    y = el.get("y")

                    if el_type == "vertical_list":
                        items = el.get("items", [])
                        item_labels = [i.get("text", "") for i in items[:5]]
                        element_descriptions.append(
                            f"vertical_list: [{', '.join(item_labels)}]"
                        )
                    elif el_text:
                        element_descriptions.append(
                            f"{el_type}('{el_text}') at ({int(x or 0)}, {int(y or 0)})"
                        )
                    else:
                        element_descriptions.append(
                            f"{el_type} at ({int(x or 0)}, {int(y or 0)})"
                        )

                lines.append(f"UI elements: {' | '.join(element_descriptions)}")

            # ── Detected objects (YOLO) ────────────────────
            objects = vision_data.get("objects", [])
            if objects:
                obj_names = list({o.get("type", "") for o in objects if o.get("type")})
                lines.append(f"Detected objects: {', '.join(obj_names[:10])}")

            summary = "\n".join(lines)
            logger.debug(f"Screen summary built:\n{summary}")
            return summary

        except Exception as e:
            logger.error(f"ScreenSummaryBuilder error: {e}")
            return "Screen context unavailable."