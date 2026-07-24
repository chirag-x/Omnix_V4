# Omnix V4 module
# Omnix V4 module
import platform
import psutil


class SystemInfo:

    @staticmethod
    def get_os():

        return platform.system()

    @staticmethod
    def cpu_usage():

        return psutil.cpu_percent(interval=1)

    @staticmethod
    def memory_usage():

        mem = psutil.virtual_memory()

        return mem.percent

    @staticmethod
    def disk_usage():

        disk = psutil.disk_usage('/')

        return disk.percent