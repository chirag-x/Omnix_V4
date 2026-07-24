import re
import time
from difflib import SequenceMatcher

from loguru import logger

from system.keyboard_mouse_controller import KeyboardMouseController
from vision.element_locator import ElementLocator


class UIController:

    CLICKABLE_TYPES = {
        "Button",
        "CheckBox",
        "Hyperlink",
        "ListItem",
        "MenuItem",
        "RadioButton",
        "TabItem",
        "TreeItem",
    }

    def __init__(self, vision_manager=None):

        self.vision_manager = vision_manager
        self.locator = (
            ElementLocator(vision_manager)
            if vision_manager is not None
            else None
        )
        self._desktop = None
        self._uia_error_logged = False

    def click(
        self,
        target,
        control_type=None,
        index=0,
        window_title=None,
        button="left",
        double=False,
    ):

        control = self.find_control(
            target=target,
            control_type=control_type,
            index=index,
            window_title=window_title,
        )

        if control is not None:
            try:
                if double:
                    control.double_click_input(button=button)
                elif button == "right":
                    control.right_click_input()
                else:
                    control.click_input(button=button)

                logger.info(
                    f"Clicked native UI control: {self._control_name(control)}"
                )
                return "success"
            except Exception as e:
                logger.debug(f"Native UI click failed: {e}")

        return self._click_vision_target(
            target=target,
            index=index,
            button=button,
            double=double,
        )

    def invoke(self, target, control_type=None, index=0, window_title=None):

        control = self.find_control(
            target=target,
            control_type=control_type,
            index=index,
            window_title=window_title,
        )

        if control is None:
            return self.click(
                target,
                control_type=control_type,
                index=index,
                window_title=window_title,
            )

        try:
            control.invoke()
            logger.info(f"Invoked UI control: {self._control_name(control)}")
            return "success"
        except Exception as e:
            logger.debug(f"Native invoke failed: {e}")
            return self.click(
                target,
                control_type=control_type,
                index=index,
                window_title=window_title,
            )

    def set_text(
        self,
        value,
        target=None,
        control_type="Edit",
        index=0,
        window_title=None,
        clear=True,
    ):

        control = self.find_control(
            target=target,
            control_type=control_type,
            index=index,
            window_title=window_title,
        )

        if control is not None:
            try:
                if hasattr(control, "set_edit_text"):
                    control.set_edit_text(str(value))
                else:
                    control.set_focus()
                    if clear:
                        KeyboardMouseController.hotkey("ctrl", "a")
                    KeyboardMouseController.type_text(str(value))

                logger.info(
                    f"Set text in native UI control: {self._control_name(control)}"
                )
                return "success"
            except Exception as e:
                logger.debug(f"Native set_text failed: {e}")

        if target:
            clicked = self._click_vision_target(target, index=index)

            if clicked == "error":
                return "error"

        if clear:
            KeyboardMouseController.hotkey("ctrl", "a")

        KeyboardMouseController.type_text(str(value))
        return "success"

    def perform(
        self,
        action,
        target=None,
        value=None,
        control_type=None,
        index=0,
        window_title=None,
    ):

        action = str(action or "click").lower().strip()

        if action == "click":
            return self.click(
                target,
                control_type=control_type,
                index=index,
                window_title=window_title,
            )

        if action == "double_click":
            return self.click(
                target,
                control_type=control_type,
                index=index,
                window_title=window_title,
                double=True,
            )

        if action == "right_click":
            return self.click(
                target,
                control_type=control_type,
                index=index,
                window_title=window_title,
                button="right",
            )

        if action == "invoke":
            return self.invoke(
                target,
                control_type=control_type,
                index=index,
                window_title=window_title,
            )

        if action in {"set_text", "type"}:
            if value is None:
                return "error"

            return self.set_text(
                value=value,
                target=target,
                control_type=control_type or "Edit",
                index=index,
                window_title=window_title,
            )

        control = self.find_control(
            target=target,
            control_type=control_type,
            index=index,
            window_title=window_title,
        )

        if control is None:
            return "error"

        method_names = {
            "focus": ("set_focus",),
            "select": ("select",),
            "expand": ("expand",),
            "collapse": ("collapse",),
            "check": ("check", "toggle"),
            "uncheck": ("uncheck", "toggle"),
        }

        for method_name in method_names.get(action, ()):
            method = getattr(control, method_name, None)

            if method is None:
                continue

            try:
                method()
                logger.info(
                    f"Performed {action} on UI control: "
                    f"{self._control_name(control)}"
                )
                return "success"
            except Exception as e:
                logger.debug(
                    f"UI action {action} via {method_name} failed: {e}"
                )

        return "error"

    def wait_for(
        self,
        target,
        state="visible",
        control_type=None,
        window_title=None,
        timeout=10,
    ):

        deadline = time.time() + max(float(timeout), 0)
        state = str(state or "visible").lower()

        while time.time() <= deadline:
            control = self.find_control(
                target=target,
                control_type=control_type,
                window_title=window_title,
            )
            vision_element = None

            if control is None and self.locator is not None and target:
                vision_element = self.locator.find_text(target)

            exists = control is not None or vision_element is not None

            if state in {"visible", "exists", "present"} and exists:
                return "success"

            if state in {"gone", "hidden", "absent"} and not exists:
                return "success"

            if state == "enabled" and control is not None:
                try:
                    if control.is_enabled():
                        return "success"
                except Exception:
                    pass

            time.sleep(0.25)

        logger.warning(f"Timed out waiting for UI target '{target}' ({state})")
        return "error"

    def find_control(
        self,
        target=None,
        control_type=None,
        index=0,
        window_title=None,
    ):

        root = self._get_window(window_title)

        if root is None:
            return None

        try:
            controls = root.descendants(
                control_type=control_type
            ) if control_type else root.descendants()
        except Exception as e:
            logger.debug(f"Unable to enumerate UI controls: {e}")
            return None

        ranked = []

        for order, control in enumerate(controls):
            try:
                if not control.is_visible():
                    continue
            except Exception:
                pass

            if control_type:
                actual_type = getattr(
                    getattr(control, "element_info", None),
                    "control_type",
                    None,
                )

                if actual_type and actual_type.lower() != control_type.lower():
                    continue

            score = self._match_score(target, self._control_labels(control))

            if target and score <= 0:
                continue

            ranked.append((score, -order, control))

        ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)

        if index < 0 or index >= len(ranked):
            return None

        return ranked[index][2]

    def list_controls(self, window_title=None, limit=100):

        root = self._get_window(window_title)

        if root is None:
            return []

        controls = []

        try:
            descendants = root.descendants()
        except Exception:
            return controls

        for control in descendants:
            name = self._control_name(control)

            if not name:
                continue

            info = getattr(control, "element_info", None)
            rectangle = None

            try:
                rect = control.rectangle()
                rectangle = {
                    "left": rect.left,
                    "top": rect.top,
                    "right": rect.right,
                    "bottom": rect.bottom,
                }
            except Exception:
                pass

            controls.append({
                "text": name,
                "type": getattr(info, "control_type", None),
                "automation_id": getattr(info, "automation_id", None),
                "rectangle": rectangle,
            })

            if len(controls) >= limit:
                break

        return controls

    def _get_desktop(self):

        if self._desktop is not None:
            return self._desktop

        try:
            from pywinauto import Desktop

            self._desktop = Desktop(backend="uia")
            return self._desktop
        except Exception as e:
            if not self._uia_error_logged:
                logger.warning(f"Windows UI Automation unavailable: {e}")
                self._uia_error_logged = True
            return None

    def _get_window(self, window_title=None):

        desktop = self._get_desktop()

        if desktop is None:
            return None

        if window_title:
            candidates = []

            try:
                windows = desktop.windows(visible_only=True)
            except Exception:
                windows = []

            for window in windows:
                score = self._match_score(
                    window_title,
                    self._control_labels(window),
                )

                if score > 0:
                    candidates.append((score, window))

            if candidates:
                candidates.sort(key=lambda item: item[0], reverse=True)
                return candidates[0][1]

            return None

        try:
            import pygetwindow as gw

            active = gw.getActiveWindow()

            if active and getattr(active, "_hWnd", None):
                return desktop.window(handle=active._hWnd).wrapper_object()
        except Exception as e:
            logger.debug(f"Unable to resolve active UI window: {e}")

        return None

    def _click_vision_target(
        self,
        target,
        index=0,
        button="left",
        double=False,
    ):

        if self.locator is None or not target:
            return "error"

        elements = self.locator.find_all(target)

        if not elements or index < 0 or index >= len(elements):
            logger.warning(f"OCR UI target not found: {target}")
            return "error"

        element = self.locator.sort_by_position(elements)[index]
        coordinates = self.locator.get_coordinates(element)

        if not coordinates or None in coordinates:
            return "error"

        x, y = self._desktop_coordinates(*coordinates)

        if double:
            KeyboardMouseController.double_click(x, y)
        elif button == "right":
            KeyboardMouseController.right_click(x, y)
        else:
            KeyboardMouseController.click(x, y)

        logger.info(f"Clicked OCR UI target '{target}' at ({x}, {y})")
        return "success"

    def _desktop_coordinates(self, x, y):

        observer = getattr(self.vision_manager, "observer", None)
        bounds = getattr(observer, "screen_bounds", None)

        if not bounds:
            return x, y

        return (
            int(bounds.get("left", 0) + x),
            int(bounds.get("top", 0) + y),
        )

    def _control_labels(self, control):

        labels = []

        try:
            labels.append(control.window_text())
        except Exception:
            pass

        info = getattr(control, "element_info", None)

        for value in (
            getattr(info, "name", None),
            getattr(info, "automation_id", None),
            getattr(info, "class_name", None),
        ):
            if value:
                labels.append(str(value))

        return labels

    def _control_name(self, control):

        for label in self._control_labels(control):
            if label and str(label).strip():
                return str(label).strip()

        return ""

    def _match_score(self, target, labels):

        if not target:
            return 1

        target = self._normalize(target)

        if not target:
            return 0

        best = 0

        for label in labels:
            label = self._normalize(label)

            if not label:
                continue

            if label == target:
                score = 100
            elif label.startswith(target) or target.startswith(label):
                score = 90
            elif target in label or label in target:
                score = 80
            else:
                target_tokens = set(target.split())
                label_tokens = set(label.split())
                overlap = len(target_tokens & label_tokens)
                token_score = (
                    60 * overlap / max(len(target_tokens), 1)
                    if overlap
                    else 0
                )
                similarity = 50 * SequenceMatcher(
                    None,
                    target,
                    label,
                ).ratio()
                score = max(token_score, similarity)

            best = max(best, score)

        return best if best >= 30 else 0

    def _normalize(self, value):

        value = str(value or "").lower()
        value = re.sub(r"[^a-z0-9]+", " ", value)
        return re.sub(r"\s+", " ", value).strip()
