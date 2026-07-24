# Omnix V4 module
import json
import os
import re
import subprocess
import time
from pathlib import Path

import psutil
import shutil
from loguru import logger


class AppController:

    CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "app_paths.json"

    APP_ALIASES = {
        "brave browser": "brave",
        "calc": "calculator",
        "code": "visual studio code",
        "command prompt": "cmd",
        "explorer": "file explorer",
        "google chrome": "chrome",
        "google": "chrome",
        "microsoft edge": "edge",
        "microsoft excel": "excel",
        "microsoft outlook": "outlook",
        "microsoft powerpoint": "powerpoint",
        "microsoft teams": "teams",
        "microsoft word": "word",
        "task manager": "task manager",
        "vs code": "visual studio code",
        "vscode": "visual studio code",
        "windows settings": "settings",
    }

    DEFAULT_TARGETS = {
        "calculator": ["calculator:", "calc.exe"],
        "camera": ["microsoft.windows.camera:"],
        "brave": ["brave.exe", "brave"],
        "chrome": ["chrome.exe", "chrome"],
        "cmd": ["cmd.exe"],
        "edge": ["msedge.exe", "msedge"],
        "excel": ["excel.exe"],
        "file explorer": ["explorer.exe"],
        "firefox": ["firefox.exe", "firefox"],
        "notepad": ["notepad.exe"],
        "outlook": ["outlook.exe"],
        "paint": ["mspaint.exe"],
        "powerpoint": ["powerpnt.exe"],
        "powershell": ["powershell.exe"],
        "settings": ["ms-settings:"],
        "spotify": [
            "spotify:",
            "%APPDATA%\\Spotify\\Spotify.exe",
            "Spotify.exe",
            "spotify",
        ],
        "steam": ["steam.exe", "steam"],
        "task manager": ["taskmgr.exe"],
        "vlc": ["vlc.exe", "vlc"],
        "visual studio code": ["code", "Code.exe"],
        "word": ["winword.exe"],
    }

    PROCESS_ALIASES = {
        "calculator": ["CalculatorApp.exe", "calc.exe"],
        "camera": ["WindowsCamera.exe"],
        "brave": ["brave.exe"],
        "chrome": ["chrome.exe"],
        "cmd": ["cmd.exe"],
        "discord": ["Discord.exe"],
        "edge": ["msedge.exe"],
        "excel": ["EXCEL.exe"],
        "file explorer": ["explorer.exe"],
        "firefox": ["firefox.exe"],
        "notepad": ["notepad.exe"],
        "outlook": ["OUTLOOK.exe"],
        "paint": ["mspaint.exe"],
        "powerpoint": ["POWERPNT.exe"],
        "powershell": ["powershell.exe", "pwsh.exe"],
        "settings": ["SystemSettings.exe"],
        "slack": ["slack.exe"],
        "spotify": ["Spotify.exe"],
        "steam": ["steam.exe", "steamwebhelper.exe"],
        "task manager": ["Taskmgr.exe"],
        "telegram": ["Telegram.exe"],
        "teams": ["ms-teams.exe", "Teams.exe"],
        "vlc": ["vlc.exe"],
        "visual studio code": ["Code.exe"],
        "whatsapp": ["WhatsApp.exe"],
        "word": ["WINWORD.exe"],
    }

    PROTECTED_PROCESS_NAMES = {
        "csrss.exe",
        "dwm.exe",
        "explorer.exe",
        "fontdrvhost.exe",
        "lsass.exe",
        "services.exe",
        "smss.exe",
        "system",
        "wininit.exe",
        "winlogon.exe",
    }

    @staticmethod
    def open_app(app_name):

        original_name = str(app_name or "").strip()

        if not original_name:
            logger.warning("open_app called without app name")
            return "error"

        app_key = AppController._canonical_name(original_name)

        logger.info(f"Opening app: {original_name} ({app_key})")

        for target in AppController._targets_for(original_name, app_key):

            if AppController._launch_target(target):
                AppController._wait_for_process(app_key, target)
                return "success"

        shortcut = AppController._find_start_menu_shortcut(app_key)

        if shortcut and AppController._launch_target(str(shortcut)):
            AppController._wait_for_process(app_key, shortcut.name)
            return "success"

        start_app_id = AppController._find_start_app_id(app_key)

        if start_app_id and AppController._launch_start_app(start_app_id):
            AppController._wait_for_process(app_key, start_app_id)
            return "success"

        if AppController._launch_with_windows_start(original_name):
            AppController._wait_for_process(app_key, original_name)
            return "success"

        logger.warning(f"App not found: {original_name}")
        return "error"

    @staticmethod
    def _canonical_name(app_name):

        name = re.sub(r"\s+", " ", app_name.lower().strip())
        name = re.sub(r"^(open|start|launch|close|exit|quit)\s+", "", name)
        name = re.sub(r"\s+app$", "", name).strip()

        return AppController.APP_ALIASES.get(name, name)

    @staticmethod
    def _targets_for(original_name, app_key):

        targets = []
        config_targets = AppController._load_config_targets()

        for key in {original_name.lower().strip(), app_key}:
            configured = config_targets.get(key)
            if configured:
                targets.extend(configured)

        targets.extend(AppController.DEFAULT_TARGETS.get(app_key, []))
        targets.extend([original_name, app_key, f"{app_key}.exe"])

        unique_targets = []
        seen = set()

        for target in targets:
            if not target:
                continue

            target = str(target).strip()
            key = target.lower()

            if key not in seen:
                unique_targets.append(target)
                seen.add(key)

        return unique_targets

    @staticmethod
    def _load_config_targets():

        if not AppController.CONFIG_PATH.exists():
            return {}

        raw = AppController.CONFIG_PATH.read_text(encoding="utf-8").strip()

        if not raw:
            return {}

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid app path config: {e}")
            return {}

        if not isinstance(data, dict):
            return {}

        normalized = {}

        for name, value in data.items():
            key = AppController._canonical_name(str(name))

            if isinstance(value, str):
                normalized[key] = [value]
            elif isinstance(value, list):
                normalized[key] = [str(item) for item in value if item]
            elif isinstance(value, dict):
                entries = []
                for field in ("path", "command", "uri"):
                    if value.get(field):
                        entries.append(str(value[field]))
                entries.extend(str(item) for item in value.get("targets", []) if item)
                normalized[key] = entries

        return normalized

    @staticmethod
    def _launch_target(target):

        target = os.path.expanduser(os.path.expandvars(str(target).strip()))

        if not target:
            return False

        try:
            if AppController._is_uri(target):
                os.startfile(target)
                logger.info(f"Launched URI: {target}")
                return True

            path = Path(target)

            if path.exists():
                os.startfile(str(path))
                logger.info(f"Launched path: {path}")
                return True

            resolved = shutil.which(target)

            if resolved:
                subprocess.Popen([resolved], close_fds=True)
                logger.info(f"Launched executable: {resolved}")
                return True

        except Exception as e:
            logger.debug(f"Launch target failed for {target}: {e}")

        return False

    @staticmethod
    def _is_uri(target):

        if re.match(r"^[a-zA-Z]:[\\/]", target):
            return False

        return bool(re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target))

    @staticmethod
    def _find_start_menu_shortcut(app_key):

        roots = []

        for env_name in ("APPDATA", "PROGRAMDATA"):
            value = os.environ.get(env_name)
            if value:
                roots.append(Path(value) / "Microsoft" / "Windows" / "Start Menu" / "Programs")

        tokens = set(AppController._tokenize(app_key))
        matches = []

        for root in roots:

            if not root.exists():
                continue

            try:
                shortcuts = root.rglob("*.lnk")
            except Exception:
                continue

            for shortcut in shortcuts:
                stem = AppController._canonical_name(shortcut.stem)
                stem_tokens = set(AppController._tokenize(stem))

                if not tokens:
                    continue

                if stem == app_key:
                    return shortcut

                if tokens.issubset(stem_tokens) or app_key in stem:
                    matches.append((len(stem_tokens), shortcut))

        if matches:
            matches.sort(key=lambda item: item[0])
            logger.info(f"Resolved start menu shortcut: {matches[0][1]}")
            return matches[0][1]

        return None

    @staticmethod
    def _find_start_app_id(app_key):

        escaped = app_key.replace("'", "''")
        script = (
            f"$name = '{escaped}'; "
            "Get-StartApps | "
            "Where-Object { $_.Name -like \"*$name*\" } | "
            "Select-Object -First 1 -ExpandProperty AppID"
        )

        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", script],
                capture_output=True,
                text=True,
                timeout=5
            )
        except Exception as e:
            logger.debug(f"Get-StartApps lookup failed for {app_key}: {e}")
            return None

        if result.returncode != 0:
            logger.debug(
                f"Get-StartApps lookup failed for {app_key}: {result.stderr}"
            )
            return None

        app_id = result.stdout.strip().splitlines()

        if not app_id:
            return None

        logger.info(f"Resolved StartApps id for {app_key}: {app_id[0]}")
        return app_id[0]

    @staticmethod
    def _launch_start_app(app_id):

        try:
            subprocess.Popen(["explorer.exe", f"shell:AppsFolder\\{app_id}"])
            logger.info(f"Launched StartApps id: {app_id}")
            return True
        except Exception as e:
            logger.debug(f"StartApps launch failed for {app_id}: {e}")
            return False

    @staticmethod
    def _tokenize(value):

        return re.findall(r"[a-z0-9]+", value.lower())

    @staticmethod
    def _launch_with_windows_start(app_name):

        try:
            result = subprocess.run(
                ["cmd", "/c", "start", "", app_name],
                capture_output=True,
                text=True,
                timeout=3
            )

            if result.returncode == 0:
                logger.info(f"Launched with Windows start: {app_name}")
                return True

            logger.debug(
                f"Windows start failed for {app_name}: {result.stderr or result.stdout}"
            )

        except Exception as e:
            logger.debug(f"Windows start failed for {app_name}: {e}")

        return False

    @staticmethod
    def _wait_for_process(app_key, target):

        process_names = list(AppController.PROCESS_ALIASES.get(app_key, []))

        target_name = Path(str(target)).name

        if target_name.lower().endswith(".exe"):
            process_names.append(target_name)

        if not process_names:
            return False

        deadline = time.time() + 3

        while time.time() < deadline:
            running = AppController._is_any_process_running(process_names)

            if running:
                logger.info(f"App process detected: {running}")
                return True

            time.sleep(0.25)

        logger.debug(f"Launch not verified by process list: {app_key}")
        return False

    @staticmethod
    def _is_any_process_running(process_names):

        wanted = {name.lower() for name in process_names if name}

        for proc in psutil.process_iter(["name"]):

            try:
                name = (proc.info.get("name") or "").lower()

                if name in wanted:
                    return proc.info.get("name")

            except Exception:
                pass

        return None

    @staticmethod
    def close_app(app_name):

        original_name = str(app_name or "").strip()

        if not original_name:
            logger.warning("close_app called without app name")
            return "error"

        app_key = AppController._canonical_name(original_name)
        process_names = AppController._process_names_for(original_name, app_key)

        logger.info(
            f"Closing app: {original_name} ({app_key}); "
            f"process candidates: {sorted(process_names)}"
        )

        if app_key == "file explorer":
            return AppController._close_file_explorer_windows()

        matches = AppController._matching_processes(process_names)

        if not matches:
            matches = AppController._matching_window_processes(app_key)

        if not matches:
            logger.warning(f"No running process or window found for: {original_name}")
            return "error"

        terminated = []

        for proc in matches:
            try:
                proc.terminate()
                terminated.append(proc)
                logger.info(f"Terminating process: {proc.name()} ({proc.pid})")
            except (psutil.NoSuchProcess, psutil.ZombieProcess):
                continue
            except psutil.AccessDenied:
                try:
                    proc.kill()
                    terminated.append(proc)
                    logger.info(f"Killing process: {proc.name()} ({proc.pid})")
                except Exception as e:
                    logger.warning(f"Unable to close process {proc.pid}: {e}")

        if not terminated:
            return "error"

        _, alive = psutil.wait_procs(terminated, timeout=3)

        for proc in alive:
            try:
                proc.kill()
                logger.info(f"Force-killed process: {proc.name()} ({proc.pid})")
            except (psutil.NoSuchProcess, psutil.ZombieProcess):
                pass
            except Exception as e:
                logger.warning(f"Unable to force-close process {proc.pid}: {e}")

        still_alive = []

        if alive:
            _, still_alive = psutil.wait_procs(alive, timeout=2)

        if still_alive:
            logger.warning(
                f"Unable to stop processes: {[proc.pid for proc in still_alive]}"
            )
            return "error"

        remaining = AppController._matching_processes(process_names)

        if remaining:
            logger.warning(
                f"App still has running processes: "
                f"{[proc.info.get('name') for proc in remaining]}"
            )
            return "error"

        logger.info(f"Closed app successfully: {original_name}")
        return "success"

    @staticmethod
    def _close_file_explorer_windows():

        script = """
$count = 0
$shell = New-Object -ComObject Shell.Application
foreach ($window in @($shell.Windows())) {
    try {
        $name = [System.IO.Path]::GetFileName($window.FullName)
        if ($name -ieq 'explorer.exe') {
            $window.Quit()
            $count++
        }
    } catch {}
}
Write-Output $count
"""

        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", script],
                capture_output=True,
                text=True,
                timeout=8,
            )
        except Exception as e:
            logger.warning(f"Unable to close File Explorer windows: {e}")
            return "error"

        if result.returncode != 0:
            logger.warning(
                f"Unable to close File Explorer windows: {result.stderr}"
            )
            return "error"

        try:
            closed_count = int(result.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            closed_count = 0

        if closed_count < 1:
            logger.warning("No File Explorer windows found")
            return "error"

        logger.info(f"Closed {closed_count} File Explorer window(s)")
        return "success"

    @staticmethod
    def _process_names_for(original_name, app_key):

        names = set(AppController.PROCESS_ALIASES.get(app_key, []))

        for target in AppController._targets_for(original_name, app_key):
            expanded = os.path.expanduser(os.path.expandvars(str(target)))
            target_name = Path(expanded).name

            if target_name.lower().endswith(".exe"):
                names.add(target_name)

        for value in (original_name, app_key):
            value = str(value).strip()

            if value and " " not in value:
                names.add(value if value.lower().endswith(".exe") else f"{value}.exe")

        return {
            name.lower()
            for name in names
            if name and name.lower() not in AppController.PROTECTED_PROCESS_NAMES
        }

    @staticmethod
    def _matching_processes(process_names):

        wanted = {name.lower() for name in process_names if name}
        matches = []

        if not wanted:
            return matches

        for proc in psutil.process_iter(["name", "exe"]):
            try:
                name = (proc.info.get("name") or "").lower()
                exe_name = Path(proc.info.get("exe") or "").name.lower()

                if name in wanted or exe_name in wanted:
                    matches.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        return matches

    @staticmethod
    def _matching_window_processes(app_key):

        search_name = re.sub(r"[^a-zA-Z0-9 ._-]", "", app_key).strip()

        if len(search_name) < 3:
            return []

        escaped = search_name.replace("'", "''")
        script = (
            f"$name = '{escaped}'; "
            "Get-Process | "
            "Where-Object { $_.MainWindowTitle -and "
            "$_.MainWindowTitle -like \"*$name*\" } | "
            "Select-Object -ExpandProperty Id"
        )

        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", script],
                capture_output=True,
                text=True,
                timeout=5,
            )
        except Exception as e:
            logger.debug(f"Window process lookup failed for {app_key}: {e}")
            return []

        if result.returncode != 0:
            return []

        matches = []

        for value in result.stdout.splitlines():
            try:
                proc = psutil.Process(int(value.strip()))

                if proc.pid == os.getpid():
                    continue

                if proc.name().lower() in AppController.PROTECTED_PROCESS_NAMES:
                    continue

                matches.append(proc)
            except (ValueError, psutil.Error):
                continue

        return matches
