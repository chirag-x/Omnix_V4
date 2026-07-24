# Omnix V4 module
import psutil
import subprocess
from loguru import logger


class ProcessController:

    @staticmethod
    def is_running(app_name):

        for proc in psutil.process_iter(["name"]):

            try:

                if app_name.lower() in proc.info["name"].lower():

                    return True

            except Exception:
                pass

        return False

    @staticmethod
    def kill_process(app_name):

        killed = False
        app_name = app_name.lower().strip()

        for proc in psutil.process_iter(["name"]):

            try:

                name = (proc.info.get("name") or "").lower()

                if app_name in name:

                    logger.info(f"Killing process {proc.info['name']}")

                    proc.kill()
                    killed = True

            except Exception:
                pass

        if not killed:
            logger.warning(f"No process found for: {app_name}")

        return killed

    @staticmethod
    def start_process(command):

        logger.info(f"Starting process: {command}")

        subprocess.Popen(command, shell=True)
